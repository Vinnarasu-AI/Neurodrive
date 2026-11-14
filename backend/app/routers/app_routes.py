from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.core.state import ApplicationStateManager

router = APIRouter(prefix="/api/apps", tags=["Applications"])


class ActivationRequest(BaseModel):
    mode: str


def get_app_routes(state_mgr: ApplicationStateManager) -> APIRouter:
    @router.get("/status")
    def get_status() -> Dict[str, Any]:
        return state_mgr.get_status()

    @router.post("/activate")
    def activate(req: ActivationRequest) -> Dict[str, Any]:
        ok, msg = state_mgr.request_activation(req.mode)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {
            "success": True,
            "message": msg,
            "state": state_mgr.get_status(),
        }

    @router.post("/deactivate")
    def deactivate() -> Dict[str, Any]:
        status = state_mgr.deactivate_all("User requested deactivation")
        return {
            "success": True,
            "message": "Application deactivated",
            "state": status,
        }

    return router

