#include <Wire.h>

// --- Pick your slave address (0x08..0x18) ---
#define SLAVE_ADDRESS 0x08

const uint8_t LED_PIN  = 13;
const uint8_t BTN_PIN  = 4;

const uint16_t DEBOUNCE_MS = 25;
uint8_t stableState = HIGH;      // INPUT_PULLUP: not pressed = HIGH
uint8_t lastRead    = HIGH;
unsigned long lastEdgeMs = 0;

// Shared status
volatile uint8_t pressedFlag = 0;
volatile uint8_t heartbeat   = 0;

// Simple "register" tracking last command for reads
volatile uint8_t lastCmd = 0xFF;   // 0xFF = "no command" (plain read)

// Heartbeat timer
unsigned long lastBeatMs = 0;

void onI2CRequest();                 // forward declarations (optional)
void onI2CReceive(int count);

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(BTN_PIN, INPUT_PULLUP);

  Wire.begin(SLAVE_ADDRESS);
  Wire.onRequest(onI2CRequest);
  Wire.onReceive(onI2CReceive);
}

void loop() {
  // Debounce button -> pressedFlag (0/1)
  uint8_t reading = digitalRead(BTN_PIN);
  unsigned long now = millis();

  if (reading != lastRead) {
    lastEdgeMs = now;
  }
  if ((now - lastEdgeMs) >= DEBOUNCE_MS && reading != stableState) {
    stableState = reading;
    pressedFlag = (stableState == LOW) ? 1 : 0;
  }
  lastRead = reading;

  // Heartbeat every 5 s
  if (now - lastBeatMs >= 5000UL) {
    lastBeatMs = now;
    heartbeat++;  // wraps at 255
  }
}

// Master read:
// - If lastCmd == 0x00: send [pressedFlag, heartbeat] (2 bytes)
// - If lastCmd == 0x10: send current LED state (1 byte)
// - Else (plain read_byte): send pressedFlag (1 byte)
void onI2CRequest() {
  if (lastCmd == 0x00) {
    uint8_t buf[2] = { pressedFlag, heartbeat };
    Wire.write(buf, 2);
  } else if (lastCmd == 0x10) {
    Wire.write((uint8_t)digitalRead(LED_PIN));
  } else {
    Wire.write(pressedFlag);
  }
  lastCmd = 0xFF;  // reset to "no command"
}

// Master write:
// - 1+ bytes: first byte is command
//   - 0x10 + value: set LED (0=off, nonzero=on)
//   - 0x00: prepare to return 2-byte status on next request
void onI2CReceive(int count) {
  if (count <= 0) return;

  uint8_t cmd = Wire.read();
  lastCmd = cmd;  // remember for onI2CRequest()

  if (cmd == 0x10 && Wire.available()) { // LED control
    uint8_t v = Wire.read();
    digitalWrite(LED_PIN, v ? HIGH : LOW);
  }

  // discard any extra bytes
  while (Wire.available()) (void)Wire.read();
}
