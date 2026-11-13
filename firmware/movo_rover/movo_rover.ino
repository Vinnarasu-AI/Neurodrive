/*
  ==============================================================================
  NEURODRIVE — MOVO DELIVERY ROVER ESP32 FIRMWARE (SINGLE-FILE ALL-IN-ONE)
  Target Board: ESP32 Dev Module / ESP32-WROOM-32
  ==============================================================================

  HARDWARE PIN ASSIGNMENTS (L298N Dual H-Bridge):
    const int ENA = 13;  // PWM Left/Motor A Enable
    const int IN1 = 12;  // Motor A Direction 1
    const int IN2 = 14;  // Motor A Direction 2
    const int IN3 = 27;  // Motor B Direction 1
    const int IN4 = 26;  // Motor B Direction 2
    const int ENB = 25;  // PWM Right/Motor B Enable

  DIRECTION MATRIX & MOTOR POLARITY:
    FORWARD:  IN1=HIGH, IN2=LOW,  IN3=HIGH, IN4=LOW
    BACKWARD: IN1=LOW,  IN2=HIGH, IN3=LOW,  IN4=HIGH
    LEFT:     IN1=LOW,  IN2=HIGH, IN3=HIGH, IN4=LOW
    RIGHT:    IN1=HIGH, IN2=LOW,  IN3=LOW,  IN4=HIGH
    STOP:     IN1=LOW,  IN2=LOW,  IN3=LOW,  IN4=LOW, ENA=0, ENB=0

  SAFETY GUARANTEES:
    1. Motors start strictly in STOP state prior to pin configuration.
    2. Watchdog Heartbeat: Auto-stops motors if command is not refreshed within 700 ms.
    3. Wi-Fi Disconnect Watchdog: Immediate motor halt if Wi-Fi link drops.
    4. Emergency Stop: Immediate motor halt with highest priority.
    5. Bearer Token Authentication required on all movement and speed endpoints.
*/

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ==============================================================================
// 1. WI-FI & SECURITY CONFIGURATION (EDIT HERE)
// ==============================================================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";         // Enter your 2.4GHz Wi-Fi SSID (e.g. "Vin's F42")
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";     // Enter your Wi-Fi Password (e.g. "244466666")

// HTTP Bearer Authentication Token
const char* ROVER_AUTH_TOKEN = "neurodrive_secure_token_abc123";

// Web Server Port
const int HTTP_PORT = 80;

// ==============================================================================
// 2. SPEED LIMITS & SAFETY TIMEOUTS
// ==============================================================================
const int DEFAULT_MOTOR_SPEED = 140; // Default safe speed (0 - 255)
const int MAX_MOTOR_SPEED     = 220; // Hard maximum speed cap (0 - 255)
const int MIN_MOTOR_SPEED     = 70;  // Minimum PWM threshold for motor start

// Heartbeat watchdog timeout: Stop motors if no command arrives within 700 ms
const unsigned long COMMAND_TIMEOUT_MS = 700;

// ==============================================================================
// 3. HARDWARE PIN ASSIGNMENTS
// ==============================================================================
const int ENA = 13;
const int IN1 = 12;
const int IN2 = 14;

const int IN3 = 27;
const int IN4 = 26;
const int ENB = 25;

const int STATUS_LED = 2; // Onboard LED indicator

// ==============================================================================
// 4. PWM CONFIGURATION (Compatible with ESP32 Arduino Core 2.x and 3.x)
// ==============================================================================
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  #define USE_NEW_LEDC 1
#else
  #define USE_NEW_LEDC 0
  const int PWM_FREQ       = 5000;
  const int PWM_RESOLUTION = 8;
  const int PWM_CH_A       = 0;
  const int PWM_CH_B       = 1;
#endif

// ==============================================================================
// 5. RUNTIME STATE VARIABLES
// ==============================================================================
enum RoverDirection {
  DIR_STOP = 0,
  DIR_FORWARD,
  DIR_BACKWARD,
  DIR_LEFT,
  DIR_RIGHT
};

RoverDirection currentDirection = DIR_STOP;
int currentSpeed = DEFAULT_MOTOR_SPEED;
bool isEmergencyStop = false;
unsigned long lastCommandTimestamp = 0;
unsigned long wifiReconnectTimestamp = 0;

WebServer server(HTTP_PORT);

// ==============================================================================
// 6. MOTOR LOW-LEVEL CONTROL
// ==============================================================================

void setMotorPWM(int speedVal) {
  int safeSpeed = constrain(speedVal, 0, MAX_MOTOR_SPEED);
#if USE_NEW_LEDC
  ledcWrite(ENA, safeSpeed);
  ledcWrite(ENB, safeSpeed);
#else
  ledcWrite(PWM_CH_A, safeSpeed);
  ledcWrite(PWM_CH_B, safeSpeed);
#endif
}

