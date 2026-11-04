// Arduino ESP32 Railgun Controller Firmware
// Sends clean instruction events over Serial (115200 baud) for Python mapping.

#define TRIGGER_PIN       4   // Main Trigger (Left Click)
#define SECONDARY_PIN     5   // Secondary Button (Right Click)
#define BTNEXT1_PIN       25  // Extra Button 1 (btnex1)
#define BTNEXT2_PIN       32  // Extra Button 2 (btnex2)
#define BTNEXT3_PIN       33  // Extra Button 3 (btnex3)

struct Button {
  const uint8_t pin;
  const char* name;
  bool lastState;
  unsigned long lastDebounceTime;
};

Button buttons[] = {
  {TRIGGER_PIN,   "TRIGGER",   HIGH, 0},
  {SECONDARY_PIN, "SECONDARY", HIGH, 0},
  {BTNEXT1_PIN,   "btnex1",    HIGH, 0},
  {BTNEXT2_PIN,   "btnex2",    HIGH, 0},
  {BTNEXT3_PIN,   "btnex3",    HIGH, 0}
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

      // Active LOW with INPUT_PULLUP
      if (reading == LOW) {
        Serial.print(btn.name);
        Serial.println(":DOWN");
      } else {
        Serial.print(btn.name);
        Serial.println(":UP");
      }
    }
  }

  // Small delay to prevent tight loop CPU starvation
  delay(2);
}
