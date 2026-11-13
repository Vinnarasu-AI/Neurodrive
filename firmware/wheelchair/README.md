# NEURODRIVE — MOVO Delivery Rover ESP32 Firmware

Clean, high-performance ESP32 firmware for the MOVO delivery rover H-bridge motor driver, designed for wireless integration with the NEURODRIVE assistive neural interface.

---

## 1. Hardware Pin Assignments (L298N Dual H-Bridge)

The pin assignments match your existing wiring exactly:

| ESP32 Pin | L298N Terminal | Function | Description |
|:---|:---|:---|:---|
| **GPIO 13** | **ENA** | Motor A Enable (PWM) | Left Motor Speed Control |
| **GPIO 12** | **IN1** | Motor A Direction 1 | Left Motor Direction |
| **GPIO 14** | **IN2** | Motor A Direction 2 | Left Motor Direction |
| **GPIO 27** | **IN3** | Motor B Direction 1 | Right Motor Direction |
| **GPIO 26** | **IN4** | Motor B Direction 2 | Right Motor Direction |
| **GPIO 25** | **ENB** | Motor B Enable (PWM) | Right Motor Speed Control |
| **GND** | **GND** | Common Ground | Must be connected to ESP32 GND and Battery GND |

---

## 2. Motor Polarity & Direction Truth Table

| Movement | IN1 (GPIO 12) | IN2 (GPIO 14) | IN3 (GPIO 27) | IN4 (GPIO 26) | ENA (GPIO 13) | ENB (GPIO 25) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **FORWARD** | `HIGH` | `LOW` | `HIGH` | `LOW` | `PWM` | `PWM` |
| **BACKWARD** | `LOW` | `HIGH` | `LOW` | `HIGH` | `PWM` | `PWM` |
| **LEFT** | `LOW` | `HIGH` | `HIGH` | `LOW` | `PWM` | `PWM` |
| **RIGHT** | `HIGH` | `LOW` | `LOW` | `HIGH` | `PWM` | `PWM` |
| **STOP** | `LOW` | `LOW` | `LOW` | `LOW` | `0` | `0` |

---

## 3. Required Arduino Configuration

### Board Selection
1. Open **Arduino IDE**.
2. Go to **Tools** → **Board** → **esp32** → select **ESP32 Dev Module** (or **DOIT ESP32 DEVKIT V1**).
3. Set upload parameters:
   - **Upload Speed**: `921600` (or `115200` if upload fails)
   - **CPU Frequency**: `240MHz (WiFi/BT)`
   - **Flash Frequency**: `80MHz`
   - **Flash Mode**: `QIO`
   - **Port**: Select the COM port assigned to the rover ESP32.

### Required Libraries
The firmware uses standard ESP32 libraries and `ArduinoJson`:
- **WiFi** (built into ESP32 core)
- **WebServer** (built into ESP32 core)
- **ArduinoJson** (Version 6.x or 7.x)
  - Install via Arduino IDE: **Sketch** → **Include Library** → **Manage Libraries...** → Search `ArduinoJson` by Benoît Blanchon → Click **Install**.

---

## 4. Configuration Instructions (`config.h`)

Open `firmware/movo_rover/config.h` and update the placeholders before uploading:

```cpp
// 1. Wi-Fi Configuration
const char* WIFI_SSID     = "YOUR_WIFI_SSID";      // e.g., "Vin's F42"
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // e.g., "244466666"

// 2. Authentication Token
const char* ROVER_AUTH_TOKEN = "neurodrive_secure_token_abc123";

// 3. Motor Speed & Limits
const int DEFAULT_MOTOR_SPEED = 140; // Default safe speed (0 - 255)
const int MAX_MOTOR_SPEED     = 220; // Hard speed limit (0 - 255)

// 4. Safety Watchdog Timeout
const unsigned long COMMAND_TIMEOUT_MS = 700; // Auto-stop after 700ms without heartbeat
```

---

## 5. Arduino Upload Steps

1. Connect the MOVO Rover ESP32 to your computer using a micro-USB cable.
2. In Arduino IDE, open `firmware/movo_rover/movo_rover.ino`.
3. Verify your Wi-Fi credentials in `config.h`.
4. Click **Upload** (Right Arrow icon).
5. If the upload hangs on `Connecting........_____`, press and hold the **BOOT** button on your ESP32 board until writing begins.
6. Once upload shows `Done uploading`, open the **Serial Monitor** at `115200 baud`.

---

## 6. Serial Monitor Verification

On startup, you will observe the clean boot and connection sequence:

