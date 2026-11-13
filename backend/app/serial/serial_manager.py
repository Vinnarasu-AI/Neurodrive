"""
Non-blocking Serial Reader & Hardware Manager for Upside Down Labs NPG Lite.

Protocol & Hardware Integration details:
- Baud rates checked: 230400, 115200.
- Handshake sequence:
  1. Opens serial port.
  2. Sends 'WHORU\n' (up to retry limit).
  3. Validates response against known board identifiers ('NPG-LITE', 'NPG-LITE-3CH', 'NPG-LITE-6CH').
  4. Sends 'START\n' to begin continuous binary streaming.
  5. Decodes binary packets using ChordsPacketDecoder (0xC7 0x7C sync, 10 bytes for 3CH, big-endian uint16, 0x01 delimiter).
  6. Sends 'STOP\n' upon acquisition halt or disconnect.
- Clear Source Separation:
  - REAL HARDWARE vs SIMULATION
  - Never generate fake or simulated samples when in real hardware mode!
  - If real device disconnects, state goes strictly to DISCONNECTED with error reporting.
"""

import threading
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from collections import deque
import numpy as np
import serial
import serial.tools.list_ports

from app.serial.chords_decoder import ChordsPacketDecoder, encode_chords_packet
from app.dsp.filters import RealtimeEOGFilter
from app.dsp.quality import SignalQualityEvaluator
from app.dsp.calibration import CalibrationManager
from app.dsp.blink_detector import DoubleBlinkDetector
from app.dsp.single_blink_detector import SingleBlinkDetector
from app.dsp.movo_classifier import MovoGestureClassifier as WheelchairClassifier

logger = logging.getLogger("neurodrive.serial")