void executeStop() {
  currentDirection = DIR_STOP;
  setMotorPWM(0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void executeForward(int speedVal) {
  currentDirection = DIR_FORWARD;
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  setMotorPWM(speedVal);
}

void executeBackward(int speedVal) {
  currentDirection = DIR_BACKWARD;
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  setMotorPWM(speedVal);
}

void executeLeft(int speedVal) {
  currentDirection = DIR_LEFT;
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  setMotorPWM(speedVal);
}

void executeRight(int speedVal) {
  currentDirection = DIR_RIGHT;
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  setMotorPWM(speedVal);
}

const char* directionToString(RoverDirection dir) {
  switch (dir) {
    case DIR_FORWARD:  return "FORWARD";
    case DIR_BACKWARD: return "BACKWARD";
    case DIR_LEFT:     return "LEFT";
    case DIR_RIGHT:    return "RIGHT";
    case DIR_STOP:
    default:           return "STOP";
  }
}

// ==============================================================================
// 7. AUTHENTICATION HELPER
// ==============================================================================

bool isAuthorized() {
  if (!server.hasHeader("Authorization")) {
    return false;
  }
  String authHeader = server.header("Authorization");
  String expected = String("Bearer ") + ROVER_AUTH_TOKEN;
  return authHeader.equals(expected);
}

void sendUnauthorized() {
  server.send(401, "application/json", "{\"success\":false,\"error\":\"Unauthorized: Invalid Bearer Token\"}");
}

// ==============================================================================
// 8. REST API ENDPOINTS
// ==============================================================================

// GET /api/health
void handleHealth() {
  StaticJsonDocument<256> doc;
  doc["status"] = "healthy";
  doc["device"] = "MOVO_ROVER_ESP32";
  doc["firmware_version"] = "2.0.0-neurodrive";
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["uptime_ms"] = millis();

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

// GET /api/status
void handleStatus() {
  StaticJsonDocument<384> doc;
  doc["command"] = directionToString(currentDirection);
  doc["speed"] = currentSpeed;
  doc["max_speed"] = MAX_MOTOR_SPEED;
  doc["emergency_stop"] = isEmergencyStop;
  doc["timeout_ms"] = COMMAND_TIMEOUT_MS;
  doc["time_since_last_cmd_ms"] = (currentDirection == DIR_STOP) ? 0 : (millis() - lastCommandTimestamp);
  doc["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  doc["ip_address"] = WiFi.localIP().toString();

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

// POST /api/command
void handleCommand() {
  if (!isAuthorized()) {
    sendUnauthorized();
    return;
  }

  if (isEmergencyStop) {
    server.send(423, "application/json", "{\"success\":false,\"error\":\"Emergency Stop active. Call /api/stop to clear.\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> reqDoc;
  DeserializationError err = deserializeJson(reqDoc, body);
  if (err) {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Malformed JSON request body\"}");
    return;
  }

  const char* cmd = reqDoc["command"];
  if (!cmd) {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Missing 'command' field\"}");
    return;
  }

  String cmdStr = String(cmd);
  cmdStr.trim();
  cmdStr.toUpperCase();

  // Reset watchdog heartbeat timer upon receiving valid movement command
  lastCommandTimestamp = millis();

  if (cmdStr == "FORWARD") {
    executeForward(currentSpeed);
  } else if (cmdStr == "BACKWARD") {
    executeBackward(currentSpeed);
  } else if (cmdStr == "LEFT") {
    executeLeft(currentSpeed);
  } else if (cmdStr == "RIGHT") {
    executeRight(currentSpeed);
  } else if (cmdStr == "STOP") {
    executeStop();
  } else {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Invalid command. Allowed: FORWARD, BACKWARD, LEFT, RIGHT, STOP\"}");
    return;
  }

  StaticJsonDocument<256> respDoc;
  respDoc["success"] = true;
  respDoc["executed_command"] = cmdStr;
  respDoc["speed"] = currentSpeed;
  respDoc["timestamp"] = millis();

  String res;
  serializeJson(respDoc, res);
  server.send(200, "application/json", res);
}

// POST /api/stop
void handleStop() {
  if (!isAuthorized()) {
    sendUnauthorized();
    return;
  }

  executeStop();
  isEmergencyStop = false;
  lastCommandTimestamp = millis();

  StaticJsonDocument<200> respDoc;
  respDoc["success"] = true;
  respDoc["command"] = "STOP";
  respDoc["emergency_stop"] = false;
  respDoc["message"] = "Motors halted. Emergency state cleared.";

  String res;
  serializeJson(respDoc, res);
  server.send(200, "application/json", res);
}

// POST /api/speed
void handleSpeed() {
  if (!isAuthorized()) {
    sendUnauthorized();
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> reqDoc;
  DeserializationError err = deserializeJson(reqDoc, body);
  if (err) {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Malformed JSON request body\"}");
    return;
  }

  if (!reqDoc.containsKey("speed")) {
    server.send(400, "application/json", "{\"success\":false,\"error\":\"Missing 'speed' parameter (0-255)\"}");
    return;
  }

  int requestedSpeed = reqDoc["speed"].as<int>();
  if (requestedSpeed < 0 || requestedSpeed > MAX_MOTOR_SPEED) {
    StaticJsonDocument<200> errDoc;
    errDoc["success"] = false;
    errDoc["error"] = "Speed out of range. Maximum allowed is " + String(MAX_MOTOR_SPEED);
    String res;
    serializeJson(errDoc, res);
    server.send(400, "application/json", res);
    return;
  }

  currentSpeed = requestedSpeed;
  if (currentDirection != DIR_STOP) {
    setMotorPWM(currentSpeed);
  }

  StaticJsonDocument<200> respDoc;
  respDoc["success"] = true;
  respDoc["speed"] = currentSpeed;
  respDoc["max_speed"] = MAX_MOTOR_SPEED;

  String res;
  serializeJson(respDoc, res);
  server.send(200, "application/json", res);
}

void handleNotFound() {
  server.send(404, "application/json", "{\"success\":false,\"error\":\"Resource Not Found\"}");
}

// ==============================================================================
// 9. INITIALIZATION
// ==============================================================================

void initMotors() {
  // Set pins LOW before setting pinMode to prevent power-on twitches
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

#if USE_NEW_LEDC
  ledcAttach(ENA, 5000, 8);
  ledcAttach(ENB, 5000, 8);
  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
#else
  ledcSetup(PWM_CH_A, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(PWM_CH_B, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(ENA, PWM_CH_A);
  ledcAttachPin(ENB, PWM_CH_B);
  ledcWrite(PWM_CH_A, 0);
  ledcWrite(PWM_CH_B, 0);
#endif

  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  executeStop();
  Serial.println("[MOTOR] L298N Initialized. Motors strictly STOPPED.");
}

void initWiFi() {
  WiFi.mode(WIFI_STA);
  Serial.println();
  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(250);
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(STATUS_LED, HIGH);
    Serial.println();
    Serial.println("[WIFI] Connected Successfully!");
    Serial.print("[WIFI] IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("[WIFI] Signal Strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    digitalWrite(STATUS_LED, LOW);
    Serial.println();
    Serial.println("[WIFI] Initial Connection Failed. Reconnect task active in loop.");
  }
}

// ==============================================================================
// 10. ARDUINO SETUP & LOOP
// ==============================================================================

void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("==================================================");
  Serial.println("   NEURODRIVE — MOVO DELIVERY ROVER FIRMWARE      ");
  Serial.println("==================================================");

  initMotors();
  initWiFi();

  // Register Web Server Endpoints
  server.on("/api/health", HTTP_GET, handleHealth);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/command", HTTP_POST, handleCommand);
  server.on("/api/stop", HTTP_POST, handleStop);
  server.on("/api/speed", HTTP_POST, handleSpeed);
  server.onNotFound(handleNotFound);

  const char* headerkeys[] = {"Authorization"};
  size_t headerkeyssize = sizeof(headerkeys) / sizeof(char*);
  server.collectHeaders(headerkeys, headerkeyssize);

  server.begin();
  Serial.println("[HTTP] REST API Server running on port 80.");
  Serial.println("[SAFETY] Watchdog Heartbeat active (timeout = 700 ms).");
}

void loop() {
  server.handleClient();

  unsigned long currentMillis = millis();

  // Safety Requirement: Immediate halt on Wi-Fi loss
  if (WiFi.status() != WL_CONNECTED) {
    if (currentDirection != DIR_STOP) {
      Serial.println("[SAFETY] Wi-Fi link dropped! Halting motors immediately.");
      executeStop();
    }
    if (currentMillis - wifiReconnectTimestamp > 5000) {
      wifiReconnectTimestamp = currentMillis;
      WiFi.reconnect();
    }
    return;
  }

  // Safety Requirement: 700 ms Command Watchdog Heartbeat
  if (currentDirection != DIR_STOP) {
    if (currentMillis - lastCommandTimestamp > COMMAND_TIMEOUT_MS) {
      Serial.println("[SAFETY] Heartbeat expired! Stopping motors.");
      executeStop();
    }
  }
}
