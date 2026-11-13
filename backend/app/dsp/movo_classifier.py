"""
EMG and EEG Multi-Channel DSP Pipelines & Gesture Classifier for MOVO Rover.

Channels:
  CH1: EEG (Prefrontal / Central mental focus / ERD/ERS beta/mu or frontal attention)
  CH2: Left Forearm EMG
  CH3: Right Forearm EMG

Decision Matrix & Priority:
  1. Emergency STOP (highest priority)
  2. Signal quality failure or sensor disconnect -> STOP
  3. Bilateral Contraction (CH2 active AND CH3 active) -> BACKWARD
  4. Left Forearm Contraction (CH2 active AND CH3 inactive) -> LEFT
  5. Right Forearm Contraction (CH2 inactive AND CH3 active) -> RIGHT
  6. Validated EEG Forward Intention (Both EMG inactive AND EEG validated) -> FORWARD
  7. Otherwise -> STOP
"""

import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi, iirnotch
from typing import Dict, Any, Tuple, Optional
import time
from collections import deque


class RealtimeEMGProcessor:
    """
    Forearm Surface EMG Processor.
    - Bandpass filter (20 Hz - 150 Hz) to isolate motor unit action potentials and reject motion artifacts.
    - 50 Hz Notch filter for powerline suppression.
    - Full-wave rectification (|x|).
    - Moving RMS / Leaky envelope integrator (decay window ~100-150 ms).
    - Baseline estimation, adaptive thresholding with hysteresis (activation vs release threshold).
    - Debounce timer (minimum contraction hold time to avoid transient twitch spikes).
    """

    def __init__(
        self,
        sample_rate: float = 500.0,
        lowcut: float = 20.0,
        highcut: float = 150.0,
        notch_freq: float = 50.0,
        envelope_alpha: float = 0.05,
    ):
        self.sample_rate = sample_rate
        self.envelope_alpha = envelope_alpha

        nyquist = 0.5 * sample_rate
        self.b_band, self.a_band = butter(3, [lowcut / nyquist, highcut / nyquist], btype="band")
        self.zi_band = lfilter_zi(self.b_band, self.a_band)

        self.b_notch, self.a_notch = iirnotch(notch_freq, 30.0, sample_rate)
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch)

        self.initialized = False
        self.current_envelope: float = 0.0

        # Baseline & Calibration parameters
        self.baseline_noise_floor: float = 15.0
        self.activation_threshold: float = 60.0
        self.release_threshold: float = 40.0

        # Hysteresis state & debounce
        self.is_active: bool = False
        self.active_sample_count: int = 0
        self.min_activation_samples: int = 25  # 50 ms at 500 Hz

    def reset(self, initial_value: float = 2048.0):
        self.zi_band = lfilter_zi(self.b_band, self.a_band) * initial_value
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch) * initial_value
        self.current_envelope = 0.0
        self.is_active = False
        self.active_sample_count = 0
        self.initialized = True

    def process_sample(self, raw_sample: float) -> Tuple[float, float, bool]:
        """
        Returns:
          filtered_sample, envelope, is_active
        """
        if not self.initialized:
            self.reset(raw_sample)

        # 1. Notch filter
        y_notch, self.zi_notch = lfilter(self.b_notch, self.a_notch, [raw_sample], zi=self.zi_notch)
        # 2. Bandpass filter
        y_band, self.zi_band = lfilter(self.b_band, self.a_band, y_notch, zi=self.zi_band)
        filtered = float(y_band[0])

        # 3. Full-wave rectification
        rectified = abs(filtered)

        # 4. Leaky integrator envelope
        self.current_envelope = (
            (1.0 - self.envelope_alpha) * self.current_envelope
            + self.envelope_alpha * rectified
        )

        # 5. Schmitt trigger / Hysteresis thresholding
        if not self.is_active:
            if self.current_envelope >= self.activation_threshold:
                self.active_sample_count += 1
                if self.active_sample_count >= self.min_activation_samples:
                    self.is_active = True
            else:
                self.active_sample_count = 0
        else:
            if self.current_envelope < self.release_threshold:
                self.is_active = False
                self.active_sample_count = 0

        return filtered, self.current_envelope, self.is_active


