from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.wheelchair.wheelchair_client import WheelchairClient
from app.core.state import ApplicationStateManager

router = APIRouter(prefix="/api/device/wheelchair", tags=["Wheelchair"])


class WheelchairCommandRequest(BaseModel):
    command: str  # FORWARD, BACKWARD, LEFT, RIGHT, STOP


class WheelchairSpeedRequest(BaseModel):
    speed: int  # 0 - 220


def get_wheelchair_routes(wheelchair_client: WheelchairClient, state_mgr: ApplicationStateManager) -> APIRouter:
    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        live_status = await wheelchair_client.get_status()
        client_info = wheelchair_client.get_client_status()
        return {
            "client": client_info,
            "hardware": live_status,
            "wheelchair_active": state_mgr.is_wheelchair_active(),
        }

    @router.get("/health")
    async def get_health() -> Dict[str, Any]:
        return await wheelchair_client.check_health()

    @router.post("/command")
    async def manual_command(req: WheelchairCommandRequest) -> Dict[str, Any]:
        # Manual UI commands allowed for operator testing
        res = await wheelchair_client.send_command(req.command, source="MANUAL_UI")
        return res

    @router.post("/stop")
    async def manual_stop() -> Dict[str, Any]:
        return await wheelchair_client.emergency_stop("Manual UI STOP")

    @router.post("/speed")
    async def manual_speed(req: WheelchairSpeedRequest) -> Dict[str, Any]:
        return await wheelchair_client.set_speed(req.speed)

    return router

