import serial
import csv
import time
import os


class ArduinoDataLogger:
    def __init__(self, port, baudrate=9600, folder="data", filename="plant_data.csv"):
        self.path = os.path.join(folder, filename)
        if not os.path.exists(folder):
            os.makedirs(folder)

        self.serial_port = serial.Serial(port, baudrate, timeout=1)

        # Added 'Light' to the headers
        if not os.path.isfile(self.path):
            with open(self.path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Temp", "Humidity", "Pressure", "Moisture", "TDS", "Light"])

    def listen(self):
        line = self.serial_port.readline().decode('utf-8').strip()
        if line:
            data = line.split(',')
            row = [time.strftime("%Y-%m-%d %H:%M:%S")] + data
            with open(self.path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            return row
        return None