// Tap-Tempo-Box: Hardware-Test
// Zeigt auf dem Display und im Seriellen Monitor (115200 Baud), ob Taster und
// Drehgeber funktionieren, und schaltet die beiden Klinken-Ausgänge abwechselnd.
// Benötigt die Bibliothek "U8g2" (Arduino IDE: Werkzeuge > Bibliotheken verwalten).

#include <U8x8lib.h>

U8X8_SSD1306_128X64_NONAME_HW_I2C oled(U8X8_PIN_NONE);

const int PIN_TAP = 5;     // TAP-Taster
const int PIN_SS = 4;      // Drucktaster im Drehgeber (Start/Stop)
const int PIN_A = 3;       // Drehgeber A
const int PIN_B = 2;       // Drehgeber B
const int PIN_TIP = 10;    // Optokoppler U2 -> Klinke Tip
const int PIN_RING = 9;    // Optokoppler U3 -> Klinke Ring

volatile int position = 0;

void onTurn() {
  if (digitalRead(PIN_A) == digitalRead(PIN_B)) position++;
  else position--;
}

void setup() {
  pinMode(PIN_TAP, INPUT_PULLUP);
  pinMode(PIN_SS, INPUT_PULLUP);
  pinMode(PIN_A, INPUT_PULLUP);
  pinMode(PIN_B, INPUT_PULLUP);
  pinMode(PIN_TIP, OUTPUT);
  pinMode(PIN_RING, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_A), onTurn, CHANGE);

  Serial.begin(115200);
  oled.begin();
  oled.setFont(u8x8_font_chroma48medium8_r);
  oled.drawString(0, 0, "Tap-Tempo-Box");
  oled.drawString(0, 1, "Hardware-Test");
}

void loop() {
  static unsigned long lastToggle = 0;
  static bool tipClosed = false;
  if (millis() - lastToggle > 1000) {            // jede Sekunde umschalten
    lastToggle = millis();
    tipClosed = !tipClosed;
    digitalWrite(PIN_TIP, tipClosed);
    digitalWrite(PIN_RING, !tipClosed);
  }

  bool tap = digitalRead(PIN_TAP) == LOW;        // gedrückt = LOW
  bool ss = digitalRead(PIN_SS) == LOW;
  noInterrupts();
  int pos = position;
  interrupts();

  char line[17];
  snprintf(line, sizeof line, "TAP:%s SS:%s", tap ? "an " : "aus", ss ? "an " : "aus");
  oled.drawString(0, 3, line);
  snprintf(line, sizeof line, "Dreh: %-8d", pos);
  oled.drawString(0, 4, line);
  snprintf(line, sizeof line, "Tip:%s Ring:%s", tipClosed ? "zu " : "auf", tipClosed ? "auf" : "zu ");
  oled.drawString(0, 6, line);

  Serial.print("TAP=");  Serial.print(tap);
  Serial.print("  StartStop=");  Serial.print(ss);
  Serial.print("  Drehgeber=");  Serial.println(pos);
  delay(50);
}
