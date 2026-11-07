// Arduino ESP32 Railgun Controller Firmware
// Sends clean instruction events over Serial (115200 baud) for Python mapping.

#define TRIGGER_PIN       4   // Main Trigger (Left Click)
#define SECONDARY_PIN     5   // Secondary Button (Right Click)
#define BTNEXTA_PIN       7  // Extra Button A (btnexA)
#define BTNEXTB_PIN       8  // Extra Button B (btnexB)
#define BTNEXTC_PIN       9  // Extra Button C (btnexC)

struct Button {
  const uint8_t pin;
  const char* name;
  bool lastState;
  unsigned long lastDebounceTime;
};

Button buttons[] = {
  {TRIGGER_PIN,   "TRIGGER",   HIGH, 0},
  {SECONDARY_PIN, "SECONDARY", HIGH, 0},
  {BTNEXTA_PIN,   "btnexA",    HIGH, 0},
  {BTNEXTB_PIN,   "btnexB",    HIGH, 0},
  {BTNEXTC_PIN,   "btnexC",    HIGH, 0}
};

const unsigned long DEBOUNCE_DELAY_MS = 15;

void setup() {
  Serial.begin(115200);

  for (auto &btn : buttons) {
    pinMode(btn.pin, INPUT_PULLUP);
    btn.lastState = digitalRead(btn.pin);
  }

  Serial.println("STATUS:READY");
}

void loop() {
  unsigned long now = millis();

  for (auto &btn : buttons) {
    bool reading = digitalRead(btn.pin);

    if (reading != btn.lastState && (now - btn.lastDebounceTime) > DEBOUNCE_DELAY_MS) {
      btn.lastDebounceTime = now;
      btn.lastState = reading;

      // Active LOW with INPUT_PULLUP: LOW (0) = pressed (DOWN), HIGH (1) = released (UP)
      if (reading == LOW) {
        Serial.print(btn.name);
        Serial.println(":0");
      } else {
        Serial.print(btn.name);
        Serial.println(":1");
      }
    }
  }

  // Small delay to prevent tight loop CPU starvation
  delay(2);
}
