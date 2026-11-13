"""
Signal quality evaluation for NPG Lite vertical EOG.
Evaluates:
- Saturation / Clipping check (ADC bounds: 0 or 4095 for 12-bit ADC)
- Lead contact / disconnection (flatline or 0 variance)
- Excessive noise / motion artifact / 50Hz mains hum
- Calculated Signal-to-Noise Ratio (SNR) or Quality Score (0 to 100%)
"""

from typing import Dict, Any
import numpy as np


class SignalQualityEvaluator:
    def __init__(
        self,
        adc_max: float = 4095.0,
        flatline_std_threshold: float = 2.0,
        saturation_margin: float = 20.0,
        noise_std_threshold: float = 600.0,
    ):
        self.adc_max = adc_max
        self.flatline_std = flatline_std_threshold
        self.saturation_margin = saturation_margin
        self.noise_std_threshold = noise_std_threshold

    def evaluate(self, raw_window: np.ndarray, filtered_window: np.ndarray) -> Dict[str, Any]:
        """
        Evaluates a window of signal (typically 0.5 to 2.0 seconds).
        Returns status dict: {
            "score": float (0-100),
            "is_good": bool,
            "status": "GOOD" | "CLIPPING" | "FLATLINE" | "HIGH_NOISE",
            "mean": float,
            "std": float,
            "snr_db": float
        }
        """
        if len(raw_window) < 10:
            return {
                "score": 0.0,
                "is_good": False,
                "status": "INSUFFICIENT_DATA",
                "mean": 0.0,
                "std": 0.0,
                "snr_db": 0.0,
            }

        mean_raw = float(np.mean(raw_window))
        std_raw = float(np.std(raw_window))
        std_filt = float(np.std(filtered_window))

        # 1. Saturation / Railing
        clip_low = np.sum(raw_window <= self.saturation_margin)
        clip_high = np.sum(raw_window >= (self.adc_max - self.saturation_margin))
        clipping_ratio = (clip_low + clip_high) / len(raw_window)

        if clipping_ratio > 0.05:
            return {
                "score": 10.0,
                "is_good": False,
                "status": "CLIPPING",
                "mean": round(mean_raw, 2),
                "std": round(std_raw, 2),
                "snr_db": 0.0,
            }

        # 2. Flatline / Disconnected electrode check
        if std_raw < self.flatline_std:
            return {
                "score": 0.0,
                "is_good": False,
                "status": "FLATLINE",
                "mean": round(mean_raw, 2),
                "std": round(std_raw, 2),
                "snr_db": 0.0,
            }

        # 3. High noise / extreme motion check
        if std_raw > self.noise_std_threshold:
            return {
                "score": 30.0,
                "is_good": False,
                "status": "HIGH_NOISE",
                "mean": round(mean_raw, 2),
                "std": round(std_raw, 2),
                "snr_db": 5.0,
            }

        # 4. Standard quality calculation
        # Healthy EOG signal variance is bounded with high in-band energy vs out-of-band noise
        out_of_band_noise = max(1e-4, abs(std_raw - std_filt))
        snr_linear = std_filt / out_of_band_noise
        snr_db = float(20.0 * np.log10(max(1.0, snr_linear)))

        # Normalize score between 0 and 100
        # When signal is not flatlining, not clipping, and not overflowing noise threshold,
        # it is acceptable for blink detection.
        base_score = 70.0
        score = min(100.0, max(40.0, base_score + snr_db * 2.0))

        return {
            "score": round(score, 1),
            "is_good": True,
            "status": "GOOD",
            "mean": round(mean_raw, 2),
            "std": round(std_raw, 2),
            "snr_db": round(snr_db, 2),
        }

