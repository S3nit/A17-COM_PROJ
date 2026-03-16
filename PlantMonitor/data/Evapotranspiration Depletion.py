import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

FILE_PATH = "data.csv"
WILT_THRESHOLD = 300
TREND_WINDOW_HOURS = 12

def generate_dummy_data(filename):
    np.random.seed(42)
    times = pd.date_range(end=pd.Timestamp.now(), periods=500000, freq='2S')
    time_numeric = np.linspace(0, 30, 500000)
    moisture = 700 - (time_numeric % 10) * 40 + np.random.normal(0, 2, 500000)
    
    df = pd.DataFrame({'Timestamp': times, 'Moisture': moisture})
    df.to_csv(filename, index=False)

try:
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])
except FileNotFoundError:
    generate_dummy_data(FILE_PATH)
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])

timestamps = df['Timestamp'].to_numpy()
moisture = df['Moisture'].to_numpy()

cutoff_time = timestamps[-1] - np.timedelta64(TREND_WINDOW_HOURS, 'h')
recent_mask = timestamps >= cutoff_time
recent_times = timestamps[recent_mask]
recent_moisture = moisture[recent_mask]

numeric_times = mdates.date2num(recent_times)
slope, intercept = np.polyfit(numeric_times, recent_moisture, 1)

is_drying = slope < 0
predicted_times = []
predicted_moisture = []
hours_left = 0

if is_drying:
    target_numeric_time = (WILT_THRESHOLD - intercept) / slope
    predicted_times = [numeric_times[-1], target_numeric_time]
    predicted_moisture = [recent_moisture[-1], WILT_THRESHOLD]
    hours_left = (target_numeric_time - numeric_times[-1]) * 24

fig, ax = plt.subplots(figsize=(12, 6))
bg_color, text_color, grid_color = '#f9f6fa', '#4a4063', '#d8d0df'

fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

slice_step = max(1, len(timestamps) // 10000) 

ax.plot(timestamps[::slice_step], moisture[::slice_step], 
        color="#a685e2", alpha=0.7, label="Historical Moisture")

ax.plot(recent_times[::slice_step], (slope * numeric_times + intercept)[::slice_step], 
        color="#6155a6", linewidth=2.5, label="Current ET Trend")

if is_drying:
    pred_dates = mdates.num2date(predicted_times)
    ax.plot(pred_dates, predicted_moisture, color="#ff7b54", linestyle="--", 
            linewidth=2.5, label=f"Predicted Wilt in {hours_left:.1f} hrs")
    ax.scatter(pred_dates[-1], predicted_moisture[-1], color="#ff7b54", s=100, zorder=5)

ax.axhline(WILT_THRESHOLD, color="#ffb2a6", linestyle=":", linewidth=2, label="Threshold")

ax.set_title("Evapotranspiration Depletion Profile", fontsize=16, color=text_color, fontweight='bold')
ax.set_ylabel("Moisture", color=text_color)
ax.set_xlabel("Time", color=text_color)
ax.grid(color=grid_color, linestyle='--', alpha=0.7)
ax.tick_params(colors=text_color)
ax.legend(loc="upper right", facecolor=bg_color)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

fig.autofmt_xdate(rotation=45)
plt.tight_layout()
plt.show()
