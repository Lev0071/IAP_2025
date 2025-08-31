#include <Arduino.h>

// Buttons top→bottom: D11..D2  (10 buttons)
const uint8_t BTN_PINS[] = {11,10,9,8,7,6,5,4,3,2};
const uint8_t N = sizeof(BTN_PINS)/sizeof(BTN_PINS[0]);

// true  = 10k to +5V, button to GND  → press = LOW
// false = 10k to GND, button to +5V  → press = HIGH
const bool PRESSED_IS_LOW = true;

const uint32_t DEBOUNCE_MS = 25;

bool armed[N];               // ready to report a press?
uint32_t lastEdgeMs[N];      // debounce timer

static inline bool isPressed(uint8_t pin) {
  bool level = digitalRead(pin);
  return PRESSED_IS_LOW ? (level == LOW) : (level == HIGH);
}

void setup() {
  Serial.begin(9600);

  // Configure pins (external resistors -> plain INPUT)
  for (uint8_t i = 0; i < N; i++) pinMode(BTN_PINS[i], INPUT);

  delay(100);                        // let inputs settle after power‑up

  // Sample once and arm only channels that start released
  for (uint8_t i = 0; i < N; i++) {
    armed[i]      = !isPressed(BTN_PINS[i]);  // require release→press
    lastEdgeMs[i] = millis();
  }

  Serial.println("READY");
}

void loop() {
  const uint32_t now = millis();

  for (uint8_t i = 0; i < N; i++) {
    bool pressed = isPressed(BTN_PINS[i]);

    // Debounced PRESS -> print once
    if (pressed && armed[i] && (now - lastEdgeMs[i] >= DEBOUNCE_MS)) {
      Serial.print("BTN:");
      Serial.println(i + 1);
      armed[i] = false;              // wait for release before next report
      lastEdgeMs[i] = now;
    }

    // Debounced RELEASE -> re‑arm
    if (!pressed && !armed[i] && (now - lastEdgeMs[i] >= DEBOUNCE_MS)) {
      armed[i] = true;
      lastEdgeMs[i] = now;
    }
  }
}



// #include <Arduino.h>

// // Buttons top→bottom on your drawing: D11..D2 (10 buttons)
// const uint8_t BTN_PINS[] = {11,10,9,8,7,6,5,4,3,2};
// const uint8_t N = sizeof(BTN_PINS) / sizeof(BTN_PINS[0]);

// // Set this to match your wiring:
// // true  = 10k to +5V and button to GND  → press pulls the pin LOW
// // false = 10k to GND and button to +5V  → press drives the pin HIGH
// const bool PRESSED_IS_LOW = true;

// const uint32_t DEBOUNCE_MS = 25;

// bool armed[N];               // ready to report next press?
// uint32_t lastEdgeMs[N];      // debounce timer

// void setup() {
//   Serial.begin(9600);

//   for (uint8_t i = 0; i < N; i++) {
//     // External resistors are already on the schematic, so use INPUT (no internal pullups).
//     pinMode(BTN_PINS[i], INPUT);
//     armed[i] = true;            // allow an immediate first press
//     lastEdgeMs[i] = 0;
//   }

//   Serial.println("READY");
// }

// void loop() {
//   const uint32_t now = millis();

//   for (uint8_t i = 0; i < N; i++) {
//     bool level   = digitalRead(BTN_PINS[i]);
//     bool pressed = PRESSED_IS_LOW ? (level == LOW) : (level == HIGH);

//     // Debounced PRESS edge → print once
//     if (pressed && armed[i] && (now - lastEdgeMs[i] >= DEBOUNCE_MS)) {
//       Serial.print("BTN:");
//       Serial.println(i + 1);
//       armed[i] = false;                 // wait for release before next report
//       lastEdgeMs[i] = now;
//     }

//     // Debounced RELEASE edge → re‑arm
//     if (!pressed && !armed[i] && (now - lastEdgeMs[i] >= DEBOUNCE_MS)) {
//       armed[i] = true;
//       lastEdgeMs[i] = now;
//     }
//   }
// }


