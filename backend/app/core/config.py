import os
from pydantic_settings import BaseSettings
from typing import Optional

# Determine absolute path to .env file in backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # NPG Lite Serial Settings
    NPG_SERIAL_PORT: str = "AUTO"
    NPG_BAUD_RATE: int = 230400
    NPG_CHANNELS: int = 3
    NPG_SAMPLE_RATE: int = 500
    USE_MOCK_SERIAL: bool = True

    # ESP32 Relay Settings
    RELAY_BASE_URL: str = "http://10.54.195.220"
    RELAY_AUTH_TOKEN: str = "neurodrive_secure_token_abc123"
    RELAY_TIMEOUT_SEC: float = 3.0
    RELAY_POLARITY: str = "ACTIVE_HIGH"
    USE_MOCK_RELAY: bool = False

    # Assistive Wheelchair ESP32 Settings
    WHEELCHAIR_BASE_URL: str = "http://10.54.195.37"
    WHEELCHAIR_AUTH_TOKEN: str = "neurodrive_secure_token_abc123"
    WHEELCHAIR_TIMEOUT_SEC: float = 1.0
    USE_MOCK_WHEELCHAIR: bool = False

    # SQLite database path
    DATABASE_PATH: str = "neurodrive.db"

    # DSP & Blink defaults
    BANDPASS_LOW_HZ: float = 0.5
    BANDPASS_HIGH_HZ: float = 15.0
    NOTCH_FREQ_HZ: float = 50.0
    DOUBLE_BLINK_MIN_GAP_MS: int = 150
    DOUBLE_BLINK_MAX_GAP_MS: int = 850
    REFRACTORY_PERIOD_MS: int = 1200
    PEAK_MIN_AMPLITUDE_UV: float = 250.0

    class Config:
        env_file = ENV_PATH
        extra = "ignore"


settings = Settings()

