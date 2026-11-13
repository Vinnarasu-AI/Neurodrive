from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.rover.rover_client import RoverClient
from app.core.state import ApplicationStateManager

router = APIRouter(prefix="/api/device/rover", tags=["MOVO Rover"])


class RoverCommandRequest(BaseModel):
    command: str  # FORWARD, BACKWARD, LEFT, RIGHT, STOP


class RoverSpeedRequest(BaseModel):
    speed: int  # 0 - 220


def get_rover_routes(rover_client: RoverClient, state_mgr: ApplicationStateManager) -> APIRouter:
    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        live_status = await rover_client.get_status()
        client_info = rover_client.get_client_status()
        return {
            "client": client_info,
            "hardware": live_status,
            "rover_active": state_mgr.is_rover_active(),
        }

    @router.get("/health")
    async def get_health() -> Dict[str, Any]:
        return await rover_client.check_health()

    @router.post("/command")
    async def manual_command(req: RoverCommandRequest) -> Dict[str, Any]:
        # Manual UI commands allowed for operator testing
        res = await rover_client.send_command(req.command, source="MANUAL_UI")
        return res

    @router.post("/stop")
    async def manual_stop() -> Dict[str, Any]:
        return await rover_client.emergency_stop("Manual UI STOP")

    @router.post("/speed")
    async def manual_speed(req: RoverSpeedRequest) -> Dict[str, Any]:
        return await rover_client.set_speed(req.speed)

    return router

