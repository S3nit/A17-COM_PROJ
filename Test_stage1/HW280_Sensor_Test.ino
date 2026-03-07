#include <BME280I2C.h>
#include <Wire.h>

// Initialize the sensor object
// The default is 0x77, so we MUST specify 0x76 here
BME280I2C bme; 

void setup() {
  Serial.begin(9600);
  Wire.begin(); // Required for I2C communication

  // Configure settings (Address, Oversampling, etc.)
  // BME280I2C::I2CAddr_0x76 is the constant for your specific sensor
  while(!bme.begin()) {
    Serial.println("Could not find BME280 sensor!");
    delay(1000);
  }

  // Optional: Change the address if the default begin() fails
  // bme.begin(BME280I2C::I2CAddr_0x76);

  switch(bme.chipModel()) {
     case BME280::ChipModel_BME280:
       Serial.println("Found BME280 sensor! Success.");
       break;
     case BME280::ChipModel_BMP280:
       Serial.println("Found BMP280 sensor! No Humidity available.");
       break;
     default:
       Serial.println("Found UNKNOWN sensor! Check wiring.");
  }
}

void loop() {
  float temp(NAN), hum(NAN), pres(NAN);

  // The library uses Metric units by default
  BME280::TempUnit tempUnit(BME280::TempUnit_Celsius);
  BME280::PresUnit presUnit(BME280::PresUnit_Pa);

  // Read all three parameters at once
  bme.read(pres, temp, hum, tempUnit, presUnit);

  Serial.print("Temp: ");
  Serial.print(temp);
  Serial.print(" °C | ");

  Serial.print("Humidity: ");
  Serial.print(hum);
  Serial.print(" % | ");

  Serial.print("Pressure: ");
  Serial.print(pres / 100); // Convert Pascals to hPa
  Serial.println(" hPa");

  delay(2000);
}
