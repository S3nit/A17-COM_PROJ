import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

FILE_PATH = "data.csv"
FOCUS_WINDOW_HOURS = 12 

def generate_dummy_data(filename):
    np.random.seed(42)
    times = pd.date_range(end=pd.Timestamp.now(), periods=500000, freq='2S')
    
    time_numeric = np.linspace(0, 3, 500000) 
    temp = 25 + 6 * np.sin(time_numeric * 2 * np.pi - (np.pi/2)) + np.random.normal(0, 0.2, 500000)
    humidity = 65 - 20 * np.sin(time_numeric * 2 * np.pi - (np.pi/2)) + np.random.normal(0, 1.0, 500000)
    
    df = pd.DataFrame({'Timestamp': times, 'Temp': temp, 'Humidity': humidity})
    df.to_csv(filename, index=False)

try:
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])
except FileNotFoundError:
    generate_dummy_data(FILE_PATH)
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])

timestamps = df['Timestamp'].to_numpy()
temp = df['Temp'].to_numpy()
humidity = df['Humidity'].to_numpy()

cutoff_time = timestamps[-1] - np.timedelta64(FOCUS_WINDOW_HOURS, 'h')
focus_mask = timestamps >= cutoff_time

focus_times = timestamps[focus_mask]
focus_temp = temp[focus_mask]
focus_hum = humidity[focus_mask]

fig, ax1 = plt.subplots(figsize=(12, 6))

bg_color = '#f9f6fa'
text_color = '#4a4063'
grid_color = '#d8d0df'
temp_color = '#ff7b54'   
hum_color = '#6155a6'    

fig.patch.set_facecolor(bg_color)
ax1.set_facecolor(bg_color)

slice_step = max(1, len(focus_times) // 2000) 

ax2 = ax1.twinx()

line1, = ax1.plot(focus_times[::slice_step], focus_temp[::slice_step], 
                  color=temp_color, alpha=0.85, linewidth=2.5, label="Temperature (°C)")

line2, = ax2.plot(focus_times[::slice_step], focus_hum[::slice_step], 
                  color=hum_color, alpha=0.7, linewidth=2.5, label="Relative Humidity (%)")

ax1.set_title(f"Diurnal Climate Patterns (Last {FOCUS_WINDOW_HOURS} Hours)", 
              fontsize=16, pad=15, color=text_color, fontweight='bold')
ax1.set_xlabel("Time", fontsize=12, color=text_color)
ax1.set_ylabel("Temperature (°C)", fontsize=12, color=temp_color, fontweight='bold')
ax1.tick_params(axis='y', colors=temp_color)
ax1.tick_params(axis='x', colors=text_color)

ax2.set_ylabel("Relative Humidity (%)", fontsize=12, color=hum_color, fontweight='bold')
ax2.tick_params(axis='y', colors=hum_color)
ax2.spines['right'].set_color(hum_color)

ax1.grid(color=grid_color, linestyle='--', alpha=0.7)
ax1.spines['bottom'].set_color('#a29bfe')
ax1.spines['left'].set_color(temp_color)
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)

lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper center", bbox_to_anchor=(0.5, -0.15), 
           ncol=2, facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color)

fig.autofmt_xdate(rotation=45)

plt.tight_layout()
plt.show()
