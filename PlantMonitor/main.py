from src.logger import ArduinoDataLogger
import time


def run():
    # Set 'COM12' to current port before running
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