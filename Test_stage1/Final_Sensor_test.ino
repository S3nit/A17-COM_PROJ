#include <ArduinoJson.h>
#include <Wire.h>
#include <BME280I2C.h>

// --- SENSOR PINS ---
#define TdsSensorPin   A0
#define SoilSensorPin  A1
#define LdrSensorPin   A2

// --- CALIBRATION (Adjust these for your specific sensor) ---
const int AirValue = 600;    // Reading when sensor is DRY
const int WaterValue = 250;  // Reading when sensor is in WATER

BME280I2C bme; 

void setup() {
  Serial.begin(9600);
  Wire.begin();
  
  // Initialize BME280
  bme.begin(); 
  
  pinMode(TdsSensorPin, INPUT);
  pinMode(SoilSensorPin, INPUT);
  pinMode(LdrSensorPin, INPUT);
}

void loop() {
  // 1. Gather BME280 Data (I2C 0x76)
  float temp(NAN), hum(NAN), pres(NAN);
  bool bme_ok = bme.begin(); 
  if (bme_ok) {
    bme.read(pres, temp, hum, BME280::TempUnit_Celsius, BME280::PresUnit_Pa);
  }

  // 2. Gather Analog Data
  int soilRaw = analogRead(SoilSensorPin);
  int tdsRaw  = analogRead(TdsSensorPin);
  int ldrRaw  = analogRead(LdrSensorPin);

  // 3. Advanced Health & Logic Checks
  // If soilRaw > 1000, the pin is floating (unplugged). 
  // If soilRaw < 10, the wire is likely shorted to GND.
  bool soil_ok = (soilRaw > 10 && soilRaw < 1000);
  bool tds_ok  = (tdsRaw > 2);
  bool ldr_ok  = (ldrRaw > 1);

  // 4. Create the JSON Document
  StaticJsonDocument<350> doc;
  doc["sensor_id"] = "Plant_Station_01";

  // --- DATA SECTION ---
  JsonObject data = doc.createNestedObject("data");
  
  // Temperature & Humidity
  if (isnan(temp) || !bme_ok) {
    data["temp"] = "ERR"; 
    data["hum"] = "ERR";
  } else {
    data["temp"] = serialized(String(temp, 2));
    data["hum"] = serialized(String(hum, 1));
    data["pres_hpa"] = serialized(String(pres / 100.0, 2));
  }

  // Soil Moisture Logic (Fixes the 100% unplugged bug)
  if (!soil_ok) {
    data["soil_pct"] = 0; 
  } else {
    int soilPercent = map(soilRaw, AirValue, WaterValue, 0, 100);
    data["soil_pct"] = constrain(soilPercent, 0, 100);
  }

  data["tds_raw"] = tdsRaw;
  data["light_raw"] = ldrRaw;

  // --- STATUS SECTION (Connectivity) ---
  JsonObject status = doc.createNestedObject("status");
  status["bme_connected"]  = bme_ok;
  status["soil_connected"] = soil_ok;
  status["tds_connected"]  = tds_ok;
  status["ldr_connected"]  = ldr_ok;

  // 5. Serialize and Send
  serializeJson(doc, Serial);
  Serial.println(); // Signal the end of the JSON packet

  delay(5000); // 5-second interval
}
