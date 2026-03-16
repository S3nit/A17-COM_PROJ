#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// --- TFT Display Pins ---
#define TFT_CS   10
#define TFT_DC   8
#define TFT_RST  9

// --- Touch Screen Pins ---
#define TS_CS    11
#define TS_IRQ   2

// --- Shared Software SPI Pins ---
#define TFT_MOSI 51
#define TFT_SCK  52
#define TFT_MISO 50

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCK, TFT_RST, TFT_MISO);
Adafruit_BME280 bme;

unsigned long lastUpdate = 0;
const long updateInterval = 2000;
unsigned long lastTouchTime = 0;

int lastStressLevel = -1; 
bool showDataMode = false; 
bool forceRedraw = true;   

float temp = 0;
float hum = 0;
int moist = 0;
int tds = 0;
int light = 0;
int stress = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  
  pinMode(TS_CS, OUTPUT);
  digitalWrite(TS_CS, HIGH); 
  pinMode(TS_IRQ, INPUT_PULLUP);

  tft.begin();
  tft.setRotation(0); 
  tft.fillScreen(ILI9341_BLACK);

  if (!bme.begin(0x76) && !bme.begin(0x77)) {
    Serial.println("Warning: BME280 not found!");
  }
}

uint16_t evaluateColor(float val, float optLow, float optHigh, float warnLow, float warnHigh) {
  if (val >= optLow && val <= optHigh) return ILI9341_GREEN;
  if (val >= warnLow && val <= warnHigh) return ILI9341_YELLOW;
  return ILI9341_RED;
}

void drawPlantFace(int stressLevel) {
  int centerX = 120; 
  int centerY = 160; 

  tft.fillRect(40, 80, 160, 160, ILI9341_BLACK);

  if (stressLevel == 0) { 
    tft.drawCircle(centerX, centerY, 70, ILI9341_GREEN);          
    tft.fillCircle(centerX - 25, centerY - 15, 3, ILI9341_GREEN); 
    tft.fillCircle(centerX + 25, centerY - 15, 3, ILI9341_GREEN); 
    
    tft.drawCircle(centerX, centerY + 10, 25, ILI9341_GREEN);
    tft.fillRect(centerX - 30, centerY - 16, 60, 26, ILI9341_BLACK); 
  } 
  else if (stressLevel == 1) {
    tft.drawCircle(centerX, centerY, 70, ILI9341_YELLOW);
    tft.fillCircle(centerX - 25, centerY - 15, 3, ILI9341_YELLOW);
    tft.fillCircle(centerX + 25, centerY - 15, 3, ILI9341_YELLOW);
    
    tft.drawLine(centerX - 15, centerY + 25, centerX + 15, centerY + 25, ILI9341_YELLOW);
  }
  else { 
    tft.drawCircle(centerX, centerY, 70, ILI9341_RED);
    tft.fillCircle(centerX - 25, centerY - 10, 3, ILI9341_RED);
    tft.fillCircle(centerX + 25, centerY - 10, 3, ILI9341_RED);
    
    tft.drawCircle(centerX, centerY + 35, 25, ILI9341_RED);
    tft.fillRect(centerX - 30, centerY + 35, 60, 26, ILI9341_BLACK); 
  }
}