// #include <Arduino.h>

// // Top→bottom: D11..D2  (Buttons 1..10)
// const uint8_t BTN_PINS[] = {11,10,9,8,7,6,5,4,3,2};
// const uint8_t N = sizeof(BTN_PINS) / sizeof(BTN_PINS[0]);

// const uint8_t PRESSED_LEVEL = HIGH;   // external pull-downs -> press drives pin HIGH
// const uint32_t DEBOUNCE_MS = 25;

// bool lastState[N];
// uint32_t lastChangeMs[N];

// void setup() {
//   Serial.begin(9600);
//   for (uint8_t i = 0; i < N; i++) {
//     pinMode(BTN_PINS[i], INPUT);      // using external pull-downs
//     lastState[i] = digitalRead(BTN_PINS[i]);
//     lastChangeMs[i] = 0;
//   }
//   Serial.println("READY");
// }

// void loop() {
//   const uint32_t now = millis();

//   for (uint8_t i = 0; i < N; i++) {
//     bool raw = digitalRead(BTN_PINS[i]);

//     // edge + debounce
//     if (raw != lastState[i] && (now - lastChangeMs[i]) >= DEBOUNCE_MS) {
//       lastChangeMs[i] = now;
//       lastState[i] = raw;

//       if (raw == PRESSED_LEVEL) {     // new PRESS edge → print once
//         Serial.print("BTN:");
//         Serial.println(i + 1);        // 1..10
//       }
//     }
//   }
// }


// #include <Arduino.h>

// // Top→bottom: D10..D2  (Buttons 1..9)
// const uint8_t BTN_PINS[9] = {10,9,8,7,6,5,4,3,2};

// // >>> Change this if your diagnostic shows press = HIGH
// const uint8_t PRESSED_LEVEL = HIGH;   // or LOW
// //const uint8_t PRESSED_LEVEL = LOW;   // or HIGH

// bool lastState[9];
// uint32_t lastChangeMs[9] = {0};
// const uint32_t DEBOUNCE_MS = 25;

// void setup() {
//   Serial.begin(9600);
//   for (int i=0;i<9;i++) {
//     pinMode(BTN_PINS[i], INPUT);     // safe even with external 10k pull-ups
//     lastState[i] = digitalRead(BTN_PINS[i]);
//   }
//   Serial.println("READY");
// }

// void loop() {
//   const uint32_t now = millis();
//   for (int i=0;i<9;i++) {
//     bool raw = digitalRead(BTN_PINS[i]);
//     if (raw != lastState[i] && (now - lastChangeMs[i]) >= DEBOUNCE_MS) {
//       lastChangeMs[i] = now;
//       lastState[i] = raw;
//       if (raw == PRESSED_LEVEL) {           // fire once per new press
//         Serial.print("BTN:");
//         Serial.println(i + 1);
//       }
//     }
//   }
// }

// // ========================== SERIAL BUTTON REPORT ==========================
// // Wiring (top→bottom): D10, D9, D8, D7, D6, D5, D4, D3, D2  => Buttons 1..9
// // Output format (one line per *new* press):  BTN:<1..9>\n  (e.g., BTN:3)
// // Baud must match Proteus Virtual Terminal / COMPIM (9600).

// #include <Arduino.h>

// const uint8_t BTN_PINS[9] = {10, 9, 8, 7, 6, 5, 4, 3, 2};  // D10→D2
// bool lastState[9];                    // last stable read (true=HIGH)
// uint32_t lastChangeMs[9] = {0};       // debounce timers
// const uint32_t DEBOUNCE_MS = 25;      // adjust if needed

// // Optional: brief power‑on test text so you see comms are alive.
// const bool SEND_START_BANNER = true;

// void setup() {
//   Serial.begin(9600);

//   for (int i = 0; i < 9; i++) {
//     pinMode(BTN_PINS[i], INPUT_PULLUP);   // idle HIGH, pressed = LOW
//     lastState[i] = digitalRead(BTN_PINS[i]);
//   }

