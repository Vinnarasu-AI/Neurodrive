/*
  NEURODRIVE — ESP32 Wi-Fi Relay Controller Firmware
  Board: ESP32 Dev Module / ESP32-WROOM-32
  
  POLARITY MATCHED TO USER WIRING:
  #define RELAY_PIN 23
  #define RELAY_ON  HIGH   (Light ON when pin is HIGH)
  #define RELAY_OFF LOW    (Light OFF when pin is LOW)
  
  SAFE STARTUP GUARANTEE:
  Relay starts strictly OFF on boot.
  
  Endpoints:
    POST /api/light/on
    POST /api/light/off
    GET  /api/light/status
*/

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ======================== HARDWARE PIN CONFIGURATION ========================
#define RELAY_PIN 23
#define STATUS_LED_PIN 2

// Polarity definition: User specified HIGH = ON, LOW = OFF
#define RELAY_ON  HIGH
#define RELAY_OFF LOW

// ======================== WI-FI & SECURITY CONFIGURATION ========================
const char* WIFI_SSID     = "Vin's F42";
const char* WIFI_PASSWORD = "244466666";

// HTTP Bearer Token (must match RELAY_AUTH_TOKEN in backend/.env)
const char* EXPECTED_BEARER_TOKEN = "neurodrive_secure_token_abc123";

WebServer server(80);

bool isLightOn = false;

void applyRelayState(bool turnOn) {
  isLightOn = turnOn;
  digitalWrite(RELAY_PIN, turnOn ? RELAY_ON : RELAY_OFF);
  digitalWrite(STATUS_LED_PIN, turnOn ? HIGH : LOW);
  
  Serial.print("[RELAY] State applied -> ");
  Serial.println(turnOn ? "LIGHT ON (HIGH)" : "LIGHT OFF (LOW)");
}

bool checkAuthentication() {
  if (!server.hasHeader("Authorization")) {
    return false;
  }
  String authHeader = server.header("Authorization");
  String expected = String("Bearer ") + EXPECTED_BEARER_TOKEN;
  return authHeader.equals(expected);
}

void handleLightOn() {
  if (!checkAuthentication()) {
    server.send(401, "application/json", "{\"error\":\"Unauthorized: Invalid Bearer Token\"}");
    return;
  }
  applyRelayState(true);

  StaticJsonDocument<200> doc;
  doc["success"] = true;
  doc["state"] = "ON";
  doc["relay_pin"] = RELAY_PIN;
  doc["polarity"] = "ACTIVE_HIGH";
  doc["uptime_ms"] = millis();

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

void handleLightOff() {
  if (!checkAuthentication()) {
    server.send(401, "application/json", "{\"error\":\"Unauthorized: Invalid Bearer Token\"}");
    return;
  }
  applyRelayState(false);

  StaticJsonDocument<200> doc;
  doc["success"] = true;
  doc["state"] = "OFF";
  doc["relay_pin"] = RELAY_PIN;
  doc["polarity"] = "ACTIVE_HIGH";
  doc["uptime_ms"] = millis();

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

void handleLightStatus() {
  if (!checkAuthentication()) {
    server.send(401, "application/json", "{\"error\":\"Unauthorized: Invalid Bearer Token\"}");
    return;
  }

  StaticJsonDocument<200> doc;
  doc["state"] = isLightOn ? "ON" : "OFF";
  doc["relay_pin"] = RELAY_PIN;
  doc["polarity"] = "ACTIVE_HIGH";
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_ms"] = millis();

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("\n=== NEURODRIVE ESP32 Wi-Fi Relay Controller ===");

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);

  // SAFE STARTUP GUARANTEE: Force OFF immediately
  applyRelayState(false);

  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[Wi-Fi] Connected!");
    Serial.print("[Wi-Fi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[Wi-Fi] Connection pending...");
  }

  const char *headerkeys[] = {"Authorization"};
  size_t headerkeyssize = sizeof(headerkeys) / sizeof(char*);
  server.collectHeaders(headerkeys, headerkeyssize);

  server.on("/api/light/on", HTTP_POST, handleLightOn);
  server.on("/api/light/off", HTTP_POST, handleLightOff);
  server.on("/api/light/status", HTTP_GET, handleLightStatus);

  server.begin();
  Serial.println("[HTTP] Server ready on port 80");
}

void loop() {
  server.handleClient();

  // Background Wi-Fi reconnection (state is preserved, NEVER toggles during reconnects)
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastReconnect = 0;
    if (millis() - lastReconnect > 10000) {
      lastReconnect = millis();
      WiFi.reconnect();
    }
  }
}
