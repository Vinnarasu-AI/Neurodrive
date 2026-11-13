import pytest
from app.serial.serial_manager import SerialManager
from app.core.state import ApplicationStateManager, AppMode
from app.dsp.blink_detector import DoubleBlinkDetector
from app.serial.chords_decoder import ChordsPacketDecoder, encode_chords_packet


def test_serial_manager_source_labelling_real_vs_mock():
    # 1. Mock mode
    sm = SerialManager(use_mock=True)
    snap_mock = sm.get_signal_snapshot(num_points=10)
    assert snap_mock["is_mock"] is True
    assert snap_mock["source"] == "SIMULATION"

    # 2. Real Hardware mode (when disconnected, never output fake samples)
    sm.set_simulation_mode(False)
    snap_real = sm.get_signal_snapshot(num_points=10)
    assert snap_real["is_mock"] is False
    assert snap_real["source"] == "REAL HARDWARE"
    assert snap_real["connected"] is False
    assert snap_real["quality"]["status"] == "DISCONNECTED"
    # When disconnected, no fake samples are emitted
    assert len(snap_real["filtered_ch1"]) == 0
    sm.stop()


def test_serial_manager_disconnect_hardware():
    sm = SerialManager(use_mock=False)
    sm.disconnect_hardware()
    assert sm.is_connected is False
    assert sm.is_streaming is False
    assert sm.active_port_name == "DISCONNECTED"
    assert sm.board_id is None
    snap = sm.get_signal_snapshot(num_points=10)
    assert snap["source"] == "REAL HARDWARE"
    assert snap["connected"] is False


def test_chords_decoder_malformed_packets():
    decoder = ChordsPacketDecoder(num_channels=3)
    # Corrupt packet: wrong end byte (0xFF instead of 0x01)
    corrupt_packet = bytearray([0xC7, 0x7C, 0x01, 0x08, 0x00, 0x08, 0x00, 0x08, 0x00, 0xFF])
    res = decoder.feed(bytes(corrupt_packet))
    assert len(res) == 0
    assert decoder.corrupt_bytes_skipped > 0

    # Follow with valid packet
    valid_packet = encode_chords_packet(2, [2048, 2048, 2048])
    res_valid = decoder.feed(valid_packet)
    assert len(res_valid) == 1
    assert res_valid[0][0] == 2
    assert res_valid[0][1] == [2048, 2048, 2048]


def test_double_blink_acceptance_and_single_blink_rejection():
    detector = DoubleBlinkDetector(sample_rate=500, min_gap_ms=150, max_gap_ms=850, refractory_ms=600)
    dt = 1.0 / 500.0
    thresh = 250.0

    # Single blink test
    t = 0.0
    blink_single = 400.0 * (1.0 - ((t - 0.075) / 0.075) ** 2)
    ev_single = None
    for i in range(75):  # 150ms
        t += dt
        val = max(0.0, 400.0 * (1.0 - ((i*dt - 0.075) / 0.075) ** 2))
        ev = detector.process_sample(val, t, thresh)
        if ev:
            ev_single = ev

    # Single blink must NOT trigger double blink
    assert ev_single is None

    # Wait out gap (300ms)
    for _ in range(150):
        t += dt
        detector.process_sample(0.0, t, thresh)

    # Second deliberate blink
    ev_double = None
    for i in range(75):  # 150ms
        t += dt
        val = max(0.0, 420.0 * (1.0 - ((i*dt - 0.075) / 0.075) ** 2))
        ev = detector.process_sample(val, t, thresh)
        if ev:
            ev_double = ev

    # Exactly one double-blink event registered
    assert ev_double is not None
    assert ev_double["type"] == "DOUBLE_BLINK"


def test_inactive_app_suppression():
    state_mgr = ApplicationStateManager()
    assert state_mgr.current_mode == AppMode.IDLE
    assert not state_mgr.is_smart_home_active()

    # Callback action simulator
    action_fired = []

    def mock_callback(event):
        if state_mgr.is_smart_home_active():
            action_fired.append(event)

    # In IDLE, event is suppressed
    mock_callback({"type": "DOUBLE_BLINK", "gap_ms": 300})
    assert len(action_fired) == 0

    # Activate Smart Home
    state_mgr.activate_smart_home()
    assert state_mgr.is_smart_home_active()
    mock_callback({"type": "DOUBLE_BLINK", "gap_ms": 300})
    assert len(action_fired) == 1