//   if (SEND_START_BANNER) {
//     Serial.println("READY");  // simple, Pi can ignore or use as handshake
//   }
// }

// void loop() {
//   uint32_t now = millis();

//   for (int i = 0; i < 9; i++) {
//     bool raw = digitalRead(BTN_PINS[i]);

//     // Debounce edge
//     if (raw != lastState[i] && (now - lastChangeMs[i]) >= DEBOUNCE_MS) {
//       lastChangeMs[i] = now;
//       lastState[i] = raw;

//       // Report only on new PRESS (LOW)
//       if (raw == LOW) {
//         // Machine‑friendly line for Raspberry Pi:
//         // e.g., BTN:5<newline>
//         Serial.print("BTN:");
//         Serial.println(i + 1);  // Button 1..9
//       }
//     }
//   }
// }


// /*=============================TERMINAL TEST=============================*\
// /*
//   Serial is used for communication between the Arduino board and a computer or other devices.
//   All Arduino boards have at least one serial port (also known as a UART or USART): Serial.
//   It communicates on digital pins 0 (RX) and 1 (TX) as well as with the computer via USB.

//   Reference:

//   https://www.arduino.cc/en/pmwiki.php?n=Reference/serial
// */

// // the setup routine runs once when you press reset:
// void setup() {
//   // initialize serial communication at 9600 bits per second:
//   Serial.begin(9600);
// }

// // the loop routine runs over and over again forever:
// void loop() {
//   // print out the value you read:
//   Serial.print("Output Test: ");  // print function to print out any character
//   Serial.println("I/O to Terminal works or \"Hello World\"");  // println function create a newline character
//   delay(1000);  // delay in between reads for stability
// }
// /*=============================TERMINAL TEST=============================*\



// // Buttons top→bottom: D10, D9, D8, D7, D6, D5, D4, D3, D2
// const uint8_t btnPins[9] = {10, 9, 8, 7, 6, 5, 4, 3, 2};
// const char*   btnNames[9] = {
//   "Button 1","Button 2","Button 3","Button 4","Button 5",
//   "Button 6","Button 7","Button 8","Button 9"
// };

// bool lastState[9];               // previous stable state (true = HIGH)
// uint32_t lastChangeMs[9] = {0};  // for debounce
// const uint32_t DEBOUNCE_MS = 25;

// void setup() {
//   Serial.begin(9600);            // match Virtual Terminal
//   for (int i = 0; i < 9; i++) {
//     pinMode(btnPins[i], INPUT_PULLUP);   // idle HIGH, press = LOW
//     lastState[i] = digitalRead(btnPins[i]);
//   }
// }

// void loop() {
//   uint32_t now = millis();
//   for (int i = 0; i < 9; i++) {
//     bool raw = digitalRead(btnPins[i]);
//     if (raw != lastState[i] && (now - lastChangeMs[i]) >= DEBOUNCE_MS) {
//       lastChangeMs[i] = now;
//       lastState[i] = raw;

//       if (raw == LOW) {  // new press detected
//         Serial.print(btnNames[i]);
//         Serial.println(" pressed");
//       }
//     }
//   }
// }


// // Button pins
// const int buttonPins[9] = {2,3,4,5,6,7,8,9,10};  

// void setup() {
//   Serial.begin(9600);   // must match Virtual Terminal baud rate
//   for (int i = 0; i < 9; i++) {
//     pinMode(buttonPins[i], INPUT_PULLUP);  // buttons use pull-up logic
//   }
// }

// void loop() {
//   for (int i = 0; i < 9; i++) {
//     if (digitalRead(buttonPins[i]) == LOW) {  // button pressed
//       Serial.print("Button_");
//       Serial.print(i+1);
//       Serial.println(" pressed");
//       delay(200); // debounce
//     }
//   }
// }

// void setup() {
//   // put your setup code here, to run once:

// }

// void loop() {
//   // put your main code here, to run repeatedly:

// }
