from src.logger import ArduinoDataLogger
import time


def run():
    # Update 'COM3' to your Arduino Mega port
    logger = ArduinoDataLogger(port='COM12')
    print("System Online. Logging to data/plant_data.csv...")

    try:
        while True:
            result = logger.listen()
            if result:
                print(f"Captured: {result}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Logging stopped by user.")


if __name__ == "__main__":
    run()