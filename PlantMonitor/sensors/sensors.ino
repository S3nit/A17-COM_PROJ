#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

Adafruit_BME280 bme; 

class PlantSensor {
  public:
    void begin() {
      Serial.begin(9600);
      Wire.begin(); 
      
      if (!bme.begin(0x76)) { 
        Serial.println("Could not find BME280 sensor at 0x76, trying 0x77...");
        if (!bme.begin(0x77)) {
            Serial.println("Check wiring - sensor not found!");
        }
      }
    }

    void transmitData() {
      float temp = bme.readTemperature();
      float hum = bme.readHumidity();
      float pressure = bme.readPressure() / 100.0F; 
      int moisture = analogRead(A0); 
      int tds = analogRead(A1);      
      int light = analogRead(A2); // Read the new LDR on A2

      // Format: Temp,Hum,Pressure,Moisture,TDS,Light
      Serial.print(temp);     Serial.print(",");
      Serial.print(hum);      Serial.print(",");
      Serial.print(pressure); Serial.print(",");
      Serial.print(moisture); Serial.print(",");
      Serial.print(tds);      Serial.print(",");
      Serial.println(light);
    }
};

PlantSensor myPlant;

void setup() {
  myPlant.begin();
}

void loop() {
  myPlant.transmitData();
  delay(2000); 
}