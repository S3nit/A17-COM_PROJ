import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import requests
from datetime import timedelta

# --- Configuration & UI Setup ---
st.set_page_config(page_title="Advanced Plant Monitor", layout="wide", page_icon="🌿")
DATA_PATH = "data/plant_data.csv"

OWM_API_KEY = "6c1dcad79d77f2bb646d523712c307d3"

plt.style.use('dark_background')

st.markdown("""
    <style>
    .metric-card { background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-bottom: 10px; }

    /* --- NEW: UNIFIED BOX STYLING FOR PERFECT HEIGHT ALIGNMENT --- */
    .dashboard-box {
        border-radius: 20px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 400px; /* Forces both boxes to be exactly the same height */
        padding: 20px;
        box-sizing: border-box;
    }

    .mood-box { border: 1px solid #444; transition: background 1.5s ease-in-out; }
    .weather-box { background-color: #1a1a24; border: 1px solid #333; }

    .bg-happy { background: radial-gradient(circle, rgba(0,255,0,0.2) 0%, rgba(10,10,15,1) 70%); }
    .bg-okay { background: radial-gradient(circle, rgba(100,100,100,0.1) 0%, rgba(10,10,15,1) 70%); }
    .bg-stressed { background: radial-gradient(circle, rgba(255,102,0,0.15) 0%, rgba(10,10,15,1) 70%); animation: stress-glow 2s infinite alternate; }
    .bg-critical { background: radial-gradient(circle, rgba(204,0,0,0.25) 0%, rgba(10,10,15,1) 70%); animation: panic-glow 0.8s infinite; }

    .mood-title { font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #ffffff; text-shadow: 0 2px 4px rgba(0,0,0,0.5);}
    .tip-text { color: #00ffcc; font-size: 15px; margin-top: 8px; font-weight: 500; line-height: 1.3; }

    @keyframes floating { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
    @keyframes nervous-shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px) rotate(-5deg); } 75% { transform: translateX(5px) rotate(5deg); } }
    @keyframes frantic-panic { 0%, 100% { transform: translate(0, 0); } 25% { transform: translate(-4px, 4px); } 50% { transform: translate(4px, -4px); } 75% { transform: translate(-4px, -4px); } }
    @keyframes stress-glow { 0% { box-shadow: 0 0 10px rgba(255,102,0,0.1); } 100% { box-shadow: 0 0 20px rgba(255,102,0,0.3); } }
    @keyframes panic-glow { 0%, 100% { background: radial-gradient(circle, rgba(204,0,0,0.25) 0%, rgba(10,10,15,1) 70%); } 50% { background: radial-gradient(circle, rgba(204,0,0,0.4) 0%, rgba(10,10,15,1) 70%); } }

    .face-happy { font-size: 90px; line-height: 1; display: inline-block; animation: floating 3s ease-in-out infinite; }
    .face-okay { font-size: 90px; line-height: 1; display: inline-block; }
    .face-stressed { font-size: 90px; line-height: 1; display: inline-block; animation: nervous-shake 0.4s infinite; }
    .face-critical { font-size: 90px; line-height: 1; display: inline-block; animation: frantic-panic 0.1s infinite; filter: drop-shadow(0 0 15px rgba(255,0,0,0.8)); }
    </style>
""", unsafe_allow_html=True)


# --- Robust API Fetching ---
@st.cache_data(ttl=900)
def fetch_local_weather(api_key):
    if api_key == not api_key:
        return None
  
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Kurunegala,lk&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        return None


# --- Mathematical Helper Functions ---
def calc_vpd(temp, hum):
    svp = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
    avp = svp * (hum / 100.0)
    return svp - avp


def safe_gradient(series):
    if len(series) < 2:
        return 0.0
    return np.gradient(series).mean()


def get_status_indicator(value, min_val, max_val):
    if value < min_val: return "🔵 Low"
    if value > max_val: return "🔴 High"
    return "🟢 Opt"


