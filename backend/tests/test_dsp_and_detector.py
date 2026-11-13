import pytest
import numpy as np
from app.dsp.filters import RealtimeEOGFilter
from app.dsp.quality import SignalQualityEvaluator
from app.dsp.blink_detector import DoubleBlinkDetector


def test_filters_stability():
    f = RealtimeEOGFilter(sample_rate=500.0, lowcut=0.5, highcut=15.0, notch_freq=50.0)
    # Test step response with DC offset (2048)
    dc_input = np.ones(500) * 2048.0
    out = f.filter_chunk(dc_input)

    # After initial settling, DC signal through bandpass filter must settle towards ~0
    assert abs(out[-1]) < 5.0
    assert not np.any(np.isnan(out))


def test_signal_quality_evaluator():
    evaluator = SignalQualityEvaluator()

    # Flatline test
    flat_data = np.ones(100) * 2048.0
    res = evaluator.evaluate(flat_data, flat_data * 0)
    assert res["status"] == "FLATLINE"
    assert res["is_good"] is False

    # Clipping test
    clipped_data = np.ones(100) * 4095.0
    res_clip = evaluator.evaluate(clipped_data, clipped_data * 0)
    assert res_clip["status"] == "CLIPPING"
    assert res_clip["is_good"] is False

    # Good EOG baseline test
    np.random.seed(42)
    good_raw = 2048.0 + np.random.normal(0, 15.0, 500)
    good_filt = np.random.normal(0, 10.0, 500)
    res_good = evaluator.evaluate(good_raw, good_filt)
    assert res_good["status"] == "GOOD"
    assert res_good["is_good"] is True


def test_double_blink_detector_happy_path():
    detector = DoubleBlinkDetector(
        sample_rate=500,
        min_gap_ms=150,
        max_gap_ms=850,
        refractory_ms=600,
        min_blink_duration_ms=50.0,
        max_blink_duration_ms=350.0,
    )

    threshold = 300.0
    dt = 1.0 / 500.0
    current_time = 0.0

    def generate_blink(start_t, peak_amp=400.0, dur_sec=0.15):
        # Generates half-sine blink profile
        n_pts = int(dur_sec / dt)
        t_arr = np.linspace(0, np.pi, n_pts)
        amps = peak_amp * np.sin(t_arr)
        return amps

    triggered_event = None

    # 1. Baseline 0.5s
    for _ in range(250):
        current_time += dt
        ev = detector.process_sample(0.0, current_time, threshold)
        if ev:
            triggered_event = ev

    # 2. First Blink (duration 150ms)
    b1_amps = generate_blink(current_time, peak_amp=450.0, dur_sec=0.15)
    for a in b1_amps:
        current_time += dt
        ev = detector.process_sample(a, current_time, threshold)
        if ev:
            triggered_event = ev

    assert detector.last_valid_blink is not None
    assert triggered_event is None

    # 3. Inter-blink gap 300ms
    for _ in range(150):
        current_time += dt
        ev = detector.process_sample(0.0, current_time, threshold)
        if ev:
            triggered_event = ev

    # 4. Second Blink (duration 150ms)
    b2_amps = generate_blink(current_time, peak_amp=480.0, dur_sec=0.15)
    for a in b2_amps:
        current_time += dt
        ev = detector.process_sample(a, current_time, threshold)
        if ev:
            triggered_event = ev

    # Double blink should now be triggered!
    assert triggered_event is not None
    assert triggered_event["type"] == "DOUBLE_BLINK"
    assert 200.0 <= triggered_event["gap_ms"] <= 600.0


def test_double_blink_detector_rejects_single_blink():
    detector = DoubleBlinkDetector(
        sample_rate=500,
        min_gap_ms=150,
        max_gap_ms=500,
        refractory_ms=600,
    )
    threshold = 300.0
    dt = 1.0 / 500.0
    current_time = 0.0

    # Single blink
    amps = 400.0 * np.sin(np.linspace(0, np.pi, 75))  # 150ms
    for a in amps:
        current_time += dt
        ev = detector.process_sample(a, current_time, threshold)
        assert ev is None

    # Wait 1.5 seconds (exceeding max_gap_ms)
    for _ in range(750):
        current_time += dt
        ev = detector.process_sample(0.0, current_time, threshold)
        assert ev is None

    # State must have reverted to IDLE
    assert detector.state == "IDLE"
    assert detector.last_valid_blink is None