void loop() {
  unsigned long currentMillis = millis();

  int rawX, rawY;
  if (readTouch(rawX, rawY)) {
    if (currentMillis - lastTouchTime > 500) { // 500ms debounce
      lastTouchTime = currentMillis;
      showDataMode = !showDataMode; // Flip the state!
      forceRedraw = true;           // Tell the screen to wipe itself
    }
  }

  if (currentMillis - lastUpdate >= updateInterval || forceRedraw) {
 
    if (currentMillis - lastUpdate >= updateInterval) {
      lastUpdate = currentMillis;

      temp = bme.readTemperature();
      hum = bme.readHumidity();
      moist = analogRead(A0);
      tds = analogRead(A1);
      light = analogRead(A2);

      stress = 0;
      if (temp > 32 || temp < 22) stress++;
      if (moist < 350 || moist > 800) stress++; 

      Serial.print(temp); Serial.print(",");
      Serial.print(hum);  Serial.print(",");
      Serial.print(1013); Serial.print(","); 
      Serial.print(moist); Serial.print(",");
      Serial.print(tds); Serial.print(",");
      Serial.println(light);
    }

    if (forceRedraw) {
      tft.fillScreen(ILI9341_BLACK);
    }

    if (showDataMode) {
      tft.setTextColor(ILI9341_WHITE, ILI9341_BLACK);
      tft.setTextSize(2);
      tft.setCursor(45, 20); tft.print("JASMINE VITALS");
      tft.drawLine(20, 45, 220, 45, ILI9341_DARKCYAN);

      tft.setTextSize(2);
      
      // TEMP (Opt: 22-32, Warn: 18-35)
      tft.setTextColor(ILI9341_WHITE); tft.setCursor(20, 70); tft.print("Temp:");
      tft.setTextColor(evaluateColor(temp, 22, 32, 18, 35), ILI9341_BLACK);
      tft.setCursor(120, 70); tft.print(temp, 1); tft.print(" C  ");

      // HUMIDITY (Opt: 60-90, Warn: 50-95)
      tft.setTextColor(ILI9341_WHITE); tft.setCursor(20, 110); tft.print("Hum:");
      tft.setTextColor(evaluateColor(hum, 60, 90, 50, 95), ILI9341_BLACK);
      tft.setCursor(120, 110); tft.print(hum, 0); tft.print(" %  ");

      // MOISTURE (Opt: 350-750, Warn: 300-800)
      tft.setTextColor(ILI9341_WHITE); tft.setCursor(20, 150); tft.print("Soil:");
      tft.setTextColor(evaluateColor(moist, 350, 750, 300, 800), ILI9341_BLACK);
      tft.setCursor(120, 150); tft.print(moist); tft.print("    ");

      // TDS (Opt: 600-1200, Warn: 500-1400)
      tft.setTextColor(ILI9341_WHITE); tft.setCursor(20, 190); tft.print("TDS:");
      tft.setTextColor(evaluateColor(tds, 600, 1200, 500, 1400), ILI9341_BLACK);
      tft.setCursor(120, 190); tft.print(tds); tft.print(" ppm");

      // LIGHT (Opt: 400-950, Warn: 300-1000)
      tft.setTextColor(ILI9341_WHITE); tft.setCursor(20, 230); tft.print("Light:");
      tft.setTextColor(evaluateColor(light, 400, 950, 300, 1000), ILI9341_BLACK);
      tft.setCursor(120, 230); tft.print(light); tft.print("  ");
      
      tft.setTextSize(1);
      tft.setTextColor(ILI9341_DARKGREY, ILI9341_BLACK);
      tft.setCursor(45, 290); tft.print("Tap screen to hide data");
    } 
  
    else {
      if (forceRedraw || stress != lastStressLevel) {
        drawPlantFace(stress);
        lastStressLevel = stress;
      }
    }
    
    forceRedraw = false; 
  }
}

// ==========================================================
// CUSTOM SOFTWARE SPI TOUCH FUNCTION 
// ==========================================================
bool readTouch(int &x, int &y) {
  if (digitalRead(TS_IRQ) == HIGH) return false; // Pen is up

  digitalWrite(TS_CS, LOW); // Turn ON Touch Chip

  // Read X
  uint8_t cmdX = 0xD0;
  for (int i = 7; i >= 0; i--) { 
    digitalWrite(TFT_MOSI, (cmdX & (1 << i)) ? HIGH : LOW);
    digitalWrite(TFT_SCK, LOW); digitalWrite(TFT_SCK, HIGH);
  }
  digitalWrite(TFT_SCK, LOW);
  uint16_t resultX = 0;
  for (int i = 15; i >= 0; i--) { 
    digitalWrite(TFT_MOSI, LOW); 
    digitalWrite(TFT_SCK, LOW); digitalWrite(TFT_SCK, HIGH);
    if (digitalRead(TFT_MISO)) resultX |= (1 << i);
  }
  digitalWrite(TFT_SCK, LOW);
  x = resultX >> 3;

  // Read Y
  uint8_t cmdY = 0x90;
  for (int i = 7; i >= 0; i--) { 
    digitalWrite(TFT_MOSI, (cmdY & (1 << i)) ? HIGH : LOW);
    digitalWrite(TFT_SCK, LOW); digitalWrite(TFT_SCK, HIGH);
  }
  digitalWrite(TFT_SCK, LOW);
  uint16_t resultY = 0;
  for (int i = 15; i >= 0; i--) { 
    digitalWrite(TFT_MOSI, LOW);
    digitalWrite(TFT_SCK, LOW); digitalWrite(TFT_SCK, HIGH);
    if (digitalRead(TFT_MISO)) resultY |= (1 << i);
  }
  digitalWrite(TFT_SCK, LOW);
  y = resultY >> 3;

  digitalWrite(TS_CS, HIGH); // Turn OFF Touch Chip
  return true;
}
