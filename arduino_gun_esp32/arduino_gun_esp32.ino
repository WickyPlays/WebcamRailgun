#include <BleCombo.h>

#define BUTTON_PIN 4
#define RIGHT_BUTTON_PIN 5
#define ENTER_BUTTON_PIN 25
#define SHIFT_BUTTON_PIN 32
#define ESC_BUTTON_PIN 33

bool lastButtonState = HIGH;
bool lastRightButtonState = HIGH;
bool lastEnterButtonState = HIGH;
bool lastShiftButtonState = HIGH;
bool lastEscButtonState = HIGH;

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(RIGHT_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ENTER_BUTTON_PIN, INPUT_PULLUP);
  pinMode(SHIFT_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ESC_BUTTON_PIN, INPUT_PULLUP);

  Keyboard.begin();
  Mouse.begin();
}

void loop() {
  bool buttonState = digitalRead(BUTTON_PIN);
  bool rightButtonState = digitalRead(RIGHT_BUTTON_PIN);
  bool enterButtonState = digitalRead(ENTER_BUTTON_PIN);
  bool shiftButtonState = digitalRead(SHIFT_BUTTON_PIN);
  bool escButtonState = digitalRead(ESC_BUTTON_PIN);

  if (Keyboard.isConnected()) {
    if (buttonState == LOW && lastButtonState == HIGH) {
      Mouse.press(MOUSE_LEFT);
    }

    if (buttonState == HIGH && lastButtonState == LOW) {
      Mouse.release(MOUSE_LEFT);
    }

    if (rightButtonState == LOW && lastRightButtonState == HIGH) {
      Mouse.press(MOUSE_RIGHT);
    }

    if (rightButtonState == HIGH && lastRightButtonState == LOW) {
      Mouse.release(MOUSE_RIGHT);
    }

    if (enterButtonState == LOW && lastEnterButtonState == HIGH) {
      Keyboard.press(KEY_RETURN);
    }

    if (enterButtonState == HIGH && lastEnterButtonState == LOW) {
      Keyboard.release(KEY_RETURN);
    }

    if (shiftButtonState == LOW && lastShiftButtonState == HIGH) {
      Keyboard.press(KEY_LEFT_SHIFT);
    }

    if (shiftButtonState == HIGH && lastShiftButtonState == LOW) {
      Keyboard.release(KEY_LEFT_SHIFT);
    }

    if (escButtonState == LOW && lastEscButtonState == HIGH) {
      Keyboard.press(KEY_ESC);
    }

    if (escButtonState == HIGH && lastEscButtonState == LOW) {
      Keyboard.release(KEY_ESC);
    }
  }

  lastButtonState = buttonState;
  lastRightButtonState = rightButtonState;
  lastEnterButtonState = enterButtonState;
  lastShiftButtonState = shiftButtonState;
  lastEscButtonState = escButtonState;

  delay(10);
}