import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

# --- 1. Configuration ---
FILE_PATH = "data.csv"
WILT_THRESHOLD = 300  # The absolute minimum raw moisture value
TREND_WINDOW_HOURS = 12 # How far back to look to calculate the current ET slope

def generate_dummy_data(filename):
    """Generates a quick dummy dataset if you don't have yours handy."""
    print("Generating simulated dataset...")
    np.random.seed(42)
    # Simulate 3 days of data at 0.5 Hz (approx 518,400 points)
    times = pd.date_range(end=pd.Timestamp.now(), periods=500000, freq='2S')
    
    # Create a sawtooth pattern (watering spikes + ET drainage)
    time_numeric = np.linspace(0, 30, 500000)
    moisture = 700 - (time_numeric % 10) * 40 + np.random.normal(0, 2, 500000)
    
    df = pd.DataFrame({'Timestamp': times, 'Moisture': moisture})
    df.to_csv(filename, index=False)
    print("Dummy data ready!\n")

# --- 2. High-Performance Data Loading ---
try:
    # pd.read_csv is incredibly fast for I/O and date parsing
    print("Loading millions of rows...")
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])
except FileNotFoundError:
    generate_dummy_data(FILE_PATH)
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])

print("Crunching the numbers...")

# Cast to NumPy arrays for blazing fast mathematics
timestamps = df['Timestamp'].to_numpy()
moisture = df['Moisture'].to_numpy()

# --- 3. Predictive Math Logic ---
# Find the timestamp for our "trend window" (e.g., last 12 hours)
cutoff_time = timestamps[-1] - np.timedelta64(TREND_WINDOW_HOURS, 'h')

# Create a boolean mask to isolate recent data (NumPy masking is insanely fast)
recent_mask = timestamps >= cutoff_time
recent_times = timestamps[recent_mask]
recent_moisture = moisture[recent_mask]

# Convert datetime64 to matplotlib's numeric format for easy linear regression
numeric_times = mdates.date2num(recent_times)

# Calculate the Evapotranspiration (ET) Slope using a 1st-degree polynomial (y = mx + c)
# This smooths out micro-fluctuations in the sensor
slope, intercept = np.polyfit(numeric_times, recent_moisture, 1)

is_drying = slope < 0
predicted_times = []
predicted_moisture = []
hours_left = 0

if is_drying:
    # Algebra time: When does our line hit the WILT_THRESHOLD?
    # y = mx + c  =>  x = (y - c) / m
    target_numeric_time = (WILT_THRESHOLD - intercept) / slope
    
    # Create points for the prediction dashed line
    predicted_times = [numeric_times[-1], target_numeric_time]
    predicted_moisture = [recent_moisture[-1], WILT_THRESHOLD]
    
    # Calculate exact hours remaining
    time_diff = target_numeric_time - numeric_times[-1]
    hours_left = time_diff * 24 # date2num returns days, so multiply by 24

# --- 4. Visualization ---
# Set up soft light violet theme
fig, ax = plt.subplots(figsize=(12, 6))

# Soft, off-white/lavender background hex colors
bg_color = '#f9f6fa'
text_color = '#4a4063'
grid_color = '#d8d0df'

fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

# To avoid matplotlib crashing on millions of points, we slice the array
slice_step = max(1, len(timestamps) // 10000) 

# Plot the historical Sawtooth Curve (Soft Violet)
ax.plot(timestamps[::slice_step], moisture[::slice_step], 
        color="#a685e2", alpha=0.7, label="Historical Moisture")

# Plot the Recent Trend Line (Regression - Deep Purple)
ax.plot(recent_times[::slice_step], (slope * numeric_times + intercept)[::slice_step], 
        color="#6155a6", linewidth=2.5, label="Current ET Trend")

# Plot the Prediction (Soft Coral/Peach instead of harsh red)
if is_drying:
    # Convert numeric time back to datetime for plotting
    pred_dates = mdates.num2date(predicted_times)
    ax.plot(pred_dates, predicted_moisture, color="#ff7b54", linestyle="--", linewidth=2.5, 
            label=f"Predicted Wilt in {hours_left:.1f} hrs")
    
    # Mark the exact "Death Zone" impact point
    ax.scatter(pred_dates[-1], predicted_moisture[-1], color="#ff7b54", s=100, zorder=5)

# Add a horizontal line for the danger zone (Soft Pink)
ax.axhline(WILT_THRESHOLD, color="#ffb2a6", linestyle=":", linewidth=2, label="Critical Wilt Threshold")

# Aesthetics & Theming
ax.set_title("Evapotranspiration Depletion Profile & Forecast", fontsize=16, pad=15, color=text_color, fontweight='bold')
ax.set_ylabel("Raw Capacitive Moisture", fontsize=12, color=text_color)
ax.set_xlabel("Time", fontsize=12, color=text_color)

# Soft gridlines
ax.grid(color=grid_color, linestyle='--', alpha=0.7)

# Clean up the borders
for spine in ['bottom', 'left']:
    ax.spines[spine].set_color('#a29bfe')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Match tick colors to the text
ax.tick_params(colors=text_color, which='both')

# Style the legend to fit right in
ax.legend(loc="upper right", facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color)

# Format the x-axis to look nice with dates
fig.autofmt_xdate(rotation=45)

plt.tight_layout()
plt.show()