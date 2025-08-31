#include <Wire.h>

#define SLAVE_ADDRESS 0x08

void onReq() {
  uint8_t v = 0x42;          // constant test byte
  Wire.write(&v, 1);         // always 1 byte
}

void setup() {
  // keep SD deselected just in case
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);

  // (optional) expose weak internal pullups
  pinMode(A4, INPUT_PULLUP);
  pinMode(A5, INPUT_PULLUP);

  Wire.begin(SLAVE_ADDRESS);
  Wire.onRequest(onReq);
}

void loop() {}
