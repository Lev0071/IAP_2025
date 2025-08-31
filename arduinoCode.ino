#include <Wire.h>

#define I2C_ADDR 0x08     // <- set uniquely per board: 0x08, 0x09, 0x0A, ...
#define HELLO     0xFF    // must match Pi

volatile byte lastCommand = 0x00;

void setup() {
  Wire.begin(I2C_ADDR);              // unique 7-bit address
  Wire.onReceive(receiveEvent);      // when Pi writes
  Wire.onRequest(requestEvent);      // when Pi reads
}

void loop() { /* your normal work */ }

void receiveEvent(int) {
  if (Wire.available()) lastCommand = Wire.read();  // store last command from Pi
}

void requestEvent() {
  // respond "alive" only to the HELLO command
  Wire.write(lastCommand == HELLO ? 0x01 : 0x00);
}
