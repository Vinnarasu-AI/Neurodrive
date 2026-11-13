import pytest
import pytest_asyncio
from app.core.state import ApplicationStateManager, AppMode
from app.relay.relay_client import RelayClient


def test_state_manager_mutual_exclusivity():
    sm = ApplicationStateManager()
    assert sm.current_mode == AppMode.IDLE
    assert not sm.is_smart_home_active()

    # Activate Smart Home
    ok, msg = sm.request_activation("SMART_HOME_ACTIVE")
    assert ok is True
    assert sm.is_smart_home_active()
    assert sm.current_mode == AppMode.SMART_HOME_ACTIVE

    # Activate Game Mode (Now valid and active!)
    ok, msg = sm.request_activation("GAME_ACTIVE")
    assert ok is True
    assert sm.is_game_active()
    assert not sm.is_smart_home_active()
    assert sm.current_mode == AppMode.GAME_ACTIVE

    # Attempt Wheelchair (Strictly reserved Coming Soon)
    ok, msg = sm.request_activation("WHEELCHAIR_ACTIVE")
    assert ok is False
    assert "Coming Soon" in msg
    assert sm.is_game_active()

    # Deactivate back to IDLE
    sm.deactivate_all("User manual stop")
    assert sm.current_mode == AppMode.IDLE
    assert not sm.is_smart_home_active()


@pytest.mark.asyncio
async def test_relay_client_deduplication():
    client = RelayClient(use_mock=True)

    # Initial state is OFF
    status = await client.get_status()
    assert status["state"] == "OFF"

    # Turning OFF while already OFF must deduplicate
    res_off = await client.turn_off()
    assert res_off["success"] is True
    assert res_off.get("deduplicated") is True

    # Turn ON
    res_on = await client.turn_on()
    assert res_on["success"] is True
    assert res_on["state"] == "ON"
    assert not res_on.get("deduplicated")

    # Turn ON again - deduplication triggered
    res_on_dup = await client.turn_on()
    assert res_on_dup["success"] is True
    assert res_on_dup.get("deduplicated") is True
    assert res_on_dup["state"] == "ON"

    # Toggle ON -> OFF
    res_tog = await client.toggle()
    assert res_tog["success"] is True
    assert res_tog["state"] == "OFF"

