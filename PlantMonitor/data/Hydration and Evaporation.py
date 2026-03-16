import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

FILE_PATH = "data.csv"

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

numeric_hours = mdates.date2num(timestamps) * 24
raw_rate = np.gradient(moisture, numeric_hours)

window_size = 450
kernel = np.ones(window_size) / window_size
smoothed_rate = np.convolve(raw_rate, kernel, mode='same')

fig, ax = plt.subplots(figsize=(12, 6))
bg_color, text_color, grid_color = '#f9f6fa', '#4a4063', '#d8d0df'
hydration_color, et_color, zero_line_color = '#a29bfe', '#ff7b54', '#6155a6'

fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

slice_step = max(1, len(timestamps) // 5000) 
plot_times = timestamps[::slice_step]
plot_rates = smoothed_rate[::slice_step]

ax.plot(plot_times, plot_rates, color=zero_line_color, alpha=0.8, linewidth=1.5)

ax.fill_between(plot_times, plot_rates, 0, where=(plot_rates >= 0), 
                color=hydration_color, alpha=0.6, interpolate=True, label="Hydration Rate (+)")

ax.fill_between(plot_times, plot_rates, 0, where=(plot_rates < 0), 
                color=et_color, alpha=0.6, interpolate=True, label="Evapotranspiration Rate (-)")

ax.axhline(0, color=zero_line_color, linestyle='-', linewidth=1.5, alpha=0.5)

ax.set_title("Dynamic Hydration vs. Evapotranspiration Rates", fontsize=16, pad=15, color=text_color, fontweight='bold')
ax.set_xlabel("Time", fontsize=12, color=text_color)
ax.set_ylabel("Rate of Change (Δ Moisture / Hour)", fontsize=12, color=text_color)

ax.grid(color=grid_color, linestyle='--', alpha=0.7)
ax.spines['bottom'].set_color(zero_line_color)
ax.spines['left'].set_color(zero_line_color)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(colors=text_color, which='both')
ax.legend(loc="upper right", facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color)

fig.autofmt_xdate(rotation=45)
plt.tight_layout()
plt.show()