```text
==================================================
   NEURODRIVE — MOVO DELIVERY ROVER FIRMWARE      
==================================================
[MOTOR] L298N Initialized. Motors strictly STOPPED.

[WIFI] Connecting to SSID: Vin's F42
.....
[WIFI] Connected Successfully!
[WIFI] IP Address: 192.168.1.150
[WIFI] Signal Strength (RSSI): -54 dBm
[HTTP] REST API Server started on port 80.
[SAFETY] Watchdog Heartbeat active (timeout = 700 ms).
```

*Note down the assigned IP address (e.g., `192.168.1.150`).*

---

## 7. HTTP API Testing (Curl & PowerShell Examples)

Replace `ROVER_IP` with the IP address printed on your Serial Monitor.

### 1. Health Check (Public)
```bash
curl -X GET http://<ROVER_IP>/api/health
```
**Response:**
```json
{
  "status": "healthy",
  "device": "MOVO_ROVER_ESP32",
  "firmware_version": "2.0.0-neurodrive",
  "wifi_rssi": -54,
  "uptime_ms": 14205
}
```

### 2. Status Query (Public)
```bash
curl -X GET http://<ROVER_IP>/api/status
```
**Response:**
```json
{
  "command": "STOP",
  "speed": 140,
  "max_speed": 220,
  "emergency_stop": false,
  "timeout_ms": 700,
  "time_since_last_cmd_ms": 0,
  "wifi_connected": true,
  "ip_address": "192.168.1.150"
}
```

### 3. Forward Movement (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/command \
  -H "Authorization: Bearer neurodrive_secure_token_abc123" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"FORWARD\"}"
```
**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://<ROVER_IP>/api/command" -Method POST `
  -Headers @{ "Authorization" = "Bearer neurodrive_secure_token_abc123" } `
  -ContentType "application/json" `
  -Body '{"command":"FORWARD"}'
```

### 4. Turn Left (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/command \
  -H "Authorization: Bearer neurodrive_secure_token_abc123" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"LEFT\"}"
```

### 5. Turn Right (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/command \
  -H "Authorization: Bearer neurodrive_secure_token_abc123" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"RIGHT\"}"
```

### 6. Backward Movement (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/command \
  -H "Authorization: Bearer neurodrive_secure_token_abc123" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"BACKWARD\"}"
```

### 7. Emergency STOP (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/stop \
  -H "Authorization: Bearer neurodrive_secure_token_abc123"
```
**Response:**
```json
{
  "success": true,
  "command": "STOP",
  "emergency_stop": false,
  "message": "Motors halted. Emergency state cleared."
}
```

### 8. Set Speed (Authenticated)
```bash
curl -X POST http://<ROVER_IP>/api/speed \
  -H "Authorization: Bearer neurodrive_secure_token_abc123" \
  -H "Content-Type: application/json" \
  -d "{\"speed\": 160}"
```

---

## 8. Safety & Heartbeat Architecture

1. **Power-On Transient Suppression**: All H-bridge direction pins are forced `LOW` and PWM duty cycles are set to `0` immediately at boot before peripheral pin modes are configured.
2. **700 ms Dead-Man Heartbeat**:
   - When a movement command (`FORWARD`, `LEFT`, etc.) is sent, the rover executes it and records `lastCommandTimestamp`.
   - The NEURODRIVE backend must refresh this command every 200–300 ms while the intention/signal is active.
   - If the backend crashes, Wi-Fi drops, or the user releases the gesture, the rover stops automatically within 700 ms.
3. **Wi-Fi Loss Immediate Halt**: If `WiFi.status() != WL_CONNECTED`, motors halt instantly without waiting for timeout.
4. **Speed Clamping**: Requested speeds are clamped between `0` and `MAX_MOTOR_SPEED` (`220`) to prevent motor overheating and brownouts.

---

## 9. Bench Safety Test Procedure (Prior to Ground Operation)

1. **Wheels-Up Test**: Place the rover on a stand or block so all wheels spin freely off the ground.
2. **Power Up**: Power the ESP32 and L298N. Verify wheels remain completely motionless.
3. **Heartbeat Expiry Test**:
   - Send one `FORWARD` command via curl.
   - Observe wheels spin forward and then **automatically stop after exactly 700 ms**.
4. **Emergency Stop Test**:
   - Send continuous `FORWARD` commands.
   - Send `POST /api/stop`. Verify instant motor cessation.
5. **Wi-Fi Disconnect Test**:
   - Send `FORWARD` commands while turning off the router Wi-Fi.
   - Verify motors halt immediately upon connection drop.

