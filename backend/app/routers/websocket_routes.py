from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
from typing import Dict, Any

from app.serial.serial_manager import SerialManager
from app.core.state import ApplicationStateManager
from app.relay.relay_client import RelayClient
from app.services.automation_service import HomeAutomationService

logger = logging.getLogger("neurodrive.ws")
router = APIRouter(tags=["WebSocket"])


def get_websocket_routes(
    serial_mgr: SerialManager,
    state_mgr: ApplicationStateManager,
    relay_client: RelayClient,
    auto_service: HomeAutomationService,
) -> APIRouter:
    @router.websocket("/ws/stream")
    async def websocket_stream(websocket: WebSocket):
        await websocket.accept()
        logger.info("Frontend WebSocket client connected to real-time EOG feed")

        try:
            while True:
                # Transmit snapshot at ~30 FPS (approx every 33ms)
                snapshot = serial_mgr.get_signal_snapshot(num_points=150)
                snapshot["app_state"] = state_mgr.get_status()
                snapshot["relay_state"] = relay_client.current_state

                # Double blink for Smart Home
                if len(serial_mgr.blink_detector.detected_double_blinks) > 0:
                    snapshot["latest_double_blink"] = serial_mgr.blink_detector.detected_double_blinks[-1]
                else:
                    snapshot["latest_double_blink"] = None

                # Single blink Jump event for Dino Game
                snapshot["latest_game_jump"] = auto_service.latest_game_jump
                snapshot["game_jump_counter"] = auto_service.game_jump_counter

                await websocket.send_text(json.dumps(snapshot))
                await asyncio.sleep(0.033)
        except WebSocketDisconnect:
            logger.info("Frontend WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    return router
