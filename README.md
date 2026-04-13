# 🌿 PLANTY — Advanced Plant Analysis System

> **Track, Monitor, and Care for Your Plants with Ease**
> CO1010 Semester Project · Team A17 · University of Peradeniya

---

## 📖 Overview

**PLANTY** is an end-to-end IoT plant monitoring system that pairs an **Arduino-based multi-sensor hardware array** with a **real-time Python/Streamlit dashboard**. The system logs six key environmental variables at high frequency (0.5 Hz), establishes a granular micro-climate baseline around the plant, and uses predictive modelling to tell you exactly when your plant needs water — before it wilts.

Built over one week of continuous data collection, the system logged **~400,000 rows** of sensor data with zero data loss, crashes, or baseline corruption.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────┐      (Serial Communication)       ┌──────────────────────────────────┐
│         Arduino Mega             │ ───────────────────────────────▶          Python Backend            
│                                  │                                   │                                  │
│  • BME280  → Temp/Hum/Pressure   │                                   │  logger.py  → CSV data logger    │
│  • HW-280  → Soil Moisture       │                                   │  analyzer.py → data processing   │
│  • TDS     → Nutrient level      │                                   │  dashboard.py → Streamlit UI     │
│  • LDR     → Light level         │                                   │                                  │
│  • ILI9341 → Onboard TFT display │                                   │  data/plant_data.csv             │
└──────────────────────────────────┘                                   └──────────────────────────────────┘
```

---

## 📊 Monitored Variables

| # | Variable | Sensor | Pin | Optimal Range |
|---|----------|--------|-----|---------------|
| 1 | Temperature | BME280 (I2C) | 0x76/0x77 | 22 – 32 °C |
| 2 | Relative Humidity | BME280 (I2C) | 0x76/0x77 | 60 – 90 % |
| 3 | Atmospheric Pressure | BME280 (I2C) | 0x76/0x77 | 950 – 1050 hPa |
| 4 | Soil Moisture | HW-280 Capacitive | A1 | 350 – 750 (raw) |
| 5 | Total Dissolved Solids (TDS) | TDS Probe | A0 | 600 – 1200 ppm |
| 6 | Light Intensity | LDR | A2 | 400 – 950 (raw) |

---

## ✨ Features

### 🔌 Hardware (Arduino)
- Reads all 6 sensors every **2 seconds** and streams separated data over Serial
- **ILI9341 TFT touchscreen display** — tap to toggle between a live vitals readout and an animated plant face (😁 happy / 😐 okay / 😟 stressed) that reflects real-time plant health
- Colour-coded sensor values on the display: 🟢 optimal / 🟡 warning / 🔴 critical
- Custom software SPI implementation for the XPT2046 touch controller
- Sensor fault detection — flags unplugged or shorted sensors rather than silently logging bad data

### 🖥️ Software (Python + Streamlit)
- **Auto-logging** — `logger.py` reads from the serial port and appends timestamped rows to `data/plant_data.csv`
- **Live Dashboard** — auto-refreshes every 2 seconds with:
  - Animated plant mood indicator (😁 → 😫) driven by multi-variable health evaluation
  - 7 live charts with selectable time spans: Last 10 min / 1 hr / 24 hrs / All Time
  - Real-time metrics with delta indicators for every sensor
- **Derived Insights**:
  - **VPD (Vapor Pressure Deficit)** — calculated live from temp + humidity to assess transpiration stress
  - **Temperature-compensated TDS** — corrects nutrient readings for ambient temperature drift
  - **Watering countdown** — linear regression on the moisture drying curve predicts time until wilting threshold
  - **Barometric storm warning** — alerts when pressure drops faster than –0.15 hPa/sample
- **Live Weather Integration** — pulls current Peradeniya weather via OpenWeatherMap API and factors external rain into watering recommendations
- **Long-Term Analysis tab** — daily min/max temperature swing, nutrient uptake status, and evapotranspiration depletion profile

---

## 📁 Repository Structure

```
A17-COM_PROJ/
│
├── PlantMonitor/
│   ├── main.py                        # Entry point — starts serial logging
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── src/
│   │   ├── logger.py                  # ArduinoDataLogger — serial → CSV
│   │   ├── dashboard.py               # Streamlit live dashboard
│   │   └── analyzer.py                # Data analysis utilities
│   │
│   ├── sensors/
│   │   └── sensors.ino                # Main Arduino firmware (with TFT display)
│   │
│   └── data/
│       ├── data.csv                   # Collected sensor dataset
│       ├── Temperature and Humidity.py       # Diurnal climate pattern chart
│       ├── Hydration and Evaporation.py      # Hydration vs. evapotranspiration chart
│       └── Evapotranspiration Depletion.py   # Depletion profile + wilt forecast
│
└── Test_stage1/
    ├── Final_Sensor_test.ino          # Integration test sketch (JSON output)
    └── HW280_Sensor_Test.ino          # Soil moisture sensor unit test
