"""
Robust Double-Blink Detector for Vertical EOG.

Key criteria from requirements:
1. Not a simple threshold trigger.
2. Segment individual blinks using hysteresis (trigger threshold + reset baseline).
3. Check event duration (e.g., 100ms - 400ms per blink). Eye movements (saccades)
   typically produce square wave steps or longer offsets, whereas blinks are sharp biphasic spikes.
4. Detect two distinct deliberate blink events within a configurable inter-blink window:
   min_gap_ms (e.g. 150 ms) to max_gap_ms (e.g. 850 ms).
5. Enforce refractory period (e.g. 600 ms) after a valid double-blink to avoid triple-blink/multi-trigger re-firing.
6. Guard with signal quality and calibration checks: no action if noise is high or uncalibrated.
7. Return event details for diagnostics & visual UI feedback.
"""

from typing import Optional, Dict, Any, List
import time
from collections import deque
import numpy as np


class BlinkEvent:
    def __init__(self, start_time: float, peak_time: float, peak_amplitude: float, duration_ms: float):
        self.start_time = start_time
        self.peak_time = peak_time
        self.peak_amplitude = peak_amplitude
        self.duration_ms = duration_ms


class DoubleBlinkDetector:
    def __init__(
        self,
        sample_rate: int = 500,
        min_gap_ms: int = 150,
        max_gap_ms: int = 850,
        refractory_ms: int = 600,
        min_blink_duration_ms: float = 60.0,
        max_blink_duration_ms: float = 400.0,
        hysteresis_ratio: float = 0.4,
    ):
        self.sample_rate = sample_rate
        self.min_gap_sec = min_gap_ms / 1000.0
        self.max_gap_sec = max_gap_ms / 1000.0
        self.refractory_sec = refractory_ms / 1000.0
        self.min_blink_duration_ms = min_blink_duration_ms
        self.max_blink_duration_ms = max_blink_duration_ms
        self.hysteresis_ratio = hysteresis_ratio

        # State machine
        self.state = "IDLE"  # "IDLE", "IN_BLINK", "WAIT_SECOND_BLINK", "REFRACTORY"
        self.current_blink_start: Optional[float] = None
        self.current_blink_peak: float = 0.0
        self.current_blink_peak_time: float = 0.0

        self.last_valid_blink: Optional[BlinkEvent] = None
        self.last_double_blink_time: float = 0.0

        # Diagnostics & History
        self.detected_single_blinks: deque = deque(maxlen=20)
        self.detected_double_blinks: deque = deque(maxlen=20)

    def set_parameters(
        self,
        min_gap_ms: Optional[int] = None,
        max_gap_ms: Optional[int] = None,
        refractory_ms: Optional[int] = None,
    ):
        if min_gap_ms is not None:
            self.min_gap_sec = min_gap_ms / 1000.0
        if max_gap_ms is not None:
            self.max_gap_sec = max_gap_ms / 1000.0
        if refractory_ms is not None:
            self.refractory_sec = refractory_ms / 1000.0

    def process_sample(
        self,
        filtered_val: float,
        timestamp: float,
        threshold: float,
        is_signal_good: bool = True,
        is_calibrated: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Process single real-time filtered EOG sample.
        Returns a dict describing the double-blink event if triggered, else None.
        """
        # If signal quality is bad or not calibrated, reset state machine for safety
        if not is_signal_good or not is_calibrated:
            if self.state in ["IN_BLINK", "WAIT_SECOND_BLINK"]:
                self.state = "IDLE"
                self.last_valid_blink = None
            return None

        # Check refractory period
        if self.state == "REFRACTORY":
            if timestamp - self.last_double_blink_time >= self.refractory_sec:
                self.state = "IDLE"
            else:
                return None

        # Check expiration of first blink if waiting for second
        if self.state == "WAIT_SECOND_BLINK":
            if self.last_valid_blink is not None:
                gap_from_first = timestamp - self.last_valid_blink.peak_time
                if gap_from_first > self.max_gap_sec:
                    # Timed out waiting for second blink
                    self.state = "IDLE"
                    self.last_valid_blink = None

        reset_threshold = threshold * self.hysteresis_ratio

        # State 1: IDLE or WAIT_SECOND_BLINK - looking for onset of a blink
        if self.state in ["IDLE", "WAIT_SECOND_BLINK"]:
            if filtered_val >= threshold:
                # Rising edge of a blink
                self.state_prev = self.state
                self.state = "IN_BLINK"
                self.current_blink_start = timestamp
                self.current_blink_peak = filtered_val
                self.current_blink_peak_time = timestamp

        # State 2: IN_BLINK - tracking peak and falling edge below reset_threshold
        elif self.state == "IN_BLINK":
            if filtered_val > self.current_blink_peak:
                self.current_blink_peak = filtered_val
                self.current_blink_peak_time = timestamp

            # Falling edge condition
            if filtered_val <= reset_threshold:
                duration_ms = (timestamp - (self.current_blink_start or timestamp)) * 1000.0

                # Validate blink morphology (duration check)
                if self.min_blink_duration_ms <= duration_ms <= self.max_blink_duration_ms:
                    blink_ev = BlinkEvent(
                        start_time=self.current_blink_start or timestamp,
                        peak_time=self.current_blink_peak_time,
                        peak_amplitude=self.current_blink_peak,
                        duration_ms=duration_ms,
                    )
                    self.detected_single_blinks.append({
                        "time": blink_ev.peak_time,
                        "amplitude": round(blink_ev.peak_amplitude, 1),
                        "duration_ms": round(blink_ev.duration_ms, 1),
                    })

                    # Check if this completes a double blink
                    if self.last_valid_blink is not None:
                        gap_sec = blink_ev.peak_time - self.last_valid_blink.peak_time
                        if self.min_gap_sec <= gap_sec <= self.max_gap_sec:
                            # DOUBLE BLINK CONFIRMED!
                            self.state = "REFRACTORY"
                            self.last_double_blink_time = timestamp
                            first_ev = self.last_valid_blink
                            self.last_valid_blink = None

                            event_data = {
                                "type": "DOUBLE_BLINK",
                                "timestamp": timestamp,
                                "gap_ms": round(gap_sec * 1000.0, 1),
                                "first_amplitude": round(first_ev.peak_amplitude, 1),
                                "second_amplitude": round(blink_ev.peak_amplitude, 1),
                                "first_duration_ms": round(first_ev.duration_ms, 1),
                                "second_duration_ms": round(blink_ev.duration_ms, 1),
                            }
                            self.detected_double_blinks.append(event_data)
                            return event_data
                        else:
                            # Gap was too small or too large; promote current blink to new first
                            self.last_valid_blink = blink_ev
                            self.state = "WAIT_SECOND_BLINK"
                    else:
                        # First blink registered
                        self.last_valid_blink = blink_ev
                        self.state = "WAIT_SECOND_BLINK"
                else:
                    # Duration out of bounds (likely a sustained gaze/saccade or high freq spike)
                    # Reset back to previous state or IDLE
                    self.state = "IDLE"
                    self.last_valid_blink = None

        return None

    def reset(self):
        self.state = "IDLE"
        self.current_blink_start = None
        self.current_blink_peak = 0.0
        self.current_blink_peak_time = 0.0
        self.last_valid_blink = None
        self.last_double_blink_time = 0.0

