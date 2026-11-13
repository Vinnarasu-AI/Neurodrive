# NEURODRIVE — Application 01: Smart Home Automation

**NEURODRIVE** is a modular, high-reliability assistive technology system designed to empower users with limited motor mobility to control appliances using electrooculography (EOG).

This application focuses strictly on **Smart Home Automation** using an **Upside Down Labs NPG Lite (ESP32-C6)** with on-board BioAmp running the official Chords serial firmware, coupled with a separate **ESP32 Wi-Fi Relay Controller**.

---

## 🏗️ Architecture & Features

```
┌────────────────────────────────────────────────────────┐
│                      NEURODRIVE                        │
│          Assistive Technology Web Dashboard            │
│         (React + Vite + Recharts + Lucide)             │
└───────────────▲────────────────────────▲───────────────┘
                │ WebSocket              │ REST API
                │ (Real-time EOG feed)   │ (State / Relay / Config)
┌───────────────▼────────────────────────▼───────────────┐
│                   Python 3.11 Backend                  │
│       FastAPI • NumPy • SciPy • PySerial • aiosqlite   │
│                                                        │
│  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │  Chords Packet Decoder  │  │ DSP Filter Pipeline │  │
│  │  (0xC7 0x7C sync, 500Hz)│  │ (0.5-15Hz Bandpass) │  │
│  └────────────┬────────────┘  └──────────┬──────────┘  │
│               │                          │             │
│  ┌────────────▼────────────┐  ┌──────────▼──────────┐  │
│  │ Signal Quality & SNR    │  │ State Machine       │  │
│  │ (Lead-off, Noise, Rail) │  │ Double-Blink Detect │  │
│  └────────────┬────────────┘  └──────────┬──────────┘  │
│               │                          │             │
│               └─────────────┬────────────┘             │
│                             │                          │
│                ┌────────────▼───────────┐              │
│                │  Relay HTTP Client     │              │
│                │  (Bearer Auth, Dedupe) │              │
│                └────────────┬───────────┘              │
└─────────────────────────────┼──────────────────────────┘
                              │ Authenticated Local HTTP
       USB Virtual COM        ▼
┌──────────────────────┐  ┌─────────────────────────────────┐
│ Upside Down Labs     │  │ Separate ESP32 Wi-Fi Controller │
│ NPG Lite (ESP32-C6)  │  │ Songle SRD-05VDC-SL-C Relay     │
│ Vertical EOG Channel1│  │ Low-Voltage LED / Test Load     │
└──────────────────────┘  └─────────────────────────────────┘
```

### Key Engineering Features
1. **Official Chords Serial Protocol Parser**:
   - Strictly conforms to Upside Down Labs framing (`0xC7, 0x7C` sync header, rolling counter, 16-bit big-endian ADC channels, `0x01` delimiter).
   - Resilient against corrupted bytes, partial buffers, multi-packet bursts, and disconnections.
2. **Deterministic Double-Blink Detector**:
   - Not a simple threshold trigger.
   - Evaluates baseline, peak amplitude, duration (60–400 ms), hysteresis, inter-blink gap window (150–850 ms), and refractory protection (600 ms).
   - Distinct from sustained eye gaze / vertical saccades.
3. **Strict Application Exclusivity**:
   - `IDLE` vs `SMART_HOME_ACTIVE`.
   - `EOG Game Control` and `Wheelchair Control` cards are displayed as "Coming Soon" and strictly disabled.
4. **Resilient Relay Control**:
   - Non-blocking async HTTP client with Bearer Token authentication.
   - Initial boot safe-state enforcement (strictly OFF).
   - Command deduplication prevents redundant relay toggles.
5. **Persistent Audit Trail**:
   - SQLite (`aiosqlite`) tracks all blink events, relay actions, latencies, and errors.
6. **Built-in Mock Generators**:
   - Full end-to-end operation is testable even without physical hardware plugged in.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# (Optional) Review environment configuration
copy .env.example .env

# Run automated unit test suite
python -m pytest tests -v

# Start FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API will be available at `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`).

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install packages
npm install

# Run Vitest test suite
npx vitest run

# Start Vite development server
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## ⚡ ESP32 Relay Firmware Setup
The source code for the separate Wi-Fi relay controller is in [esp32_relay.ino](file:///C:/Users/rvinn/Downloads/Neurodrive/firmware/esp32_relay/esp32_relay.ino).

1. Open `firmware/esp32_relay/esp32_relay.ino` in Arduino IDE.
2. Install `ArduinoJson` from the Library Manager.
3. Update `WIFI_SSID`, `WIFI_PASSWORD`, and `EXPECTED_BEARER_TOKEN` (must match `backend/.env`).
4. Set `RELAY_PIN` (default `GPIO 23`) and verify `RELAY_ACTIVE_LOW`.
5. Upload to your ESP32 board.
6. Check Serial Monitor (115200 baud) for the board's local IP address and enter it in `backend/.env` under `RELAY_BASE_URL`.

---

## 🧪 Testing Results
- **Backend Tests (Pytest)**: 11 / 11 passed
  - Chords framing, single packet, partial chunks, multi-packet bursts, corrupted bytes, and drop tracking.
  - DSP filters stability, signal quality evaluator, double-blink detection happy-path and single-blink rejection.
  - State manager exclusivity and relay client deduplication.
- **Frontend Tests (Vitest)**: 3 / 3 passed
  - Application cards rendering, Coming Soon status lock verification, and state-driven deactivation buttons.
- **Vite Build**: Compiled cleanly without warnings or errors.

---

## 🛡️ Safety Checklist
Refer to [HARDWARE_WIRING_CHECKLIST.md](file:///C:/Users/rvinn/Downloads/Neurodrive/docs/HARDWARE_WIRING_CHECKLIST.md) for full patient safety and electrical isolation instructions.
- Test strictly with low-voltage DC LEDs. No mains voltage.
- Disconnect laptop charger during electrode sessions to eliminate 50Hz ground hum.