```

---

## 🛠️ Hardware Requirements

| Component | Purpose |
|-----------|---------|
| Arduino Mega 2560 | Microcontroller |
| BME280 (I2C) | Temperature, Humidity, Pressure |
| HW-280 Capacitive Soil Sensor | Soil Moisture |
| TDS Sensor | Nutrient concentration |
| LDR (photoresistor + resistor) | Light intensity |
| ILI9341 2.4" TFT (SPI) | Onboard display |
| XPT2046 Touch Controller | Touchscreen input |

### Arduino Library Dependencies
- `Adafruit_BME280`
- `Adafruit_GFX`
- `Adafruit_ILI9341`
- `ArduinoJson`
- `BME280I2C`

---

## ⚙️ Setup & Installation

### 1. Flash the Arduino

Open `PlantMonitor/sensors/sensors.ino` in the Arduino IDE and upload to your **Arduino Mega**.

> **Pin Reference:**
> | Pin | Connection |
> |-----|-----------|
> | A0 | TDS Sensor |
> | A1 | Soil Moisture |
> | A2 | LDR |
> | 50 (MISO) | TFT / Touch |
> | 51 (MOSI) | TFT / Touch |
> | 52 (SCK) | TFT / Touch |
> | 8 | TFT DC |
> | 9 | TFT RST |
> | 10 | TFT CS |
> | 11 | Touch CS |
> | 2 | Touch IRQ |

### 2. Install Python Dependencies

```bash
pip install -r PlantMonitor/requirements.txt
```

### 3. Start the Data Logger

Edit `main.py` and set the correct serial port for your system:

```python
# Windows
logger = ArduinoDataLogger(port='COM12')

# macOS / Linux
logger = ArduinoDataLogger(port='/dev/ttyUSB0')
```

Then run:

```bash
cd PlantMonitor
python main.py
```

### 4. Launch the Dashboard

In a separate terminal:

```bash
cd PlantMonitor
streamlit run src/dashboard.py
```

Open your browser at `http://localhost:8501`.

> **Optional:** Add your [OpenWeatherMap API key](https://openweathermap.org/api) to `dashboard.py` to enable the live Peradeniya weather panel.

---

## 📈 Data Visualisations

Run any of the standalone analysis scripts to regenerate the report charts:

```bash
cd PlantMonitor/data
python "Temperature and Humidity.py"
python "Hydration and Evaporation.py"
python "Evapotranspiration Depletion.py"
```

| Script | Output |
|--------|--------|
| `Temperature and Humidity.py` | Dual-axis diurnal temperature vs. humidity cycle |
| `Hydration and Evaporation.py` | Hourly ΔMoisture — watering spikes and drying curves |
| `Evapotranspiration Depletion.py` | Sawtooth moisture profile + linear regression wilt forecast |

---

## 🔬 Key Findings

- **Temperature–Humidity inverse cycle:** 18 °C minimum at 06:00 (humidity 95–98%), 32–33 °C peak at 14:00 (humidity drops ~40%)
- **Strict 72-hour watering cycle:** moisture peaks at 700–800 post-irrigation, asymmetric drying (fast daytime, stable nighttime)
- **TDS micro-fluctuations** detected immediately after watering events (baseline 15–26 ppm)
- **Wilt prediction:** model forecast next wilting point at ~184.9 hours from last observation

---

## 🤖 Reflection on AI Integration

AI tools accelerated code optimisation and data pipeline structuring (NumPy/Matplotlib). However, domain-specific biological assumptions around evapotranspiration and wilting thresholds required rigorous human correction to maintain scientific validity. AI is a strong engineering accelerator — but plant physiology still needs a human in the loop.

---

## 📄 License

Developed for academic purposes as part of the CO1010 module, Faculty of Engineering, University of Peradeniya. Please contact the team before reusing any component.

---

<p align="center">🌱 <i>Keeping plants alive, one data point at a time.</i></p>
