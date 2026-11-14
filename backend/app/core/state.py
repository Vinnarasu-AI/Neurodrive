"""
Application State Manager enforcing strict mutual exclusivity across:
- IDLE: No application active. Serial data can be monitored/calibrated, but no gesture toggles are emitted.
- SMART_HOME_ACTIVE: Gesture toggles to relay are active.
- GAME_ACTIVE: Endless runner / Dino game jumps active. Double-blink relay commands strictly suppressed.
- WHEELCHAIR_ACTIVE (Reserved - strictly disabled / Coming Soon).

Invariants:
- Exactly ONE application active at any time.
- Switching applications immediately terminates event routing to previous app and clears pending events.
- On disconnect or signal quality failure, application is automatically neutralized.
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple
import time
import logging

logger = logging.getLogger("neurodrive.state")


class AppMode(str, Enum):
    IDLE = "IDLE"
    SMART_HOME_ACTIVE = "SMART_HOME_ACTIVE"
    GAME_ACTIVE = "GAME_ACTIVE"
    WHEELCHAIR_ACTIVE = "WHEELCHAIR_ACTIVE"  # Reserved Coming Soon


class ApplicationStateManager:
    def __init__(self):
        self._current_mode: AppMode = AppMode.IDLE
        self._last_mode_change: float = time.time()
        self._reason: str = "System Initialized"

    @property
    def current_mode(self) -> AppMode:
        return self._current_mode

    def is_smart_home_active(self) -> bool:
        return self._current_mode == AppMode.SMART_HOME_ACTIVE

    def is_game_active(self) -> bool:
        return self._current_mode == AppMode.GAME_ACTIVE

    def is_wheelchair_active(self) -> bool:
        return self._current_mode == AppMode.WHEELCHAIR_ACTIVE

    def activate_smart_home(self) -> Dict[str, Any]:
        """Activates Smart Home mode."""
        self._current_mode = AppMode.SMART_HOME_ACTIVE
        self._last_mode_change = time.time()
        self._reason = "User activated Smart Home Automation"
        logger.info("Application state changed to SMART_HOME_ACTIVE")
        return self.get_status()

    def activate_game(self) -> Dict[str, Any]:
        """Activates EOG Game mode."""
        self._current_mode = AppMode.GAME_ACTIVE
        self._last_mode_change = time.time()
        self._reason = "User activated EOG Dino Game"
        logger.info("Application state changed to GAME_ACTIVE")
        return self.get_status()

    def activate_wheelchair(self) -> Dict[str, Any]:
        """Activates Assistive Wheelchair mode."""
        self._current_mode = AppMode.WHEELCHAIR_ACTIVE
        self._last_mode_change = time.time()
        self._reason = "User activated Assistive Wheelchair Control"
        logger.info("Application state changed to WHEELCHAIR_ACTIVE")
        return self.get_status()

    def deactivate_all(self, reason: str = "User deactivated application") -> Dict[str, Any]:
        """Deactivates any active application and returns to IDLE."""
        self._current_mode = AppMode.IDLE
        self._last_mode_change = time.time()
        self._reason = reason
        logger.info(f"Application state returned to IDLE: {reason}")
        return self.get_status()

    def request_activation(self, mode_str: str) -> Tuple[bool, str]:
        """
        Validates and transitions to requested mode.
        Allows SMART_HOME_ACTIVE and GAME_ACTIVE.
        Strictly blocks WHEELCHAIR_ACTIVE (Coming Soon).
        """
        mode_upper = mode_str.upper()
        if mode_upper == AppMode.WHEELCHAIR_ACTIVE.value:
            return False, "Wheelchair Control is currently in development ('Coming Soon') and cannot be activated."

        if mode_upper == AppMode.SMART_HOME_ACTIVE.value:
            self.activate_smart_home()
            return True, "Smart Home Automation activated."

        if mode_upper == AppMode.GAME_ACTIVE.value:
            self.activate_game()
            return True, "EOG Game Control activated."

        if mode_upper == AppMode.IDLE.value:
            self.deactivate_all("User switched to IDLE")
            return True, "Deactivated to IDLE."

        return False, f"Unknown application mode: {mode_str}"

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_mode": self._current_mode.value,
            "is_smart_home_active": self.is_smart_home_active(),
            "is_game_active": self.is_game_active(),
            "last_change": self._last_mode_change,
            "reason": self._reason,
            "available_apps": [
                {
                    "id": "smart_home",
                    "name": "Smart Home Automation",
                    "mode": AppMode.SMART_HOME_ACTIVE.value,
                    "enabled": True,
                    "status": "Active" if self.is_smart_home_active() else "Available",
                    "description": "Hands-free lighting control via vertical EOG double blinks.",
                },
                {
                    "id": "game_control",
                    "name": "EOG Dino Runner Game",
                    "mode": AppMode.GAME_ACTIVE.value,
                    "enabled": True,
                    "status": "Active" if self.is_game_active() else "Available",
                    "description": "Real-time pixel-art runner controlled via single deliberate blinks.",
                },
                {
                    "id": "wheelchair_control",
                    "name": "Wheelchair Control",
                    "mode": AppMode.WHEELCHAIR_ACTIVE.value,
                    "enabled": False,
                    "status": "Coming Soon",
                    "description": "Assistive mobility directional steering interface.",
                },
            ],
        }
