import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger("neurodrive.rover")


class RoverClient:
    """
    HTTP REST Client for MOVO Delivery Rover ESP32.
    Matches exact firmware endpoints in movo_rover.ino:
      GET  /api/health
      GET  /api/status
      POST /api/command  {"command": "FORWARD"|"BACKWARD"|"LEFT"|"RIGHT"|"STOP"}
      POST /api/stop     (Emergency / immediate halt)
      POST /api/speed    {"speed": int}
    """

    def __init__(
        self,
        base_url: str = "http://10.54.195.37",
        auth_token: str = "neurodrive_secure_token_abc123",
        timeout_sec: float = 0.5,
        use_mock: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout_sec = timeout_sec
        self.use_mock = use_mock

        self.current_command: str = "STOP"
        self.current_speed: int = 140
        self.is_connected: bool = False
        self.last_health_check: float = 0.0
        self.last_response_time_ms: float = 0.0
        self.last_error: Optional[str] = None

        # Watchdog heartbeat background task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._target_command: str = "STOP"
        self._command_source: str = "NONE"  # "EEG", "EMG", "MANUAL", "SAFETY"
        self._last_command_time: float = 0.0
        self._lock = asyncio.Lock()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    async def check_health(self) -> Dict[str, Any]:
        """Queries /api/health to verify connectivity without changing rover state."""
        if self.use_mock:
            self.is_connected = True
            return {
                "success": True,
                "status": "healthy",
                "device": "MOCK_MOVO_ROVER",
                "uptime_ms": int(time.time() * 1000) % 1000000,
            }

        url = f"{self.base_url}/api/health"
        start_t = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    self.is_connected = (resp.status == 200)
                    self.last_response_time_ms = round((time.time() - start_t) * 1000, 1)
                    self.last_health_check = time.time()
                    self.last_error = None
                    return data
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            return {"success": False, "error": str(e)}

    async def get_status(self) -> Dict[str, Any]:
        """Queries /api/status on the rover."""
        if self.use_mock:
            return {
                "success": True,
                "command": self.current_command,
                "speed": self.current_speed,
                "max_speed": 220,
                "emergency_stop": False,
                "timeout_ms": 700,
                "wifi_connected": True,
                "ip_address": "127.0.0.1",
            }

        url = f"{self.base_url}/api/status"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        self.is_connected = True
                        data = await resp.json()
                        return data
                    self.is_connected = False
                    return {"success": False, "status": resp.status}
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            return {"success": False, "error": str(e)}

    async def send_command(self, command: str, source: str = "MANUAL") -> Dict[str, Any]:
        """
        Sends motion command: FORWARD, BACKWARD, LEFT, RIGHT, or STOP.
        Updates internal target and refreshes last_command_time.
        """
        cmd_upper = command.strip().upper()
        if cmd_upper not in ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"]:
            return {"success": False, "error": f"Invalid rover command: {command}"}

        async with self._lock:
            self._target_command = cmd_upper
            self._command_source = source
            self._last_command_time = time.time()

        return await self._dispatch_command(cmd_upper)

    async def _dispatch_command(self, command: str) -> Dict[str, Any]:
        self.current_command = command

        if self.use_mock:
            return {
                "success": True,
                "executed_command": command,
                "speed": self.current_speed,
                "timestamp": int(time.time() * 1000),
            }

        url = f"{self.base_url}/api/command"
        payload = {"command": command}
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self._headers(), json=payload) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        self.is_connected = True
                        self.last_error = None
                        return data
                    else:
                        self.last_error = f"HTTP {resp.status}: {data}"
                        return {"success": False, "error": self.last_error}
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            logger.warning(f"[ROVER] Failed to dispatch {command} to {url}: {e}")
            return {"success": False, "error": str(e)}

    async def emergency_stop(self, reason: str = "Manual Emergency STOP") -> Dict[str, Any]:
        """
        Immediately halts both motors by calling POST /api/stop.
        Clears target command to STOP.
        """
        async with self._lock:
            self._target_command = "STOP"
            self._command_source = "EMERGENCY_STOP"
            self.current_command = "STOP"

        if self.use_mock:
            return {"success": True, "command": "STOP", "message": f"MOCK STOP: {reason}"}

        url = f"{self.base_url}/api/stop"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self._headers()) as resp:
                    data = await resp.json()
                    self.last_error = None
                    return data
        except Exception as e:
            self.last_error = str(e)
            return {"success": False, "error": str(e)}

    async def set_speed(self, speed: int) -> Dict[str, Any]:
        """Sets motor PWM speed (0 - 220) via POST /api/speed."""
        speed_clamped = max(0, min(220, int(speed)))
        self.current_speed = speed_clamped

        if self.use_mock:
            return {"success": True, "speed": speed_clamped}

        url = f"{self.base_url}/api/speed"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self._headers(), json={"speed": speed_clamped}) as resp:
                    return await resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Heartbeat Watchdog Integration (Every 200–250 ms while moving)
    def start_heartbeat_loop(self):
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_worker())
            logger.info("[ROVER] Heartbeat watchdog task started (200ms period)")

    def stop_heartbeat_loop(self):
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            logger.info("[ROVER] Heartbeat watchdog task stopped")

    async def _heartbeat_worker(self):
        while True:
            try:
                await asyncio.sleep(0.20)  # 200 ms interval (well inside 700ms ESP32 timeout)
                if self._target_command != "STOP":
                    # Refresh active movement command
                    await self._dispatch_command(self._target_command)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ROVER] Heartbeat worker error: {e}")

    def get_client_status(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected,
            "current_command": self.current_command,
            "target_command": self._target_command,
            "command_source": self._command_source,
            "speed": self.current_speed,
            "base_url": self.base_url,
            "is_mock": self.use_mock,
            "last_error": self.last_error,
            "last_response_time_ms": self.last_response_time_ms,
        }

