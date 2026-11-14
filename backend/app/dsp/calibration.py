"""
Guided Calibration Manager for vertical EOG.

Supports independent profiles:
- Smart Home profile (for Double-Blink detection)
- Game profile (for Single-Blink fast reaction detection)

Workflows:
Phase 1: REST (Center Gaze Baseline) - 3 seconds
Phase 2: DELIBERATE BLINKS - 4 seconds
Phase 3: Compute individual baseline, peak threshold, and noise floor
"""

import time
from typing import Dict, Any, Optional
import numpy as np


class CalibrationProfile:
    def __init__(self, mode_name: str = "smart_home", default_threshold: float = 200.0):
        self.mode_name = mode_name
        self.calibrated = False
        self.baseline_mean: float = 2048.0
        self.baseline_std: float = 20.0
        self.blink_peak_threshold: float = default_threshold
        self.last_calibrated_at: Optional[float] = None


class CalibrationManager:
    def __init__(self, sample_rate: int = 500):
        self.sample_rate = sample_rate
        self.is_calibrating = False
        self.active_calib_target = "smart_home"  # "smart_home" or "game"
        self.stage = "IDLE"  # "IDLE", "BASELINE", "BLINKS", "COMPLETED", "FAILED"
        self.stage_start_time = 0.0

        # Buffers
        self.baseline_samples = []
        self.blink_samples = []

        # Distinct profiles
        self.profiles: Dict[str, CalibrationProfile] = {
            "smart_home": CalibrationProfile("smart_home", default_threshold=220.0),
            "game": CalibrationProfile("game", default_threshold=180.0),
        }

    @property
    def calibrated(self) -> bool:
        return self.profiles["smart_home"].calibrated

    @property
    def blink_peak_threshold(self) -> float:
        return self.profiles["smart_home"].blink_peak_threshold

    @blink_peak_threshold.setter
    def blink_peak_threshold(self, val: float):
        self.profiles["smart_home"].blink_peak_threshold = val

    @property
    def game_calibrated(self) -> bool:
        return self.profiles["game"].calibrated

    @property
    def game_blink_threshold(self) -> float:
        return self.profiles["game"].blink_peak_threshold

    @game_blink_threshold.setter
    def game_blink_threshold(self, val: float):
        self.profiles["game"].blink_peak_threshold = val

    def start_calibration(self, target: str = "smart_home"):
        """Starts stage 1: Baseline acquisition for the target application."""
        self.active_calib_target = target if target in self.profiles else "smart_home"
        self.is_calibrating = True
        self.stage = "BASELINE"
        self.stage_start_time = time.time()
        self.baseline_samples = []
        self.blink_samples = []

    def feed_sample(self, raw_sample: float, filtered_sample: float):
        if not self.is_calibrating:
            return

        now = time.time()
        elapsed = now - self.stage_start_time

        if self.stage == "BASELINE":
            self.baseline_samples.append((raw_sample, filtered_sample))
            if elapsed >= 3.0:
                self.stage = "BLINKS"
                self.stage_start_time = now

        elif self.stage == "BLINKS":
            self.blink_samples.append((raw_sample, filtered_sample))
            if elapsed >= 4.0:
                self.compute_parameters()

    def compute_parameters(self) -> bool:
        prof = self.profiles[self.active_calib_target]
        if len(self.baseline_samples) < 200 or len(self.blink_samples) < 200:
            self.stage = "FAILED"
            self.is_calibrating = False
            return False

        base_raw = np.array([s[0] for s in self.baseline_samples])
        base_filt = np.array([s[1] for s in self.baseline_samples])
        blink_filt = np.array([s[1] for s in self.blink_samples])

        prof.baseline_mean = float(np.mean(base_raw))
        prof.baseline_std = float(np.std(base_filt))

        max_blink_amp = float(np.percentile(blink_filt, 99))
        baseline_noise_ceiling = float(np.percentile(np.abs(base_filt), 95))

        # Game mode prefers slightly more responsive/faster sensitivity
        sensitivity_ratio = 0.40 if self.active_calib_target == "game" else 0.45
        min_threshold = 140.0 if self.active_calib_target == "game" else 150.0

        if max_blink_amp > baseline_noise_ceiling * 1.6:
            prof.blink_peak_threshold = max(
                min_threshold, (baseline_noise_ceiling + max_blink_amp) * sensitivity_ratio
            )
        else:
            prof.blink_peak_threshold = max(min_threshold, prof.baseline_std * 3.5)

        prof.calibrated = True
        prof.last_calibrated_at = time.time()
        self.stage = "COMPLETED"
        self.is_calibrating = False
        return True

    def get_status(self) -> Dict[str, Any]:
        sh_prof = self.profiles["smart_home"]
        gm_prof = self.profiles["game"]
        return {
            "calibrated": sh_prof.calibrated,
            "game_calibrated": gm_prof.calibrated,
            "is_calibrating": self.is_calibrating,
            "active_target": self.active_calib_target,
            "stage": self.stage,
            "smart_home": {
                "calibrated": sh_prof.calibrated,
                "baseline_mean": round(sh_prof.baseline_mean, 2),
                "baseline_std": round(sh_prof.baseline_std, 2),
                "blink_peak_threshold": round(sh_prof.blink_peak_threshold, 2),
                "last_calibrated_at": sh_prof.last_calibrated_at,
            },
            "game": {
                "calibrated": gm_prof.calibrated,
                "baseline_mean": round(gm_prof.baseline_mean, 2),
                "baseline_std": round(gm_prof.baseline_std, 2),
                "blink_peak_threshold": round(gm_prof.blink_peak_threshold, 2),
                "last_calibrated_at": gm_prof.last_calibrated_at,
            },
            # Compatibility aliases for Smart Home
            "baseline_mean": round(sh_prof.baseline_mean, 2),
            "baseline_std": round(sh_prof.baseline_std, 2),
            "blink_peak_threshold": round(sh_prof.blink_peak_threshold, 2),
            "last_calibrated_at": sh_prof.last_calibrated_at,
        }