def evaluate_plant_health(latest, ranges, weather, pressure_trend):
    stress = 0;
    issues = [];
    tips = []

    if latest['Temp'] < ranges['Temp'][0]:
        stress += 1;
        issues.append("Temp Low 🥶");
        tips.append("💡 Tip: Relocate away from cold drafts.")
    elif latest['Temp'] > ranges['Temp'][1]:
        stress += 1;
        issues.append("Temp High 🥵");
        tips.append("💡 Tip: Increase air circulation or shade.")

    if latest['Moisture'] < ranges['Moisture'][0]:
        stress += 2;
        issues.append("Dehydrated 🏜️")
        if weather and "rain" in weather.get('weather', [{}])[0].get('description', '').lower():
            tips.append("💡 Smart Tip: Soil dry, but external precipitation detected. Natural watering advised.")
        else:
            tips.append("💡 Tip: Initiate deep watering cycle.")
    elif latest['Moisture'] > ranges['Moisture'][1]:
        stress += 2;
        issues.append("Oversaturated 🌊");
        tips.append("💡 Tip: Suspend watering. Verify drainage.")

    if latest['Compensated_TDS'] < ranges['TDS'][0]:
        stress += 1;
        issues.append("Nutrients Low 🍽️");
        tips.append("💡 Tip: Administer balanced liquid fertilizer.")
    elif latest['Compensated_TDS'] > ranges['TDS'][1]:
        stress += 1;
        issues.append("Toxicity High 🤢");
        tips.append("💡 Tip: Flush soil substrate with pure water.")

    if latest['Light'] < ranges['Light'][0]:
        stress += 1;
        issues.append("Light Low 🌑");
        tips.append("💡 Tip: Increase exposure or utilize grow lights.")
    elif latest['Light'] > ranges['Light'][1]:
        stress += 1;
        issues.append("Light High ☀️");
        tips.append("💡 Tip: Provide indirect shade to prevent scorch.")

    if pressure_trend < -0.15:
        tips.append("⚠️ Weather Alert: Rapid barometric pressure drop. Storm conditions imminent.")

    if stress == 0:
        return "😁", "face-happy", "bg-happy", "System Optimal", ["💡 Tip: Current environmental parameters are ideal."] + tips
    elif stress == 1:
        return "😐", "face-okay", "bg-okay", f"Sub-optimal: {issues[0]}", tips
    elif stress == 2:
        return "😟", "face-stressed", "bg-stressed", f"Stress Detected: {issues[0]}", tips
    else:
        return "😫", "face-critical", "bg-critical", f"Critical Alert: {' | '.join(issues[:2])}", tips


