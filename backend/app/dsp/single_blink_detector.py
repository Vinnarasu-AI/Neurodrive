"""
Dedicated Single-Blink Detector for Vertical EOG (Endless Runner / Dino Game).

Key Differences & Requirements:
- Detects exactly one deliberate blink event.
- Evaluates morphology: amplitude exceeding dynamic threshold + strict duration window (60 ms to 350 ms).
- Rejects slow eye movements (vertical saccades, looking up/down sustained > 400 ms).
- Rejects high-frequency muscle noise or spikes (< 50 ms).
- Strict refractory / debounce protection (default 350-400 ms) to prevent multiple triggers from one single blink waveform.
- Fully isolated from the double-blink detector.
- Uses independent calibration parameters so game calibration does NOT overwrite Smart Home calibration.
"""

from typing import Optional, Dict, Any
from collections import deque
import logging

logger = logging.getLogger("neurodrive.single_blink")


class SingleBlinkDetector:
    def __init__(
        self,
        sample_rate: int = 500,
        refractory_ms: int = 350,
        min_blink_duration_ms: float = 60.0,
        max_blink_duration_ms: float = 350.0,
        hysteresis_ratio: float = 0.35,
    ):
        self.sample_rate = sample_rate
        self.refractory_sec = refractory_ms / 1000.0
        self.min_blink_duration_ms = min_blink_duration_ms
        self.max_blink_duration_ms = max_blink_duration_ms
        self.hysteresis_ratio = hysteresis_ratio

        # State machine: "IDLE", "IN_BLINK", "REFRACTORY"
        self.state = "IDLE"
        self.current_blink_start: Optional[float] = None
        self.current_blink_peak: float = 0.0
        self.current_blink_peak_time: float = 0.0
        self.last_blink_time: float = 0.0

        # Event History & Diagnostics
        self.detected_single_blinks: deque = deque(maxlen=30)
        self.rejected_events: deque = deque(maxlen=30)

    def set_parameters(
        self,
        refractory_ms: Optional[int] = None,
        min_blink_duration_ms: Optional[float] = None,
        max_blink_duration_ms: Optional[float] = None,
        hysteresis_ratio: Optional[float] = None,
    ):
        if refractory_ms is not None:
            self.refractory_sec = refractory_ms / 1000.0
        if min_blink_duration_ms is not None:
            self.min_blink_duration_ms = min_blink_duration_ms
        if max_blink_duration_ms is not None:
            self.max_blink_duration_ms = max_blink_duration_ms
        if hysteresis_ratio is not None:
            self.hysteresis_ratio = hysteresis_ratio

    def reset(self):
        """Resets detector state and pending detections."""
        self.state = "IDLE"
        self.current_blink_start = None
        self.current_blink_peak = 0.0
        self.current_blink_peak_time = 0.0
        self.last_blink_time = 0.0

    def process_sample(
        self,
        filtered_val: float,
        timestamp: float,
        threshold: float,
        is_signal_good: bool = True,
        is_calibrated: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Processes a single real-time filtered EOG sample.
        Returns a single-blink event dict if a valid deliberate blink has concluded, else None.
        """
        # If signal quality is degraded or calibration missing, disarm immediately
        if not is_signal_good or not is_calibrated:
            if self.state == "IN_BLINK":
                self.state = "IDLE"
                self.current_blink_start = None
            return None

        # Check refractory cool-down
        if self.state == "REFRACTORY":
            if timestamp - self.last_blink_time >= self.refractory_sec:
                self.state = "IDLE"
            else:
                return None

        reset_threshold = threshold * self.hysteresis_ratio

        # State 1: IDLE - looking for rising edge exceeding threshold
        if self.state == "IDLE":
            if filtered_val >= threshold:
                self.state = "IN_BLINK"
                self.current_blink_start = timestamp
                self.current_blink_peak = filtered_val
                self.current_blink_peak_time = timestamp

        # State 2: IN_BLINK - tracking peak and waiting for falling edge below reset_threshold
        elif self.state == "IN_BLINK":
            if filtered_val > self.current_blink_peak:
                self.current_blink_peak = filtered_val
                self.current_blink_peak_time = timestamp

            # Falling edge condition
            if filtered_val <= reset_threshold:
                duration_ms = (timestamp - (self.current_blink_start or timestamp)) * 1000.0

                # Validate blink morphology (duration check)
                if self.min_blink_duration_ms <= duration_ms <= self.max_blink_duration_ms:
                    # Valid Single Blink confirmed!
                    self.state = "REFRACTORY"
                    self.last_blink_time = timestamp

                    event_data = {
                        "type": "SINGLE_BLINK",
                        "timestamp": timestamp,
                        "peak_time": self.current_blink_peak_time,
                        "amplitude": round(self.current_blink_peak, 1),
                        "duration_ms": round(duration_ms, 1),
                    }
                    self.detected_single_blinks.append(event_data)
                    self.current_blink_start = None
                    return event_data
                else:
                    # Rejected: sustained eye gaze/saccade or high-frequency spike
                    self.rejected_events.append({
                        "timestamp": timestamp,
                        "amplitude": round(self.current_blink_peak, 1),
                        "duration_ms": round(duration_ms, 1),
                        "reason": "DURATION_OUT_OF_BOUNDS",
                    })
                    self.state = "IDLE"
                    self.current_blink_start = None

        return None

