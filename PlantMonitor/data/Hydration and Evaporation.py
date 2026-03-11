import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- 1. Configuration ---
FILE_PATH = "data.csv"

def generate_dummy_data(filename):
    """Generates a massive dataset with a sawtooth moisture pattern."""
    print("Generating simulated moisture dataset...")
    np.random.seed(42)
    times = pd.date_range(end=pd.Timestamp.now(), periods=500000, freq='2S')
    
    # Create the sawtooth: gradual ET loss, sharp watering spikes
    time_numeric = np.linspace(0, 30, 500000)
    moisture = 700 - (time_numeric % 10) * 40 + np.random.normal(0, 2, 500000)
    
    df = pd.DataFrame({'Timestamp': times, 'Moisture': moisture})
    df.to_csv(filename, index=False)
    print("Dummy data ready!\n")

# --- 2. High-Performance Data Loading ---
try:
    print("Loading millions of rows...")
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])
except FileNotFoundError:
    generate_dummy_data(FILE_PATH)
    df = pd.read_csv(FILE_PATH, parse_dates=['Timestamp'])

print("Calculating derivatives...")

timestamps = df['Timestamp'].to_numpy()
moisture = df['Moisture'].to_numpy()

# --- 3. The Calculus: Rate of Change & Smoothing ---
# Convert datetime to numeric hours so our rate is "Moisture Units per Hour"
numeric_hours = mdates.date2num(timestamps) * 24

# Calculate raw derivative (change in moisture / change in time)
raw_rate = np.gradient(moisture, numeric_hours)

# The raw rate will be incredibly noisy because of sensor fluctuations.
# We apply a fast NumPy convolution (moving average) to smooth it out.
# At 0.5Hz (1 reading per 2 seconds), a 15-minute window is 450 points.
window_size = 450
kernel = np.ones(window_size) / window_size
smoothed_rate = np.convolve(raw_rate, kernel, mode='same')

# --- 4. Visualization ---
fig, ax = plt.subplots(figsize=(12, 6))

# Theme Colors (Light Violet Theme)
bg_color = '#f9f6fa'
text_color = '#4a4063'
grid_color = '#d8d0df'
hydration_color = '#a29bfe'  # Soft Violet/Blue for incoming water
et_color = '#ff7b54'         # Soft Coral for Evapotranspiration loss
zero_line_color = '#6155a6'  # Deep Purple for the baseline

fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)



# Slice the array after the math is done to keep rendering instant
slice_step = max(1, len(timestamps) // 5000) 
plot_times = timestamps[::slice_step]
plot_rates = smoothed_rate[::slice_step]

# Plot the main rate line
ax.plot(plot_times, plot_rates, color=zero_line_color, alpha=0.8, linewidth=1.5)

# Fill ABOVE zero (Hydration Events)
ax.fill_between(plot_times, plot_rates, 0, where=(plot_rates >= 0), 
                color=hydration_color, alpha=0.6, interpolate=True, label="Hydration Rate (+)")

# Fill BELOW zero (Evapotranspiration Phase)
ax.fill_between(plot_times, plot_rates, 0, where=(plot_rates < 0), 
                color=et_color, alpha=0.6, interpolate=True, label="Evapotranspiration Rate (-)")

# Add the Zero Baseline
ax.axhline(0, color=zero_line_color, linestyle='-', linewidth=1.5, alpha=0.5)

# Aesthetics & Theming
ax.set_title("Dynamic Hydration vs. Evapotranspiration Rates", fontsize=16, pad=15, color=text_color, fontweight='bold')
ax.set_xlabel("Time", fontsize=12, color=text_color)
ax.set_ylabel("Rate of Change (Δ Moisture / Hour)", fontsize=12, color=text_color)

# Clean up borders and grid
ax.grid(color=grid_color, linestyle='--', alpha=0.7)
ax.spines['bottom'].set_color(zero_line_color)
ax.spines['left'].set_color(zero_line_color)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(colors=text_color, which='both')

# Legend
ax.legend(loc="upper right", facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color)

fig.autofmt_xdate(rotation=45)

plt.tight_layout()
plt.show()