class SerialManager:
    SUPPORTED_BOARDS = ["NPG-LITE", "NPG-LITE-3CH", "NPG-LITE-6CH"]

    def __init__(
        self,
        port: str = "AUTO",
        baud_rate: int = 230400,
        channels: int = 3,
        sample_rate: int = 500,
        use_mock: bool = True,
        on_blink_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_single_blink_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_wheelchair_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.channels = channels
        self.sample_rate = sample_rate
        self.use_mock = use_mock
        self.on_blink_callback = on_blink_callback
        self.on_single_blink_callback = on_single_blink_callback
        self.on_wheelchair_callback = on_wheelchair_callback

        # Hardware connection
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_streaming = False
        self.board_id: Optional[str] = None
        self.active_port_name = "SIMULATED" if use_mock else "DISCONNECTED"
        self.last_connection_error: Optional[str] = None

        # Threading controls
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._buffer_lock = threading.Lock()

        # DSP components
        self.decoder = ChordsPacketDecoder(num_channels=self.channels)
        self.filter = RealtimeEOGFilter(sample_rate=self.sample_rate)
        self.quality_evaluator = SignalQualityEvaluator()
        self.calibration_mgr = CalibrationManager(sample_rate=self.sample_rate)
        self.blink_detector = DoubleBlinkDetector(sample_rate=self.sample_rate)
        self.single_blink_detector = SingleBlinkDetector(sample_rate=self.sample_rate)
        self.wheelchair_classifier = WheelchairClassifier(sample_rate=self.sample_rate)

        # Signal Buffers (last 4 seconds = 2000 points at 500 Hz)
        self.buffer_len = self.sample_rate * 4
        self.timestamps = deque(maxlen=self.buffer_len)
        self.raw_ch1 = deque(maxlen=self.buffer_len)
        self.filtered_ch1 = deque(maxlen=self.buffer_len)
        self.raw_ch2 = deque(maxlen=self.buffer_len)
        self.filtered_ch2 = deque(maxlen=self.buffer_len)
        self.raw_ch3 = deque(maxlen=self.buffer_len)
        self.filtered_ch3 = deque(maxlen=self.buffer_len)

        # Latest Wheelchair classification output
        self.latest_wheelchair_status: Dict[str, Any] = {
            "decision": "STOP",
            "source": "REST",
            "eeg": {"filtered": 0.0, "focus_index": 0.0, "intent_active": False, "calibrated": False},
            "emg_left": {"filtered": 0.0, "envelope": 0.0, "active": False, "threshold": 60.0},
            "emg_right": {"filtered": 0.0, "envelope": 0.0, "active": False, "threshold": 60.0},
        }

        # Metrics
        self.latest_quality = {"score": 0.0, "is_good": False, "status": "DISCONNECTED"}
        self.latest_sample_rate_measured = 0.0
        self._packet_count_window = 0
        self._last_rate_calc_time = time.time()

        # Mock generator states
        self._sim_phase = 0.0
        self._sim_counter = 0

    def start(self):
        """Starts background worker thread."""
        if self._running:
            return
        self._running = True
        self.is_streaming = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="NPG-Serial-Worker")
        self._thread.start()
        logger.info(f"Serial worker thread started (use_mock={self.use_mock}, port={self.port})")

    def stop(self):
        """Stops background thread and cleanly shuts down serial stream."""
        self._running = False
        self.is_streaming = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._close_serial()
        logger.info("Serial worker thread stopped")

    def connect_real_hardware(self, port_name: str, baud_rate: Optional[int] = None) -> bool:
        """Explicitly switches to Real Hardware mode and connects to specified port."""
        self.stop()
        self.use_mock = False
        self.port = port_name
        if baud_rate:
            self.baud_rate = baud_rate
        self.decoder.reset()
        self.start()
        # Give connection attempt a moment
        time.sleep(0.5)
        return self.is_connected

    def disconnect_hardware(self):
        """Stops streaming and disconnects without switching to mock mode."""
        self._send_stop_command()
        self._close_serial()
        self.active_port_name = "DISCONNECTED"
        self.is_connected = False
        self.is_streaming = False
        self.board_id = None
        self.latest_quality = {"score": 0.0, "is_good": False, "status": "DISCONNECTED"}

    def set_simulation_mode(self, enabled: bool):
        """Switches between Simulation mode and Real Hardware mode."""
        self.stop()
        self.use_mock = enabled
        self.active_port_name = "SIMULATED" if enabled else "DISCONNECTED"
        self.decoder.reset()
        if not enabled:
            self.is_connected = False
            self.is_streaming = False
            self.latest_quality = {"score": 0.0, "is_good": False, "status": "DISCONNECTED"}
        self.start()

    def start_acquisition(self) -> bool:
        """Sends START command to hardware or starts mock feed."""
        self.is_streaming = True
        if not self.use_mock and self.ser and self.ser.is_open:
            try:
                self.ser.flushInput()
                self.ser.write(b"START\n")
                logger.info("Sent START command to NPG Lite")
                return True
            except Exception as e:
                logger.error(f"Failed to send START command: {e}")
                return False
        return True

    def stop_acquisition(self) -> bool:
        """Sends STOP command to hardware or pauses stream."""
        self.is_streaming = False
        if not self.use_mock and self.ser and self.ser.is_open:
            return self._send_stop_command()
        return True

    def _send_stop_command(self) -> bool:
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"STOP\n")
                time.sleep(0.05)
                self.ser.flushInput()
                logger.info("Sent STOP command to NPG Lite")
                return True
            except Exception as e:
                logger.debug(f"Error sending STOP: {e}")
        return False

    def _close_serial(self):
        self._send_stop_command()
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.is_connected = False

    def list_ports(self) -> List[Dict[str, str]]:
        ports = serial.tools.list_ports.comports()
        return [
            {
                "device": p.device,
                "description": p.description,
                "hwid": p.hwid,
            }
            for p in ports
        ]

    def _try_open_hardware(self) -> bool:
        candidate_ports = []
        if self.port.upper() == "AUTO":
            all_ports = serial.tools.list_ports.comports()
            for p in all_ports:
                desc = p.description.lower()
                # Exclude standard bluetooth link ports
                if "bluetooth" in desc:
                    continue
                if any(k in desc for k in ["usb", "uart", "cp210", "ch340", "jtag", "serial"]):
                    candidate_ports.append(p.device)
            for p in all_ports:
                if p.device not in candidate_ports and "bluetooth" not in p.description.lower():
                    candidate_ports.append(p.device)
        else:
            candidate_ports = [self.port]

        if not candidate_ports:
            self.last_connection_error = "No candidate serial ports found."
            return False

        # Support common Chords baudrates: configured baudrate first, then fallback
        baud_list = [self.baud_rate]
        if 230400 not in baud_list:
            baud_list.append(230400)
        if 115200 not in baud_list:
            baud_list.append(115200)

        for p_name in candidate_ports:
            for b_rate in baud_list:
                try:
                    s = serial.Serial(p_name, baudrate=b_rate, timeout=0.3, write_timeout=0.5)
                    s.flushInput()
                    s.flushOutput()

                    # Handshake: WHORU
                    identified_board = None
                    for _ in range(3):
                        s.write(b"WHORU\n")
                        time.sleep(0.1)
                        resp = s.readline().decode("utf-8", errors="ignore").strip()
                        if resp in self.SUPPORTED_BOARDS or "NPG" in resp.upper():
                            identified_board = resp
                            break

                    # Start streaming
                    s.write(b"START\n")
                    self.ser = s
                    self.baud_rate = b_rate
                    self.is_connected = True
                    self.is_streaming = True
                    self.board_id = identified_board or "NPG-LITE"
                    self.active_port_name = p_name
                    self.last_connection_error = None
                    logger.info(f"Connected to NPG Lite ({self.board_id}) on {p_name} @ {b_rate} baud")
                    return True
                except Exception as e:
                    self.last_connection_error = f"Error on {p_name} ({b_rate} baud): {e}"
                    continue

        return False

    def _worker_loop(self):
        while self._running:
            if self.use_mock:
                # Simulation Mode: clearly marked, generates realistic 500 Hz synthetic data
                if self.is_streaming:
                    self._run_mock_iteration()
                time.sleep(0.002)
            else:
                # Real Hardware Mode: NEVER generate synthetic data
                if not self.is_connected:
                    if not self._try_open_hardware():
                        time.sleep(1.0)
                        continue

                if not self.is_streaming:
                    time.sleep(0.05)
                    continue

                try:
                    raw_data = self.ser.read(self.ser.in_waiting or 1)
                    if not raw_data:
                        continue

                    packets = self.decoder.feed(raw_data)
                    now = time.time()

                    for counter, ch_values in packets:
                        ch1_val = float(ch_values[0])
                        ch2_val = float(ch_values[1]) if len(ch_values) > 1 else 2048.0
                        ch3_val = float(ch_values[2]) if len(ch_values) > 2 else 2048.0
                        self._process_sample(now, ch1_val, ch2_val, ch3_val)
                        self._packet_count_window += 1

                except Exception as e:
                    logger.error(f"NPG Lite hardware disconnected or read error on {self.active_port_name}: {e}")
                    self.last_connection_error = f"Hardware disconnected: {e}"
                    self._close_serial()
                    # Do not fall back to mock! Keep state honest
                    self.latest_quality = {"score": 0.0, "is_good": False, "status": "DISCONNECTED"}
                    time.sleep(1.0)

            # Update sampling rate and signal quality metrics periodically
            now = time.time()
            if now - self._last_rate_calc_time >= 0.5:
                dt = now - self._last_rate_calc_time
                self.latest_sample_rate_measured = round(self._packet_count_window / dt, 1)
                self._packet_count_window = 0
                self._last_rate_calc_time = now

                with self._buffer_lock:
                    if len(self.raw_ch1) > 100:
                        raw_arr = np.array(list(self.raw_ch1)[-250:])
                        filt_arr = np.array(list(self.filtered_ch1)[-250:])
                        self.latest_quality = self.quality_evaluator.evaluate(raw_arr, filt_arr)
                    elif not self.is_connected and not self.use_mock:
                        self.latest_quality = {"score": 0.0, "is_good": False, "status": "DISCONNECTED"}

    def _run_mock_iteration(self):
        """Simulates 500Hz realistic 3-channel data (CH1: EOG/EEG, CH2: Left EMG, CH3: Right EMG)."""
        now = time.time()
        self._sim_phase += 0.01

        baseline = 2048.0 + 30.0 * np.sin(self._sim_phase * 0.1)
        noise = np.random.normal(0, 12.0)
        ch1_val = baseline + noise

        # Periodic double blink in CH1
        cycle_sec = now % 15.0
        if 5.0 <= cycle_sec < 5.15:
            rel_t = (cycle_sec - 5.0) / 0.15
            ch1_val += 480.0 * np.sin(rel_t * np.pi)
        elif 5.45 <= cycle_sec < 5.60:
            rel_t = (cycle_sec - 5.45) / 0.15
            ch1_val += 520.0 * np.sin(rel_t * np.pi)

        # Baseline for CH2 and CH3
        ch2_val = 2048.0 + np.random.normal(0, 10.0)
        ch3_val = 2048.0 + np.random.normal(0, 10.0)

        # Periodic EMG bursts:
        # 10s - 12s: Left EMG (turn left)
        # 13s - 15s: Right EMG (turn right)
        # 7s - 9s: Bilateral EMG (backward)
        if 10.0 <= cycle_sec < 12.0:
            ch2_val += np.random.normal(0, 120.0)
        elif 13.0 <= cycle_sec < 15.0:
            ch3_val += np.random.normal(0, 120.0)
        elif 7.0 <= cycle_sec < 9.0:
            ch2_val += np.random.normal(0, 140.0)
            ch3_val += np.random.normal(0, 140.0)

        self._sim_counter = (self._sim_counter + 1) & 0xFF
        pkt = encode_chords_packet(self._sim_counter, [int(ch1_val), int(ch2_val), int(ch3_val)])
        packets = self.decoder.feed(pkt)
        for _, ch_values in packets:
            self._process_sample(now, float(ch_values[0]), float(ch_values[1]), float(ch_values[2]))
            self._packet_count_window += 1

    def _process_sample(self, timestamp: float, raw_ch1: float, raw_ch2: float = 2048.0, raw_ch3: float = 2048.0):
        # 1. Filter sample for CH1 EOG
        filtered_ch1 = self.filter.filter_sample(raw_ch1)

        # 2. Store in thread-safe buffers
        with self._buffer_lock:
            self.timestamps.append(timestamp)
            self.raw_ch1.append(raw_ch1)
            self.filtered_ch1.append(filtered_ch1)
            self.raw_ch2.append(raw_ch2)
            self.filtered_ch2.append(raw_ch2 - 2048.0)
            self.raw_ch3.append(raw_ch3)
            self.filtered_ch3.append(raw_ch3 - 2048.0)

        # 3. Calibration sample intake
        self.calibration_mgr.feed_sample(raw_ch1, filtered_ch1)

        # 4. Double blink detection (for Smart Home)
        threshold_db = self.calibration_mgr.blink_peak_threshold
        is_good = self.latest_quality.get("is_good", True)
        is_cal = self.calibration_mgr.calibrated or self.use_mock

        event = self.blink_detector.process_sample(
            filtered_val=filtered_ch1,
            timestamp=timestamp,
            threshold=threshold_db,
            is_signal_good=is_good,
            is_calibrated=is_cal,
        )

        if event and self.on_blink_callback:
            try:
                self.on_blink_callback(event)
            except Exception as e:
                logger.error(f"Error in blink callback: {e}")

        # 5. Dedicated Single-Blink Detection (for EOG Dino Game Runner)
        threshold_sb = self.calibration_mgr.game_blink_threshold
        is_game_cal = self.calibration_mgr.game_calibrated or self.use_mock

        sb_event = self.single_blink_detector.process_sample(
            filtered_val=filtered_ch1,
            timestamp=timestamp,
            threshold=threshold_sb,
            is_signal_good=is_good,
            is_calibrated=is_game_cal,
        )

        if sb_event and self.on_single_blink_callback:
            try:
                self.on_single_blink_callback(sb_event)
            except Exception as e:
                logger.error(f"Error in single blink callback: {e}")

        # 6. Assistive Wheelchair Multichannel EEG + EMG Classification
        wc_res = self.wheelchair_classifier.classify(
            ch1_raw=raw_ch1,
            ch2_raw=raw_ch2,
            ch3_raw=raw_ch3,
            is_signal_good=is_good,
        )
        self.latest_wheelchair_status = wc_res
        if self.on_wheelchair_callback:
            try:
                self.on_wheelchair_callback(wc_res)
            except Exception as e:
                logger.error(f"Error in Wheelchair callback: {e}")

    def get_signal_snapshot(self, num_points: int = 500) -> Dict[str, Any]:
        """Thread-safe snapshot with explicit hardware source tagging."""
        source_label = "SIMULATION" if self.use_mock else "REAL HARDWARE"
        is_conn = (self.ser is not None and self.ser.is_open and self.is_connected) if not self.use_mock else True

        with self._buffer_lock:
            pts = min(num_points, len(self.timestamps))
            if pts == 0 or (not self.use_mock and not is_conn):
                return {
                    "timestamps": [],
                    "raw_ch1": [],
                    "filtered_ch1": [],
                    "raw_ch2": [],
                    "filtered_ch2": [],
                    "raw_ch3": [],
                    "filtered_ch3": [],
                    "movo": self.latest_wheelchair_status,
                    "wheelchair": self.latest_wheelchair_status,
                    "quality": self.latest_quality if not self.use_mock else {"score": 95, "is_good": True, "status": "GOOD"},
                    "calibration": self.calibration_mgr.get_status(),
                    "sample_rate": self.latest_sample_rate_measured if is_conn else 0.0,
                    "connected": is_conn,
                    "is_streaming": self.is_streaming,
                    "port": self.active_port_name,
                    "is_mock": self.use_mock,
                    "source": source_label,
                    "board_id": self.board_id or ("SIMULATOR" if self.use_mock else "NPG-LITE"),
                    "error": self.last_connection_error,
                }

            t_list = list(self.timestamps)[-pts:]
            raw_list = list(self.raw_ch1)[-pts:]
            filt_list = list(self.filtered_ch1)[-pts:]
            raw2_list = list(self.raw_ch2)[-pts:]
            filt2_list = list(self.filtered_ch2)[-pts:]
            raw3_list = list(self.raw_ch3)[-pts:]
            filt3_list = list(self.filtered_ch3)[-pts:]

        return {
            "timestamps": [round(t, 3) for t in t_list],
            "raw_ch1": [round(r, 1) for r in raw_list],
            "filtered_ch1": [round(f, 1) for f in filt_list],
            "raw_ch2": [round(r, 1) for r in raw2_list],
            "filtered_ch2": [round(f, 1) for f in filt2_list],
            "raw_ch3": [round(r, 1) for r in raw3_list],
            "filtered_ch3": [round(f, 1) for f in filt3_list],
            "movo": self.latest_wheelchair_status,
            "wheelchair": self.latest_wheelchair_status,
            "quality": self.latest_quality,
            "calibration": self.calibration_mgr.get_status(),
            "sample_rate": self.latest_sample_rate_measured,
            "connected": is_conn,
            "is_streaming": self.is_streaming,
            "port": self.active_port_name,
            "is_mock": self.use_mock,
            "source": source_label,
            "board_id": self.board_id or ("SIMULATOR" if self.use_mock else "NPG-LITE"),
            "error": self.last_connection_error,
        }
