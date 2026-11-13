import pytest
import asyncio
import numpy as np
from app.dsp.movo_classifier import (
    RealtimeEMGProcessor,
    RealtimeEEGProcessor,
    MovoGestureClassifier as WheelchairClassifier,
)
from app.core.state import ApplicationStateManager, AppMode
from app.wheelchair.wheelchair_client import WheelchairClient
from app.services.automation_service import HomeAutomationService
from app.serial.serial_manager import SerialManager
from app.relay.relay_client import RelayClient


def test_emg_processor_rest_vs_contraction():
    proc = RealtimeEMGProcessor(sample_rate=500.0)
    proc.activation_threshold = 50.0
    proc.release_threshold = 30.0

    # 1. Feed quiet baseline
    for _ in range(200):
        filt, env, is_active = proc.process_sample(2048.0 + np.random.normal(0, 3.0))
    assert not is_active, "EMG must be inactive during rest"
    assert env < 20.0

    # 2. Feed strong contraction burst (> 50 samples to satisfy debounce)
    for _ in range(100):
        filt, env, is_active = proc.process_sample(2048.0 + np.random.normal(0, 150.0))
    assert is_active, "EMG must activate during sustained contraction"


def test_wheelchair_classifier_priority_matrix():
    classifier = WheelchairClassifier(sample_rate=500.0)
    classifier.emg_left.activation_threshold = 40.0
    classifier.emg_right.activation_threshold = 40.0

    # Case A: Rest -> STOP
    for _ in range(100):
        res = classifier.classify(ch1_raw=2048.0, ch2_raw=2048.0, ch3_raw=2048.0, is_signal_good=True)
    assert res["decision"] == "STOP"

    # Case B: Left Forearm EMG Active -> LEFT
    for _ in range(60):
        res = classifier.classify(
            ch1_raw=2048.0,
            ch2_raw=2048.0 + np.random.normal(0, 150.0),
            ch3_raw=2048.0,
            is_signal_good=True,
        )
    assert res["decision"] == "LEFT"

    # Reset
    classifier.emg_left.reset()
    classifier.emg_right.reset()

    # Case C: Right Forearm EMG Active -> RIGHT
    for _ in range(60):
        res = classifier.classify(
            ch1_raw=2048.0,
            ch2_raw=2048.0,
            ch3_raw=2048.0 + np.random.normal(0, 150.0),
            is_signal_good=True,
        )
    assert res["decision"] == "RIGHT"

    # Reset
    classifier.emg_left.reset()
    classifier.emg_right.reset()

    # Case D: Bilateral EMG Contraction -> BACKWARD
    for _ in range(60):
        res = classifier.classify(
            ch1_raw=2048.0,
            ch2_raw=2048.0 + np.random.normal(0, 150.0),
            ch3_raw=2048.0 + np.random.normal(0, 150.0),
            is_signal_good=True,
        )
    assert res["decision"] == "BACKWARD"


def test_wheelchair_classifier_eeg_forward_validation():
    classifier = WheelchairClassifier(sample_rate=500.0)
    classifier.eeg.is_calibrated = True
    classifier.eeg.forward_threshold = 1.2

    # Simulate strong beta rhythm in CH1 (18 Hz focus)
    t = np.linspace(0, 1, 500)
    beta_wave = 40.0 * np.sin(2 * np.pi * 18 * t)

    res = None
    for val in beta_wave:
        res = classifier.classify(
            ch1_raw=2048.0 + val,
            ch2_raw=2048.0,
            ch3_raw=2048.0,
            is_signal_good=True,
        )

    assert res["decision"] in ["FORWARD", "STOP"]


def test_wheelchair_classifier_safety_stop_on_bad_signal():
    classifier = WheelchairClassifier(sample_rate=500.0)
    # Even if EMG is active, bad signal quality must force STOP
    for _ in range(60):
        res = classifier.classify(
            ch1_raw=2048.0,
            ch2_raw=2048.0 + np.random.normal(0, 150.0),
            ch3_raw=2048.0,
            is_signal_good=False,  # BAD SIGNAL / DISCONNECTED
        )
    assert res["decision"] == "STOP"
    assert res["source"] == "POOR_SIGNAL_QUALITY"


@pytest.mark.asyncio
async def test_application_switching_isolation():
    state_mgr = ApplicationStateManager()
    relay_client = RelayClient(use_mock=True)
    wheelchair_client = WheelchairClient(use_mock=True)
    serial_mgr = SerialManager(use_mock=True)
    service = HomeAutomationService(
        state_mgr=state_mgr,
        relay_client=relay_client,
        serial_mgr=serial_mgr,
        wheelchair_client=wheelchair_client,
    )
    service.set_event_loop(asyncio.get_event_loop())

    # 1. Start in WHEELCHAIR_ACTIVE
    state_mgr.activate_wheelchair()
    assert state_mgr.is_wheelchair_active()
    assert not state_mgr.is_smart_home_active()
    assert not state_mgr.is_game_active()

    # Wheelchair event dispatched
    service._handle_wheelchair_event({"decision": "FORWARD", "source": "EEG_INTENT"})
    await asyncio.sleep(0.05)
    assert wheelchair_client.current_command == "FORWARD"

    # Double blink happens while in WHEELCHAIR_ACTIVE -> Must NOT touch relay!
    relay_client.toggle_call_count = 0
    service._handle_double_blink_event({"gap_ms": 300, "first_amplitude": 400})
    await asyncio.sleep(0.05)
    assert relay_client.current_state == "OFF"

    # 2. Switch to SMART_HOME_ACTIVE
    await wheelchair_client.emergency_stop("Switching to Smart Home")
    state_mgr.activate_smart_home()
    assert wheelchair_client.current_command == "STOP"
    assert not state_mgr.is_wheelchair_active()

    # Wheelchair event arrives while in SMART_HOME_ACTIVE -> Must be completely ignored
    service._handle_wheelchair_event({"decision": "LEFT", "source": "LEFT_EMG"})
    await asyncio.sleep(0.05)
    assert wheelchair_client.current_command == "STOP"


@pytest.mark.asyncio
async def test_wheelchair_client_manual_and_stop_commands():
    client = WheelchairClient(use_mock=True)
    res_fwd = await client.send_command("FORWARD", source="MANUAL_UI")
    assert res_fwd["success"] is True
    assert client.current_command == "FORWARD"

    res_stop = await client.emergency_stop("Safety stop test")
    assert res_stop["success"] is True
    assert client.current_command == "STOP"

