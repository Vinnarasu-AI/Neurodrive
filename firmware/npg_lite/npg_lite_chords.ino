/*
  NEURODRIVE — Official Protocol NPG Lite Firmware (ESP32-C6)
  
  Channel 1 (A0 / BioAmp Ch1: A0P, A0N, REF)
  Protocol: Official Upside Down Labs Chords Binary Protocol
  
  Communication:
  - Baud: 230400 bps (USB CDC)
  - Handshake:
      Receives "WHORU\n" -> Replies "NPG-LITE-3CH\n"
      Receives "START\n" -> Begins continuous 500 Hz binary streaming
      Receives "STOP\n"  -> Stops streaming
  
  Packet Format (10 Bytes total):
      [0] 0xC7 (SYNC 1)
      [1] 0x7C (SYNC 2)
      [2] Counter (0-255)
      [3] Ch1 High Byte (Big-Endian)
      [4] Ch1 Low Byte
      [5] Ch2 High Byte
      [6] Ch2 Low Byte
      [7] Ch3 High Byte
      [8] Ch3 Low Byte
      [9] 0x01 (END BYTE)
*/

#include <Arduino.h>

// Board Identification matching Chords & Neurodrive parser
#define BOARD_ID "NPG-LITE-3CH"

static constexpr uint32_t SERIAL_BAUD = 230400;
static constexpr uint32_t SAMPLE_RATE_HZ = 500;
static constexpr uint32_t SAMPLE_PERIOD_US = 1000000UL / SAMPLE_RATE_HZ;

// Framing bytes
static const uint8_t SYNC1 = 0xC7;
static const uint8_t SYNC2 = 0x7C;
static const uint8_t END_BYTE = 0x01;

uint8_t packetCounter = 0;
bool isStreaming = false;
uint32_t nextSampleUs = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);
  analogReadResolution(12); // 12-bit ADC (0 - 4095)
  pinMode(A0, INPUT);       // First BioAmp channel (A0P, A0N, REF)

  const uint32_t start = millis();
  while (!Serial && (millis() - start < 1500)) {
    delay(10);
  }
  nextSampleUs = micros();
}

void loop() {
  // Check for incoming commands: WHORU, START, STOP
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "WHORU") {
      Serial.println(BOARD_ID);
    } else if (cmd == "START") {
      isStreaming = true;
      nextSampleUs = micros();
    } else if (cmd == "STOP") {
      isStreaming = false;
    }
  }

  // 500 Hz streaming loop
  if (isStreaming) {
    const uint32_t now = micros();
    if ((int32_t)(now - nextSampleUs) >= 0) {
      nextSampleUs += SAMPLE_PERIOD_US;

      // Read Channel 1 (A0P/A0N/REF on BioAmp)
      uint16_t ch1 = (uint16_t)analogRead(A0);
      uint16_t ch2 = 2048; // Baseline for unused channels
      uint16_t ch3 = 2048;

      // Construct official 10-byte Chords binary packet
      uint8_t packet[10];
      packet[0] = SYNC1;
      packet[1] = SYNC2;
      packet[2] = packetCounter++;
      
      // Channel 1 (Big-endian uint16)
      packet[3] = (uint8_t)((ch1 >> 8) & 0xFF);
      packet[4] = (uint8_t)(ch1 & 0xFF);

      // Channel 2
      packet[5] = (uint8_t)((ch2 >> 8) & 0xFF);
      packet[6] = (uint8_t)(ch2 & 0xFF);

      // Channel 3
      packet[7] = (uint8_t)((ch3 >> 8) & 0xFF);
      packet[8] = (uint8_t)(ch3 & 0xFF);

      packet[9] = END_BYTE;

      Serial.write(packet, 10);

      // Protect against slip if loop fell behind
      if ((int32_t)(micros() - nextSampleUs) > (int32_t)(SAMPLE_PERIOD_US * 4)) {
        nextSampleUs = micros() + SAMPLE_PERIOD_US;
      }
    }
  }
}

