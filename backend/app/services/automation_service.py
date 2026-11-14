"""
Core Automation & Gesture Routing Service.

Strict gesture routing rules:
IF SMART_HOME_ACTIVE:
    DoubleBlinkDetector -> Relay toggle
    SingleBlinkDetector is completely suppressed / ignored.
IF GAME_ACTIVE:
    SingleBlinkDetector -> Game Jump dispatch
    DoubleBlinkDetector is completely suppressed (NEVER actuates relay).
IF IDLE:
    All gesture events are suppressed and ignored.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from collections import deque

from app.core.state import ApplicationStateManager, AppMode
from app.core.database import db
from app.relay.relay_client import RelayClient
from app.serial.serial_manager import SerialManager

logger = logging.getLogger("neurodrive.service")


class HomeAutomationService:
    def __init__(
        self,
        state_mgr: ApplicationStateManager,
        relay_client: RelayClient,
        serial_mgr: SerialManager,
        wheelchair_client: Optional[Any] = None,
    ):
        self.state_mgr = state_mgr
        self.relay_client = relay_client
        self.serial_mgr = serial_mgr
        self.wheelchair_client = wheelchair_client

        # Bind both callbacks to this routing service
        self.serial_mgr.on_blink_callback = self._handle_double_blink_event
        self.serial_mgr.on_single_blink_callback = self._handle_single_blink_event

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_event_info: Optional[Dict[str, Any]] = None

        # Recent game jumps queue for WebSocket broadcasting
        self.latest_game_jump: Optional[Dict[str, Any]] = None
        self.game_jump_counter: int = 0

    def _handle_wheelchair_event(self, event_data: Dict[str, Any]):
        if not self.state_mgr.is_wheelchair_active() or not self.wheelchair_client:
            return
        cmd = event_data.get("decision", "STOP")
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.wheelchair_client.send_command(cmd, source=event_data.get("source", "WHEELCHAIR_INTENT")),
                self._loop,
            )

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def _handle_double_blink_event(self, event_data: Dict[str, Any]):
        """
        Double-Blink handler: ONLY processes when SMART_HOME_ACTIVE is true.
        Strictly forbidden from running when GAME_ACTIVE or IDLE.
        """
        if not self.state_mgr.is_smart_home_active():
            logger.debug("Double-blink detected, but ignored because Smart Home is not active.")
            return

        self._last_event_info = event_data
        logger.info(f"[SMART HOME] Double Blink valid! (gap: {event_data.get('gap_ms')}ms). Actuating Relay...")

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._execute_gesture_toggle(event_data), self._loop)

    def _handle_single_blink_event(self, event_data: Dict[str, Any]):
        """
        Single-Blink handler: ONLY processes when GAME_ACTIVE is true.
        Strictly forbidden from calling the relay or running during SMART_HOME_ACTIVE or IDLE.
        """
        if not self.state_mgr.is_game_active():
            logger.debug("Single-blink detected, but ignored because Game is not active.")
            return

        self.game_jump_counter += 1
        event_data["jump_id"] = self.game_jump_counter
        self.latest_game_jump = event_data
        logger.info(f"[EOG DINO GAME] Single Blink Jump Triggered! (jump #{self.game_jump_counter}, dur: {event_data.get('duration_ms')}ms)")

        # Log jump event to DB asynchronously
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._log_game_jump(event_data), self._loop)

    async def _log_game_jump(self, event_data: Dict[str, Any]):
        await db.log_event(
            event_type="GAME_JUMP_TRIGGERED",
            source="EOG_CH1_SINGLE_BLINK",
            details=f"jump_id={event_data.get('jump_id')}; amp={event_data.get('amplitude')}; dur={event_data.get('duration_ms')}ms",
            success=True,
        )

    async def _execute_gesture_toggle(self, event_data: Dict[str, Any]):
        # Double check state exclusivity
        if not self.state_mgr.is_smart_home_active():
            return

        # Execute toggle with deduplication
        res = await self.relay_client.toggle(trigger="GESTURE_DOUBLE_BLINK")

        # Persist to database
        await db.log_event(
            event_type="DOUBLE_BLINK_DETECTED",
            source="EOG_CH1",
            details=f"gap={event_data.get('gap_ms')}ms; first_amp={event_data.get('first_amplitude')}; second_amp={event_data.get('second_amplitude')}",
            success=True,
        )

        await db.log_relay_action(
            command=f"TOGGLE -> {res.get('state')}",
            state=res.get("state", "UNKNOWN"),
            trigger="GESTURE_DOUBLE_BLINK",
            latency_ms=res.get("latency_ms", 0.0),
            success=res.get("success", False),
            error_message=res.get("error"),
        )

    async def manual_turn_on(self) -> Dict[str, Any]:
        res = await self.relay_client.turn_on(trigger="MANUAL_UI")
        await db.log_relay_action(
            command="ON",
            state=res.get("state", "ON"),
            trigger="MANUAL_UI",
            latency_ms=res.get("latency_ms", 0.0),
            success=res.get("success", False),
            error_message=res.get("error"),
        )
        return res

    async def manual_turn_off(self) -> Dict[str, Any]:
        res = await self.relay_client.turn_off(trigger="MANUAL_UI")
        await db.log_relay_action(
            command="OFF",
            state=res.get("state", "OFF"),
            trigger="MANUAL_UI",
            latency_ms=res.get("latency_ms", 0.0),
            success=res.get("success", False),
            error_message=res.get("error"),
        )
        return res

    def emergency_disable(self) -> Dict[str, Any]:
        """Instantly disarms all gestures and transitions to IDLE."""
        status = self.state_mgr.deactivate_all("EMERGENCY_STOP triggered by user")
        self.serial_mgr.blink_detector.reset()
        self.serial_mgr.single_blink_detector.reset()
        self.latest_game_jump = None
        logger.warning("Emergency disable invoked: All gesture processing disarmed.")
        return status
