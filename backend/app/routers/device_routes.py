from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.serial.serial_manager import SerialManager
from app.relay.relay_client import RelayClient
from app.services.automation_service import HomeAutomationService
from app.core.database import db

router = APIRouter(prefix="/api/device", tags=["Device & Relay"])


class PortConfigRequest(BaseModel):
    port: str
    baud_rate: Optional[int] = 230400
    use_mock: Optional[bool] = False


class ThresholdConfigRequest(BaseModel):
    min_gap_ms: Optional[int] = None
    max_gap_ms: Optional[int] = None
    refractory_ms: Optional[int] = None
    blink_peak_threshold: Optional[float] = None


class ModeSwitchRequest(BaseModel):
    use_mock: bool


def get_device_routes(
    serial_mgr: SerialManager,
    relay_client: RelayClient,
    auto_service: HomeAutomationService,
) -> APIRouter:
    @router.get("/status")
    async def get_device_status() -> Dict[str, Any]:
        relay_stat = await relay_client.get_status()
        ports = serial_mgr.list_ports()
        source_label = "SIMULATION" if serial_mgr.use_mock else "REAL HARDWARE"
        return {
            "npg_lite": {
                "connected": serial_mgr.is_connected or serial_mgr.use_mock,
                "is_streaming": serial_mgr.is_streaming,
                "port": serial_mgr.active_port_name,
                "is_mock": serial_mgr.use_mock,
                "source": source_label,
                "board_id": serial_mgr.board_id,
                "baud_rate": serial_mgr.baud_rate,
                "sample_rate_measured": serial_mgr.latest_sample_rate_measured,
                "signal_quality": serial_mgr.latest_quality,
                "available_ports": ports,
                "last_error": serial_mgr.last_connection_error,
            },
            "relay": relay_stat,
        }

    @router.post("/npg/connect")
    def connect_npg(req: PortConfigRequest) -> Dict[str, Any]:
        """Explicitly connects to physical NPG Lite on the selected COM port."""
        success = serial_mgr.connect_real_hardware(req.port, req.baud_rate)
        return {
            "success": success,
            "connected": serial_mgr.is_connected,
            "port": serial_mgr.active_port_name,
            "board_id": serial_mgr.board_id,
            "source": "REAL HARDWARE",
            "message": f"Connected to NPG Lite on {req.port}" if success else f"Connection failed on {req.port}: {serial_mgr.last_connection_error}",
        }

    @router.post("/npg/disconnect")
    def disconnect_npg() -> Dict[str, Any]:
        """Cleanly halts acquisition and closes COM port."""
        serial_mgr.disconnect_hardware()
        return {
            "success": True,
            "connected": False,
            "message": "NPG Lite hardware disconnected.",
        }

    @router.post("/npg/start_acquisition")
    def start_acq() -> Dict[str, Any]:
        """Sends START command to begin streaming."""
        ok = serial_mgr.start_acquisition()
        return {
            "success": ok,
            "is_streaming": serial_mgr.is_streaming,
            "message": "Acquisition started (START sent)",
        }

    @router.post("/npg/stop_acquisition")
    def stop_acq() -> Dict[str, Any]:
        """Sends STOP command to halt streaming."""
        ok = serial_mgr.stop_acquisition()
        return {
            "success": ok,
            "is_streaming": serial_mgr.is_streaming,
            "message": "Acquisition stopped (STOP sent)",
        }

    @router.post("/npg/set_mode")
    def set_mode(req: ModeSwitchRequest) -> Dict[str, Any]:
        """Switches between Simulation and Real Hardware mode."""
        serial_mgr.set_simulation_mode(req.use_mock)
        return {
            "success": True,
            "use_mock": serial_mgr.use_mock,
            "source": "SIMULATION" if serial_mgr.use_mock else "REAL HARDWARE",
            "message": f"Mode switched to {'SIMULATION' if req.use_mock else 'REAL HARDWARE'}",
        }

    @router.post("/npg/configure")
    def configure_serial(req: PortConfigRequest) -> Dict[str, Any]:
        serial_mgr.stop()
        serial_mgr.port = req.port
        if req.baud_rate:
            serial_mgr.baud_rate = req.baud_rate
        if req.use_mock is not None:
            serial_mgr.use_mock = req.use_mock
            serial_mgr.active_port_name = "SIMULATED" if req.use_mock else "DISCONNECTED"
        serial_mgr.start()
        return {
            "success": True,
            "message": f"Serial port updated to {req.port} (mock={req.use_mock})",
        }

    @router.post("/detector/configure")
    def configure_detector(req: ThresholdConfigRequest) -> Dict[str, Any]:
        serial_mgr.blink_detector.set_parameters(
            min_gap_ms=req.min_gap_ms,
            max_gap_ms=req.max_gap_ms,
            refractory_ms=req.refractory_ms,
        )
        if req.blink_peak_threshold is not None:
            serial_mgr.calibration_mgr.blink_peak_threshold = req.blink_peak_threshold
        return {
            "success": True,
            "message": "Detection thresholds updated successfully",
            "thresholds": {
                "min_gap_ms": int(serial_mgr.blink_detector.min_gap_sec * 1000),
                "max_gap_ms": int(serial_mgr.blink_detector.max_gap_sec * 1000),
                "refractory_ms": int(serial_mgr.blink_detector.refractory_sec * 1000),
                "blink_peak_threshold": serial_mgr.calibration_mgr.blink_peak_threshold,
            },
        }

    @router.post("/relay/on")
    async def turn_relay_on() -> Dict[str, Any]:
        return await auto_service.manual_turn_on()

    @router.post("/relay/off")
    async def turn_relay_off() -> Dict[str, Any]:
        return await auto_service.manual_turn_off()

    @router.post("/emergency_stop")
    def emergency_stop() -> Dict[str, Any]:
        return auto_service.emergency_disable()

    @router.get("/logs")
    async def get_event_logs(limit: int = 50) -> Dict[str, Any]:
        events = await db.get_recent_events(limit=limit)
        relay_acts = await db.get_recent_relay_actions(limit=limit)
        return {
            "events": events,
            "relay_actions": relay_acts,
        }

    return router
