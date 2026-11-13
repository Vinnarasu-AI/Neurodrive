from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.state import ApplicationStateManager

router = APIRouter(prefix="/api/apps", tags=["Applications"])


class ActivationRequest(BaseModel):
    mode: str


def get_app_routes(state_mgr: ApplicationStateManager, auto_service: Optional[Any] = None) -> APIRouter:
    @router.get("/status")
    def get_status() -> Dict[str, Any]:
        return state_mgr.get_status()

    @router.post("/activate")
    async def activate(req: ActivationRequest) -> Dict[str, Any]:
        # Safety clean-up on mode switch: stop other actuators
        if auto_service and hasattr(auto_service, "wheelchair_client") and auto_service.wheelchair_client:
            await auto_service.wheelchair_client.emergency_stop("Application Mode Switch")
        if auto_service and hasattr(auto_service, "relay_client") and auto_service.relay_client:
            await auto_service.relay_client.turn_off("Application Mode Switch")

        ok, msg = state_mgr.request_activation(req.mode)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {
            "success": True,
            "message": msg,
            "state": state_mgr.get_status(),
        }

    @router.post("/deactivate")
    async def deactivate() -> Dict[str, Any]:
        if auto_service and hasattr(auto_service, "wheelchair_client") and auto_service.wheelchair_client:
            await auto_service.wheelchair_client.emergency_stop("Application Deactivated")
        status = state_mgr.deactivate_all("User requested deactivation")
        return {
            "success": True,
            "message": "Application deactivated",
            "state": status,
        }

    return router

