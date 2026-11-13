import pytest
import numpy as np
from app.dsp.single_blink_detector import SingleBlinkDetector
from app.core.state import ApplicationStateManager, AppMode
from app.services.automation_service import HomeAutomationService
from app.relay.relay_client import RelayClient
from app.serial.serial_manager import SerialManager


def test_valid_single_blink_triggers_one_event():
    detector = SingleBlinkDetector(sample_rate=500, refractory_ms=350, min_blink_duration_ms=60.0, max_blink_duration_ms=350.0)
    dt = 1.0 / 500.0
    thresh = 200.0

    # 150ms blink (within 60 - 350ms window)
    t = 0.0
    triggered = []
    # 50 points baseline
    for _ in range(50):
        t += dt
        ev = detector.process_sample(0.0, t, thresh)
        if ev: triggered.append(ev)

    # 75 points blink pulse (150ms)
    pulse = 350.0 * np.sin(np.linspace(0, np.pi, 75))
    for v in pulse:
        t += dt
        ev = detector.process_sample(float(v), t, thresh)
        if ev: triggered.append(ev)

    # 50 points return to baseline
    for _ in range(50):
        t += dt
        ev = detector.process_sample(0.0, t, thresh)
        if ev: triggered.append(ev)

    assert len(triggered) == 1
    assert triggered[0]["type"] == "SINGLE_BLINK"
    assert 100.0 <= triggered[0]["duration_ms"] <= 200.0


def test_single_blink_does_not_generate_repeated_jumps():
    detector = SingleBlinkDetector(sample_rate=500, refractory_ms=400)
    dt = 1.0 / 500.0
    thresh = 200.0
    t = 0.0
    triggered = []

    # One blink pulse
    pulse = 350.0 * np.sin(np.linspace(0, np.pi, 75))
    for v in pulse:
        t += dt
        ev = detector.process_sample(float(v), t, thresh)
        if ev: triggered.append(ev)

    # Continued high-frequency wobble or baseline
    for _ in range(100):
        t += dt
        ev = detector.process_sample(0.0, t, thresh)
        if ev: triggered.append(ev)

    # Exactly ONE jump must be emitted
    assert len(triggered) == 1


def test_slow_eye_movement_saccade_rejected():
    detector = SingleBlinkDetector(sample_rate=500, min_blink_duration_ms=60.0, max_blink_duration_ms=350.0)
    dt = 1.0 / 500.0
    thresh = 200.0
    t = 0.0

    # Slow vertical saccade: 600ms duration (> 350ms max duration)
    slow_pulse = 350.0 * np.sin(np.linspace(0, np.pi, 300))
    triggered = []
    for v in slow_pulse:
        t += dt
        ev = detector.process_sample(float(v), t, thresh)
        if ev: triggered.append(ev)

    assert len(triggered) == 0
    assert len(detector.rejected_events) == 1
    assert detector.rejected_events[0]["reason"] == "DURATION_OUT_OF_BOUNDS"


def test_poor_quality_signal_rejected():
    detector = SingleBlinkDetector(sample_rate=500)
    dt = 1.0 / 500.0
    thresh = 200.0
    t = 0.0

    pulse = 350.0 * np.sin(np.linspace(0, np.pi, 75))
    triggered = []
    for v in pulse:
        t += dt
        # is_signal_good=False
        ev = detector.process_sample(float(v), t, thresh, is_signal_good=False)
        if ev: triggered.append(ev)

    assert len(triggered) == 0


def test_strict_gesture_routing_exclusivity():
    state_mgr = ApplicationStateManager()
    relay_client = RelayClient(use_mock=True)
    serial_mgr = SerialManager(use_mock=True)
    svc = HomeAutomationService(state_mgr, relay_client, serial_mgr)

    # 1. When in IDLE: neither double blink nor single blink can actuate relay or game
    assert state_mgr.current_mode == AppMode.IDLE
    svc._handle_single_blink_event({"type": "SINGLE_BLINK", "duration_ms": 150})
    assert svc.latest_game_jump is None
    assert svc.game_jump_counter == 0

    svc._handle_double_blink_event({"type": "DOUBLE_BLINK", "gap_ms": 300})
    assert relay_client.current_state == "OFF"

    # 2. When in SMART_HOME_ACTIVE:
    state_mgr.activate_smart_home()
    assert state_mgr.is_smart_home_active()
    # Single blink must NOT trigger game jump
    svc._handle_single_blink_event({"type": "SINGLE_BLINK", "duration_ms": 150})
    assert svc.latest_game_jump is None
    assert svc.game_jump_counter == 0

    # 3. When in GAME_ACTIVE:
    state_mgr.activate_game()
    assert state_mgr.is_game_active()
    assert not state_mgr.is_smart_home_active()

    # Double blink must NOT actuate relay
    svc._handle_double_blink_event({"type": "DOUBLE_BLINK", "gap_ms": 300})
    assert relay_client.current_state == "OFF"

    # Single blink triggers game jump exactly once
    svc._handle_single_blink_event({"type": "SINGLE_BLINK", "duration_ms": 140, "amplitude": 320})
    assert svc.latest_game_jump is not None
    assert svc.game_jump_counter == 1
    assert svc.latest_game_jump["jump_id"] == 1

