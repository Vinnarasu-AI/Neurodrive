"""
DSP filtering modules for EOG signals.
Vertical EOG features:
- Low-frequency DC drift / head movements (< 0.5 Hz)
- Powerline noise (50 Hz / 60 Hz hum)
- Muscle/EMG artifacts and high-frequency noise (> 15 Hz - 30 Hz)
- Dominant blink energy: ~0.5 Hz to 10-15 Hz.
"""

from typing import Tuple, Optional
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi, iirnotch


class RealtimeEOGFilter:
    def __init__(
        self,
        sample_rate: float = 500.0,
        lowcut: float = 0.5,
        highcut: float = 15.0,
        notch_freq: float = 50.0,
        notch_q: float = 30.0,
        filter_order: int = 3,
    ):
        self.sample_rate = sample_rate
        self.lowcut = lowcut
        self.highcut = highcut
        self.notch_freq = notch_freq
        self.notch_q = notch_q
        self.filter_order = filter_order

        # Bandpass filter design
        nyquist = 0.5 * sample_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        self.b_band, self.a_band = butter(filter_order, [low, high], btype="band")
        self.zi_band = lfilter_zi(self.b_band, self.a_band)

        # Notch filter design (for powerline suppression)
        self.b_notch, self.a_notch = iirnotch(notch_freq, notch_q, sample_rate)
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch)

        self.initialized = False

    def reset(self, initial_value: float = 2048.0):
        """Resets filter state using the provided initial DC level to avoid filter settling spikes."""
        self.zi_band = lfilter_zi(self.b_band, self.a_band) * initial_value
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch) * initial_value
        self.initialized = True

    def filter_sample(self, sample: float) -> float:
        """Processes a single real-time sample through the notch and bandpass cascaded filters."""
        if not self.initialized:
            self.reset(sample)

        # 1. Notch filter
        y_notch, self.zi_notch = lfilter(
            self.b_notch, self.a_notch, [sample], zi=self.zi_notch
        )
        # 2. Bandpass filter
        y_band, self.zi_band = lfilter(
            self.b_band, self.a_band, y_notch, zi=self.zi_band
        )
        return float(y_band[0])

    def filter_chunk(self, samples: np.ndarray) -> np.ndarray:
        """Processes a chunk of samples in sequence while maintaining filter continuity."""
        if len(samples) == 0:
            return np.array([], dtype=np.float64)

        if not self.initialized:
            self.reset(float(samples[0]))

        y_notch, self.zi_notch = lfilter(
            self.b_notch, self.a_notch, samples, zi=self.zi_notch
        )
        y_band, self.zi_band = lfilter(
            self.b_band, self.a_band, y_notch, zi=self.zi_band
        )
        return y_band