def create_mpl_chart(df, y_col, title, color, ylabel=""):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(df['Timestamp'], df[y_col], color=color, linewidth=2)
    ax.set_title(title, fontsize=14, pad=10)
    ax.set_ylabel(ylabel)
    ax.grid(color='gray', linestyle='--', alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return fig


# --- Main Application Logic ---
st.title("🌿 Advanced Plant Ecosystem Dashboard")

weather_data = fetch_local_weather(OWM_API_KEY)

if os.path.exists(DATA_PATH) and os.path.getsize(DATA_PATH) > 60:
    try:
        df = pd.read_csv(DATA_PATH)

        required_cols = ["Timestamp", "Temp", "Humidity", "Pressure", "Moisture", "TDS", "Light"]
        if all(col in df.columns for col in required_cols) and not df.empty:

            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df.dropna(subset=['Timestamp'], inplace=True)

            df['VPD'] = calc_vpd(df['Temp'], df['Humidity'])

            temp_comp_factor = 1 + 0.02 * (df['Temp'] - 25)
            temp_comp_factor = np.where(temp_comp_factor == 0, 0.001, temp_comp_factor)
            df['Compensated_TDS'] = df['TDS'] / temp_comp_factor

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            recent_window = df.tail(30)

            pressure_trend = safe_gradient(recent_window['Pressure'])

            ranges = {
                "Temp": (18, 28), "Humidity": (40, 70), "Pressure": (950, 1050),
                "Moisture": (300, 700), "TDS": (500, 1500), "VPD": (0.4, 1.2), "Light": (200, 900)
            }

            main_tab1, main_tab2 = st.tabs(["🔴 LIVE DASHBOARD", "📅 LONG-TERM ANALYSIS"])

            # ==========================================
            # TAB 1: LIVE DASHBOARD
            # ==========================================
            with main_tab1:
                header_col1, header_col2 = st.columns([2, 1])

                with header_col1:
                    face_emoji, face_class, bg_class, mood_message, tips_list = evaluate_plant_health(latest, ranges,
                                                                                                      weather_data,
                                                                                                      pressure_trend)
                    tips_html = "".join([f"<div class='tip-text'>{tip}</div>" for tip in tips_list])

                    # Uses the unified dashboard-box class
                    st.markdown(f"""
                        <div class="dashboard-box mood-box {bg_class}">
                            <div class="{face_class}">{face_emoji}</div>
                            <div class="mood-title">"{mood_message}"</div>
                            {tips_html}
                        </div>
                    """, unsafe_allow_html=True)

                with header_col2:
                    if weather_data and 'main' in weather_data:
                        w_temp = weather_data['main']['temp']
                        w_desc = weather_data['weather'][0]['description'].title()
                        w_hum = weather_data['main']['humidity']
                        icon_code = weather_data['weather'][0]['icon']

                        # Added HTTPS to the image URL to fix the broken image circle
                        st.markdown(f"""
                            <div class="dashboard-box weather-box">
                                <h3 style="margin:0px 0px 10px 0px; color:#aaa;">📍 Kurunegala Forecast</h3>
                                <img src="https://openweathermap.org/img/wn/{icon_code}@2x.png" width="100">
                                <h1 style="margin:0px;">{w_temp:.1f}°C</h1>
                                <p style="font-size:18px; color:#00ffcc; margin:5px 0px;">{w_desc}</p>
                                <p style="color:#aaa; margin:0px;">Outside Humidity: {w_hum}%</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div class="dashboard-box weather-box">
                                <h3 style="color:#aaa; margin:0px;">📍 External Weather</h3>
                                <p style="color:#ff5555; margin-top:20px; font-size: 18px;">API Key Missing or Network Error.</p>
                                <p style="font-size:12px; color:#aaa;">Configuration required: Insert valid OpenWeatherMap API key.</p>
                            </div>
                        """, unsafe_allow_html=True)

                st.subheader("📡 Real-Time Sensor Status")
                cols = st.columns(7)

                with cols[0]:
                    st.metric("Temp (°C)", f"{latest['Temp']:.1f}", delta=f"{latest['Temp'] - previous['Temp']:.1f}",
                              help="Ambient air temperature.")
                    st.markdown(get_status_indicator(latest['Temp'], *ranges["Temp"]))
                with cols[1]:
                    st.metric("Humidity (%)", f"{latest['Humidity']:.1f}",
                              delta=f"{latest['Humidity'] - previous['Humidity']:.1f}", help="Relative Humidity (RH).")
                    st.markdown(get_status_indicator(latest['Humidity'], *ranges["Humidity"]))
                with cols[2]:
                    st.metric("Pressure", f"{latest['Pressure']:.1f}",
                              delta=f"{latest['Pressure'] - previous['Pressure']:.1f}",
                              help="Atmospheric Pressure. Local sensor overrides API data for immediate storm detection.")
                    st.markdown(get_status_indicator(latest['Pressure'], *ranges["Pressure"]))
                with cols[3]:
                    st.metric("Moisture", f"{latest['Moisture']:.0f}",
                              delta=f"{latest['Moisture'] - previous['Moisture']:.0f}",
                              help="Raw capacitive soil moisture.")
                    st.markdown(get_status_indicator(latest['Moisture'], *ranges["Moisture"]))
                with cols[4]:
                    st.metric("TDS (ppm)", f"{latest['Compensated_TDS']:.0f}",
                              delta=f"{latest['Compensated_TDS'] - previous['Compensated_TDS']:.0f}",
                              help="Total Dissolved Solids.")
                    st.markdown(get_status_indicator(latest['Compensated_TDS'], *ranges["TDS"]))
                with cols[5]:
                    st.metric("VPD (kPa)", f"{latest['VPD']:.2f}", delta=f"{latest['VPD'] - previous['VPD']:.2f}",
                              help="Vapor Pressure Deficit.")
                    st.markdown(get_status_indicator(latest['VPD'], *ranges["VPD"]))
                with cols[6]:
                    st.metric("Light (Raw)", f"{latest['Light']:.0f}",
                              delta=f"{latest['Light'] - previous['Light']:.0f}", help="LDR Light Intensity.")
                    st.markdown(get_status_indicator(latest['Light'], *ranges["Light"]))

                st.markdown("---")

                st.subheader("🔬 Derived Insights & Predictions")
                ins_col1, ins_col2, ins_col3 = st.columns(3)

                with ins_col1:
                    moisture_drop_rate = safe_gradient(recent_window['Moisture'])
                    if moisture_drop_rate < -0.1:
                        points_to_wilt = max(0, latest['Moisture'] - 300)
                        cycles_left = points_to_wilt / abs(moisture_drop_rate)
                        hours_left = (cycles_left * 2) / 3600
                        st.metric("Irrigation Prediction", f"Wilt in {hours_left:.1f}h ⏳",
                                  help="Calculates the immediate mathematical slope of soil moisture depletion to project the estimated time until the absolute dry threshold is reached.")
                    else:
                        st.metric("Irrigation Prediction", "Stable/Rising 🟢",
                                  help="Calculates the immediate mathematical slope of soil moisture depletion to project dry-out time. Currently stable.")

                with ins_col2:
                    temp_trend = safe_gradient(recent_window['Temp'])
                    moisture_trend = safe_gradient(recent_window['Moisture'])
                    if temp_trend > 0.5 and moisture_trend > -0.05:
                        st.metric("Transpiration Status", "Shock Detected ⚠️",
                                  help="Detects stomatal closure. Triggered when ambient temperature rises rapidly but soil moisture depletion halts.")
                    else:
                        st.metric("Transpiration Status", "Normal 🟢",
                                  help="Detects stomatal closure. Triggered when ambient temperature rises rapidly but soil moisture depletion halts.")

                with ins_col3:
                    if latest['VPD'] < 0.4:
                        vpd_stat = "Danger: Low Transpiration 🔵"
                    elif 0.4 <= latest['VPD'] <= 0.8:
                        vpd_stat = "Ideal: Early Vegetative 🟢"
                    elif 0.8 < latest['VPD'] <= 1.2:
                        vpd_stat = "Ideal: Late/Flowering 🟢"
                    else:
                        vpd_stat = "Danger: High Stress 🔴"
                    st.metric("VPD Growth Zone", vpd_stat,
                              help="Vapor Pressure Deficit combines Temperature and Humidity. High VPD causes excessive transpiration; low VPD halts nutrient transport.")

                st.markdown("---")
                st.subheader("📊 Live Data Visualization")
                time_filter = st.radio("⏳ Select Graph Time Span:",
                                       ["Last 10 Minutes", "Last Hour", "Last 24 Hours", "All Time"], horizontal=True)

                now = df['Timestamp'].max()
                if time_filter == "Last 10 Minutes":
                    mask = (df['Timestamp'] >= now - timedelta(minutes=10))
                elif time_filter == "Last Hour":
                    mask = (df['Timestamp'] >= now - timedelta(hours=1))
                elif time_filter == "Last 24 Hours":
                    mask = (df['Timestamp'] >= now - timedelta(days=1))
                else:
                    mask = df['Timestamp'] == df['Timestamp']

                graph_df = df.loc[mask]

                if not graph_df.empty:
                    v_tab1, v_tab2, v_tab3, v_tab4, v_tab5, v_tab6, v_tab7 = st.tabs(
                        ["Temperature", "Humidity", "Pressure", "Soil Moisture", "TDS", "VPD", "Light Levels"])
                    with v_tab1: fig1 = create_mpl_chart(graph_df, 'Temp', "Ambient Temperature", "#ff5555",
                                                         "°C"); st.pyplot(fig1); plt.close(fig1)
                    with v_tab2: fig2 = create_mpl_chart(graph_df, 'Humidity', "Relative Humidity", "#00aaff",
                                                         "%"); st.pyplot(fig2); plt.close(fig2)
                    with v_tab3: fig3 = create_mpl_chart(graph_df, 'Pressure', "Atmospheric Pressure", "#ffffff",
                                                         "hPa"); st.pyplot(fig3); plt.close(fig3)
                    with v_tab4: fig4 = create_mpl_chart(graph_df, 'Moisture', "Soil Moisture Levels", "#00ff00",
                                                         "Raw Value"); st.pyplot(fig4); plt.close(fig4)
                    with v_tab5: fig5 = create_mpl_chart(graph_df, 'Compensated_TDS', "Nutrient Concentration (TDS)",
                                                         "#ffaa00", "ppm"); st.pyplot(fig5); plt.close(fig5)
                    with v_tab6: fig6 = create_mpl_chart(graph_df, 'VPD', "Vapor Pressure Deficit (VPD)", "#ff00ff",
                                                         "kPa"); st.pyplot(fig6); plt.close(fig6)
                    with v_tab7: fig7 = create_mpl_chart(graph_df, 'Light', "Light Intensity (LDR)", "#ffff00",
                                                         "Raw Value"); st.pyplot(fig7); plt.close(fig7)

            # ==========================================
            # TAB 2: LONG-TERM HISTORICAL ANALYSIS
            # ==========================================
            with main_tab2:
                st.subheader("📅 Long-Term Ecosystem Profiling")
                st.write(
                    "This section resamples raw high-frequency data into daily agricultural averages to profile the overall plant environment.")

                df_daily = df.copy()
                df_daily.set_index('Timestamp', inplace=True)

                daily_stats = pd.DataFrame()
                daily_stats['Max_Temp'] = df_daily['Temp'].resample('D').max()
                daily_stats['Min_Temp'] = df_daily['Temp'].resample('D').min()
                daily_stats['DIF (Temp Diff)'] = daily_stats['Max_Temp'] - daily_stats['Min_Temp']
                daily_stats['Avg_Moisture'] = df_daily['Moisture'].resample('D').mean()
                daily_stats['Avg_TDS'] = df_daily['Compensated_TDS'].resample('D').mean()
                daily_stats['Relative Light Budget'] = df_daily['Light'].resample('D').sum() / 1000

                daily_stats.dropna(inplace=True)

                if len(daily_stats) > 0:
                    hist_col1, hist_col2, hist_col3 = st.columns(3)

                    with hist_col1:
                        today_dif = daily_stats['DIF (Temp Diff)'].iloc[-1]
                        st.metric("Daily Temp Swing (DIF)", f"{today_dif:.1f} °C",
                                  help="Diurnal Temperature Variation (DIF) is the difference between daily maximum and minimum temperatures. A drop of 5-10°C at night is required by most plants to trigger blooming and regulate internodal stretching.")

                    with hist_col2:
                        if len(daily_stats) > 1:
                            tds_trend = daily_stats['Avg_TDS'].iloc[-1] - daily_stats['Avg_TDS'].iloc[-2]
                            moisture_trend = daily_stats['Avg_Moisture'].iloc[-1] - daily_stats['Avg_Moisture'].iloc[-2]

                            if tds_trend > 0 and moisture_trend < 0:
                                status_text = "Lockout Warning ⚠️"
                            elif tds_trend < 0 and moisture_trend < 0:
                                status_text = "Active Feeding 🟢"
                            else:
                                status_text = "Baseline/Watering ⏸️"
                        else:
                            status_text = "Processing..."

                        st.metric("Nutrient Uptake Status", status_text,
                                  help="Evaluates TDS and Moisture trends over multiple days. A drop in moisture coupled with a rise in TDS indicates Nutrient Lockout, requiring a pure water flush.")

                    with hist_col3:
                        today_light = daily_stats['Relative Light Budget'].iloc[-1]
                        st.metric("Daily Light Integral (Proxy)", f"{today_light:.0f} Photons",
                                  help="Integrates Light intensity readings over a 24-hour period to measure the total volume of daily light. Useful for determining if supplemental artificial lighting is required.")

                    st.markdown("---")
                    st.subheader("📉 Evapotranspiration Curve",
                                 help="Extended soil moisture tracking forms a 'sawtooth' pattern. The downward slope mathematically defines the exact rate of evapotranspiration at given temperatures.")

                    fig_hist, ax_hist = plt.subplots(figsize=(12, 4))
                    ax_hist.plot(df['Timestamp'], df['Moisture'], color="#00ff00", alpha=0.7)
                    ax_hist.set_title("Historical Soil Moisture Depletion Profile", fontsize=12)
                    ax_hist.set_ylabel("Raw Moisture")
                    ax_hist.grid(color='gray', linestyle='--', alpha=0.3)
                    fig_hist.autofmt_xdate(rotation=45)
                    st.pyplot(fig_hist)
                    plt.close(fig_hist)

                else:
                    st.info(
                        "📊 Insufficient data. The system requires a minimum of 24 hours of continuous logging to generate the Long-Term Analysis report.")

        else:
            st.error(
                "❌ Data structure anomaly detected. Please verify CSV integrity or delete `data/plant_data.csv` to initiate a fresh log.")

    except pd.errors.EmptyDataError:
        pass
    except Exception as e:
        st.error(f"⚠️ System Exception Encountered: {e}")

else:
    st.warning("⏳ System initializing. Awaiting initial data packet from hardware...")

time.sleep(2)
st.rerun()