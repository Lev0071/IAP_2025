#include <Wire.h>

// --- Pick your slave address (0x08..0x18) ---
#define SLAVE_ADDRESS 0x08

volatile uint8_t heartbeat = 0;     // increments every 5 s
unsigned long lastBeatMs = 0;

void setup() {
  Wire.begin(SLAVE_ADDRESS);        // Start I²C in slave mode
  Wire.onRequest(onI2CRequest);     // Called when master reads
}

void loop() {
  unsigned long now = millis();

  // Increment heartbeat every 5 seconds
  if (now - lastBeatMs >= 5000UL) {
    lastBeatMs = now;
    heartbeat++;                    // wraps at 255 → 0
  }
}

// Send heartbeat (1 byte) to master
void onI2CRequest() {
  Wire.write(heartbeat);
}
