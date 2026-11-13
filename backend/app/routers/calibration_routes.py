from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.serial.serial_manager import SerialManager

router = APIRouter(prefix="/api/calibration", tags=["Calibration"])


class StartCalibRequest(BaseModel):
    target: Optional[str] = "smart_home"  # "smart_home" or "game"


def get_calibration_routes(serial_mgr: SerialManager) -> APIRouter:
    @router.get("/status")
    def get_status() -> Dict[str, Any]:
        return serial_mgr.calibration_mgr.get_status()

    @router.post("/start")
    def start_calibration(req: Optional[StartCalibRequest] = None) -> Dict[str, Any]:
        target = req.target if req and req.target else "smart_home"
        serial_mgr.calibration_mgr.start_calibration(target=target)
        app_name = "EOG Dino Game" if target == "game" else "Smart Home Automation"
        return {
            "success": True,
            "target": target,
            "message": f"{app_name} calibration started. Gaze forward at center for 3 seconds.",
            "status": serial_mgr.calibration_mgr.get_status(),
        }

    @router.post("/reset")
    def reset_calibration(req: Optional[StartCalibRequest] = None) -> Dict[str, Any]:
        target = req.target if req and req.target else "smart_home"
        if target in serial_mgr.calibration_mgr.profiles:
            serial_mgr.calibration_mgr.profiles[target].calibrated = False
        serial_mgr.calibration_mgr.stage = "IDLE"
        return {
            "success": True,
            "target": target,
            "message": f"Calibration reset for {target}.",
            "status": serial_mgr.calibration_mgr.get_status(),
        }

    return router