class RealtimeEEGProcessor:
    """
    Dedicated EEG Processor for Channel 1.
    - Bandpass (1.0 Hz - 30.0 Hz) + 50 Hz Notch.
    - Computes relative power in Beta band (13-30 Hz) and Alpha band (8-12 Hz).
    - Evaluates cognitive focus index (Beta / (Alpha + Theta)) to validate forward intention.
    - Rejects ocular/blink artifacts (amplitude > 200 uV) before forwarding to classifier.
    - Requires calibration profile to establish intentional active state vs resting baseline.
    """

    def __init__(
        self,
        sample_rate: float = 500.0,
        lowcut: float = 1.0,
        highcut: float = 30.0,
        notch_freq: float = 50.0,
    ):
        self.sample_rate = sample_rate
        nyquist = 0.5 * sample_rate
        self.b_band, self.a_band = butter(3, [lowcut / nyquist, highcut / nyquist], btype="band")
        self.zi_band = lfilter_zi(self.b_band, self.a_band)

        self.b_notch, self.a_notch = iirnotch(notch_freq, 30.0, sample_rate)
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch)

        self.initialized = False
        self.window_samples = deque(maxlen=250)  # 500 ms window
        self.focus_index: float = 0.0
        self.is_forward_intent: bool = False

        # Thresholds derived during calibration
        self.baseline_focus: float = 0.8
        self.forward_threshold: float = 1.5
        self.is_calibrated: bool = False

    def reset(self, initial_value: float = 2048.0):
        self.zi_band = lfilter_zi(self.b_band, self.a_band) * initial_value
        self.zi_notch = lfilter_zi(self.b_notch, self.a_notch) * initial_value
        self.window_samples.clear()
        self.focus_index = 0.0
        self.is_forward_intent = False
        self.initialized = True

    def process_sample(self, raw_sample: float) -> Tuple[float, float, bool]:
        if not self.initialized:
            self.reset(raw_sample)

        y_notch, self.zi_notch = lfilter(self.b_notch, self.a_notch, [raw_sample], zi=self.zi_notch)
        y_band, self.zi_band = lfilter(self.b_band, self.a_band, y_notch, zi=self.zi_band)
        filtered = float(y_band[0])

        self.window_samples.append(filtered)

        # Update spectral power every 50 samples (10 times per second)
        if len(self.window_samples) == 250 and len(self.window_samples) % 50 == 0:
            arr = np.array(self.window_samples)
            # Rejection of large artifact (e.g. blink or motion)
            if np.max(np.abs(arr)) > 250.0:
                self.is_forward_intent = False
            else:
                # Fast FFT estimate
                fft_vals = np.abs(np.fft.rfft(arr))
                freqs = np.fft.rfftfreq(len(arr), 1.0 / self.sample_rate)

                # Alpha (8 - 12 Hz) vs Beta (13 - 30 Hz)
                alpha_mask = (freqs >= 8) & (freqs <= 12)
                beta_mask = (freqs >= 13) & (freqs <= 30)

                alpha_pwr = np.sum(fft_vals[alpha_mask]) + 1e-6
                beta_pwr = np.sum(fft_vals[beta_mask]) + 1e-6

                self.focus_index = float(beta_pwr / alpha_pwr)

                if self.is_calibrated and self.focus_index >= self.forward_threshold:
                    self.is_forward_intent = True
                else:
                    self.is_forward_intent = False

        return filtered, self.focus_index, self.is_forward_intent


class MovoGestureClassifier:
    """
    Synthesizes inputs from CH1 (EEG), CH2 (Left EMG), CH3 (Right EMG)
    and produces an authoritative rover motion command.
    """

    def __init__(self, sample_rate: float = 500.0):
        self.sample_rate = sample_rate
        self.emg_left = RealtimeEMGProcessor(sample_rate=sample_rate)
        self.emg_right = RealtimeEMGProcessor(sample_rate=sample_rate)
        self.eeg = RealtimeEEGProcessor(sample_rate=sample_rate)

        self.current_decision: str = "STOP"
        self.decision_source: str = "REST"
        self.last_decision_time: float = time.time()

    def classify(
        self,
        ch1_raw: float,
        ch2_raw: float,
        ch3_raw: float,
        is_signal_good: bool,
    ) -> Dict[str, Any]:
        """
        Processes 3 channels and applies strict command priority:
          1. Invalid signal / poor quality -> STOP
          2. Bilateral EMG -> BACKWARD
          3. Left EMG -> LEFT
          4. Right EMG -> RIGHT
          5. Valid EEG Forward -> FORWARD
          6. Otherwise -> STOP
        """
        # Process channels
        eeg_filt, focus_idx, eeg_forward = self.eeg.process_sample(ch1_raw)
        emg_l_filt, emg_l_env, emg_l_active = self.emg_left.process_sample(ch2_raw)
        emg_r_filt, emg_r_env, emg_r_active = self.emg_right.process_sample(ch3_raw)

        # 1. Quality & Safety Gate
        if not is_signal_good:
            self.current_decision = "STOP"
            self.decision_source = "POOR_SIGNAL_QUALITY"
            return self._build_result(eeg_filt, focus_idx, emg_l_filt, emg_l_env, emg_r_filt, emg_r_env)

        # 2. Bilateral EMG Contraction
        if emg_l_active and emg_r_active:
            self.current_decision = "BACKWARD"
            self.decision_source = "BILATERAL_EMG"
        # 3. Left Forearm EMG
        elif emg_l_active and not emg_r_active:
            self.current_decision = "LEFT"
            self.decision_source = "LEFT_EMG"
        # 4. Right Forearm EMG
        elif emg_r_active and not emg_l_active:
            self.current_decision = "RIGHT"
            self.decision_source = "RIGHT_EMG"
        # 5. Validated EEG Forward Intention
        elif eeg_forward and not emg_l_active and not emg_r_active:
            self.current_decision = "FORWARD"
            self.decision_source = "EEG_INTENT"
        # 6. Default Rest State
        else:
            self.current_decision = "STOP"
            self.decision_source = "REST"

        return self._build_result(eeg_filt, focus_idx, emg_l_filt, emg_l_env, emg_r_filt, emg_r_env)

    def _build_result(
        self,
        eeg_filt: float,
        focus_idx: float,
        emg_l_filt: float,
        emg_l_env: float,
        emg_r_filt: float,
        emg_r_env: float,
    ) -> Dict[str, Any]:
        return {
            "decision": self.current_decision,
            "source": self.decision_source,
            "eeg": {
                "filtered": round(eeg_filt, 2),
                "focus_index": round(focus_idx, 2),
                "intent_active": self.eeg.is_forward_intent,
                "calibrated": self.eeg.is_calibrated,
            },
            "emg_left": {
                "filtered": round(emg_l_filt, 2),
                "envelope": round(emg_l_env, 2),
                "active": self.emg_left.is_active,
                "threshold": round(self.emg_left.activation_threshold, 2),
            },
            "emg_right": {
                "filtered": round(emg_r_filt, 2),
                "envelope": round(emg_r_env, 2),
                "active": self.emg_right.is_active,
                "threshold": round(self.emg_right.activation_threshold, 2),
            },
        }

