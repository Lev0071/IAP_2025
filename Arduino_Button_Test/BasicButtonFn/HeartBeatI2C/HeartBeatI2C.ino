#include <Wire.h>

// --- Pick your slave address (0x08..0x18) ---
 #define SLAVE_ADDRESS 0x08
// #define SLAVE_ADDRESS 0x09
// #define SLAVE_ADDRESS 0x0A	
// #define SLAVE_ADDRESS 0x0B	
// #define SLAVE_ADDRESS 0x0C	
// #define SLAVE_ADDRESS 0x0D	
// #define SLAVE_ADDRESS 0x0E	
// #define SLAVE_ADDRESS 0x0F	
// #define SLAVE_ADDRESS 0x10	
// #define SLAVE_ADDRESS 0x11	
// #define SLAVE_ADDRESS 0x12	
// #define SLAVE_ADDRESS 0x13	
// #define SLAVE_ADDRESS 0x14	
// #define SLAVE_ADDRESS 0x15	
// #define SLAVE_ADDRESS 0x16	
// #define SLAVE_ADDRESS 0x17	
// #define SLAVE_ADDRESS 0x18

const uint8_t LED_PIN  = 13;
const uint8_t BTN_PIN  = 4;

const uint16_t DEBOUNCE_MS = 25;
uint8_t stableState = HIGH;      // INPUT_PULLUP: not pressed = HIGH
uint8_t lastRead    = HIGH;
unsigned long lastEdgeMs = 0;

// Shared status
volatile uint8_t pressedFlag = 0;
volatile uint8_t heartbeat   = 0;
volatile uint8_t lastCmd     = 0xFF;  // remembers last master command

// Heartbeat timer
unsigned long lastBeatMs = 0;

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

// Master read
void onI2CRequest() {
  if (lastCmd == 0x00) {
    // Send 2-byte status (button + heartbeat)
    uint8_t buf[2] = { pressedFlag, heartbeat };
    Wire.write(buf, 2);
  } else {
    // Default: just pressedFlag (1 byte)
    Wire.write(pressedFlag);
  }
  lastCmd = 0xFF;
}

// Master write
void onI2CReceive(int count) {
  if (count <= 0) return;

  uint8_t cmd = Wire.read();
  lastCmd = cmd;

  if (cmd == 0x10 && Wire.available()) {
    // LED control
    uint8_t v = Wire.read();
    digitalWrite(LED_PIN, v ? HIGH : LOW);
  }

  // Discard extras
  while (Wire.available()) (void)Wire.read();
}
