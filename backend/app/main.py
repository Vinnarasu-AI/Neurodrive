import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import db
from app.core.state import ApplicationStateManager
from app.relay.relay_client import RelayClient
from app.wheelchair.wheelchair_client import WheelchairClient
from app.serial.serial_manager import SerialManager
from app.services.automation_service import HomeAutomationService
from app.routers.app_routes import get_app_routes
from app.routers.calibration_routes import get_calibration_routes
from app.routers.device_routes import get_device_routes
from app.routers.wheelchair_routes import get_wheelchair_routes
from app.routers.websocket_routes import get_websocket_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("neurodrive")

# Instantiate singletons
state_mgr = ApplicationStateManager()
relay_client = RelayClient(
    base_url=settings.RELAY_BASE_URL,
    auth_token=settings.RELAY_AUTH_TOKEN,
    timeout_sec=settings.RELAY_TIMEOUT_SEC,
    use_mock=settings.USE_MOCK_RELAY,
)
wheelchair_client = WheelchairClient(
    base_url=settings.WHEELCHAIR_BASE_URL,
    auth_token=settings.WHEELCHAIR_AUTH_TOKEN,
    timeout_sec=settings.WHEELCHAIR_TIMEOUT_SEC,
    use_mock=settings.USE_MOCK_WHEELCHAIR,
)
serial_mgr = SerialManager(
    port=settings.NPG_SERIAL_PORT,
    baud_rate=settings.NPG_BAUD_RATE,
    channels=settings.NPG_CHANNELS,
    sample_rate=settings.NPG_SAMPLE_RATE,
    use_mock=settings.USE_MOCK_SERIAL,
)
auto_service = HomeAutomationService(
    state_mgr=state_mgr,
    relay_client=relay_client,
    serial_mgr=serial_mgr,
    wheelchair_client=wheelchair_client,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing NEURODRIVE Backend...")
    await db.init_db()

    # Pass running event loop to automation service for thread-safe cross-talk
    loop = asyncio.get_running_loop()
    auto_service.set_event_loop(loop)

    # Initial safety guarantee: Ensure relay and wheelchair are stopped on startup
    await relay_client.turn_off(trigger="STARTUP_SAFETY_CHECK")
    await wheelchair_client.emergency_stop(reason="STARTUP_SAFETY_CHECK")
    wheelchair_client.start_heartbeat_loop()

    # Start serial reader background thread
    serial_mgr.start()
    logger.info("NEURODRIVE Backend Ready.")

    yield

    # Shutdown sequence
    logger.info("Shutting down NEURODRIVE Backend...")
    wheelchair_client.stop_heartbeat_loop()
    await wheelchair_client.emergency_stop(reason="SHUTDOWN_CLEANUP")
    serial_mgr.stop()
    await relay_client.turn_off(trigger="SHUTDOWN_CLEANUP")
    logger.info("NEURODRIVE Backend Stopped.")


app = FastAPI(
    title="NEURODRIVE Assistive Technology API",
    description="EOG-based Smart Home Automation Backend for Upside Down Labs NPG Lite",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(get_app_routes(state_mgr, auto_service))
app.include_router(get_calibration_routes(serial_mgr))
app.include_router(get_device_routes(serial_mgr, relay_client, auto_service))
app.include_router(get_wheelchair_routes(wheelchair_client, state_mgr))
app.include_router(get_websocket_routes(serial_mgr, state_mgr, relay_client, auto_service, wheelchair_client))


@app.get("/")
def root():
    return {
        "project": "NEURODRIVE",
        "application": "01 - Smart Home Automation",
        "status": "ONLINE",
        "mode": state_mgr.current_mode.value,
        "npg_lite": "MOCK" if serial_mgr.use_mock else serial_mgr.active_port_name,
        "relay": "MOCK" if relay_client.use_mock else relay_client.base_url,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

