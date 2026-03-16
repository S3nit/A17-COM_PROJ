import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import requests
from datetime import timedelta

st.set_page_config(page_title="Advanced Plant Monitor", layout="wide", page_icon="🌿")
DATA_PATH = "data/plant_data.csv"
OWM_API_KEY = "6c1dcad79d77f2bb646d523712c307d3"

plt.style.use('dark_background')

st.markdown("""
    <style>
    .metric-card { background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .dashboard-box {
        border-radius: 20px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 400px; 
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

@st.cache_data(ttl=900)
def fetch_local_weather(api_key):
    if api_key == "YOUR_API_KEY_HERE" or not api_key:
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Peradeniya,lk&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        return None

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
    stress = 0; issues = []; tips = []

    if latest['Temp'] < ranges['Temp'][0]:
        stress += 1; issues.append("Temp Low 🥶"); tips.append("💡 Tip: Relocate to a warmer, sunnier area.")
    elif latest['Temp'] > ranges['Temp'][1]:
        stress += 1; issues.append("Temp High 🥵"); tips.append("💡 Tip: Provide temporary shade from extreme afternoon sun.")

    if latest['Moisture'] < ranges['Moisture'][0]:
        stress += 2; issues.append("Dehydrated 🏜️")
        if weather and "rain" in weather.get('weather', [{}])[0].get('description', '').lower():
            tips.append("💡 Smart Tip: Soil dry, but external precipitation detected. Natural watering advised.")
        else:
            tips.append("💡 Tip: Initiate deep watering cycle.")
    elif latest['Moisture'] > ranges['Moisture'][1]:
        stress += 2; issues.append("Oversaturated 🌊"); tips.append("💡 Tip: Suspend watering. Ensure pot has adequate drainage.")

    if latest['Compensated_TDS'] < ranges['TDS'][0]:
        stress += 1; issues.append("Nutrients Low 🍽️"); tips.append("💡 Tip: Administer balanced liquid fertilizer.")
    elif latest['Compensated_TDS'] > ranges['TDS'][1]:
        stress += 1; issues.append("Toxicity High 🤢"); tips.append("💡 Tip: Flush soil substrate with pure water.")

    if latest['Light'] < ranges['Light'][0]:
        stress += 1; issues.append("Light Low 🌑"); tips.append("💡 Tip: Jasmine requires bright light to flower. Increase exposure.")
    elif latest['Light'] > ranges['Light'][1]:
        stress += 1; issues.append("Light High ☀️"); tips.append("💡 Tip: Extreme UV detected. Provide indirect shade to prevent scorch.")

    if pressure_trend < -0.15:
        tips.append("⚠️ Weather Alert: Rapid barometric pressure drop. Storm conditions imminent.")

    if stress == 0:
        return "😁", "face-happy", "bg-happy", "System Optimal", ["💡 Tip: Current tropical environmental parameters are ideal."] + tips
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
                "Temp": (22, 32),
                "Humidity": (60, 90),
                "Pressure": (950, 1050),
                "Moisture": (350, 750),
                "TDS": (600, 1200),
                "VPD": (0.5, 1.4),
                "Light": (400, 950)
            }

            main_tab1, main_tab2 = st.tabs(["🔴 LIVE DASHBOARD", "📅 LONG-TERM ANALYSIS"])

            with main_tab1:
                header_col1, header_col2 = st.columns([2, 1])

                with header_col1:
                    face_emoji, face_class, bg_class, mood_message, tips_list = evaluate_plant_health(latest, ranges, weather_data, pressure_trend)
                    tips_html = "".join([f"<div class='tip-text'>{tip}</div>" for tip in tips_list])

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

                        st.markdown(f"""
                            <div class="dashboard-box weather-box">
                                <h3 style="margin:0px 0px 10px 0px; color:#aaa;">📍 Peradeniya Forecast</h3>
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
                    st.metric("Temp (°C)", f"{latest['Temp']:.1f}", delta=f"{latest['Temp'] - previous['Temp']:.1f}")
                    st.markdown(get_status_indicator(latest['Temp'], *ranges["Temp"]))
                with cols[1]:
                    st.metric("Humidity (%)", f"{latest['Humidity']:.1f}", delta=f"{latest['Humidity'] - previous['Humidity']:.1f}")
                    st.markdown(get_status_indicator(latest['Humidity'], *ranges["Humidity"]))
                with cols[2]:
                    st.metric("Pressure", f"{latest['Pressure']:.1f}", delta=f"{latest['Pressure'] - previous['Pressure']:.1f}")
                    st.markdown(get_status_indicator(latest['Pressure'], *ranges["Pressure"]))
                with cols[3]:
                    st.metric("Moisture", f"{latest['Moisture']:.0f}", delta=f"{latest['Moisture'] - previous['Moisture']:.0f}")
                    st.markdown(get_status_indicator(latest['Moisture'], *ranges["Moisture"]))
                with cols[4]:
                    st.metric("TDS (ppm)", f"{latest['Compensated_TDS']:.0f}", delta=f"{latest['Compensated_TDS'] - previous['Compensated_TDS']:.0f}")
                    st.markdown(get_status_indicator(latest['Compensated_TDS'], *ranges["TDS"]))
                with cols[5]:
                    st.metric("VPD (kPa)", f"{latest['VPD']:.2f}", delta=f"{latest['VPD'] - previous['VPD']:.2f}")
                    st.markdown(get_status_indicator(latest['VPD'], *ranges["VPD"]))
                with cols[6]:
                    st.metric("Light (Raw)", f"{latest['Light']:.0f}", delta=f"{latest['Light'] - previous['Light']:.0f}")
                    st.markdown(get_status_indicator(latest['Light'], *ranges["Light"]))

                st.markdown("---")
                st.subheader("🔬 Derived Insights & Predictions")
                ins_col1, ins_col2, ins_col3 = st.columns(3)

                with ins_col1:
                    moisture_drop_rate = safe_gradient(recent_window['Moisture'])
                    if moisture_drop_rate < -0.05:
                        points_to_wilt = max(0, latest['Moisture'] - 350)
                        cycles_left = points_to_wilt / abs(moisture_drop_rate)
                        hours_left = (cycles_left * 2) / 3600
                        st.metric("Time Till Next Watering", f"{hours_left:.1f} Hours ⏳", delta=f"{moisture_drop_rate:.2f} rate", delta_color="off")
                    else:
                        st.metric("Time Till Next Watering", "Stable 🟢", delta=f"{moisture_drop_rate:.2f} rate", delta_color="off")

                with ins_col2:
                    temp_trend = safe_gradient(recent_window['Temp'])
                    moisture_trend = safe_gradient(recent_window['Moisture'])
                    if temp_trend > 0.5 and moisture_trend > -0.05:
                        st.metric("Transpiration Status", "Shock Detected ⚠️")
                    else:
                        st.metric("Transpiration Status", "Normal 🟢")

                with ins_col3:
                    if latest['VPD'] < 0.5: vpd_stat = "Danger: Low Transpiration 🔵"
                    elif 0.5 <= latest['VPD'] <= 0.9: vpd_stat = "Ideal: Early Vegetative 🟢"
                    elif 0.9 < latest['VPD'] <= 1.4: vpd_stat = "Ideal: Late/Flowering 🟢"
                    else: vpd_stat = "Danger: High Stress 🔴"
                    st.metric("VPD Growth Zone", vpd_stat)

                st.markdown("---")
                st.subheader("📊 Live Data Visualization")
                time_filter = st.radio("⏳ Select Graph Time Span:", ["Last 10 Minutes", "Last Hour", "Last 24 Hours", "All Time"], horizontal=True)

                now = df['Timestamp'].max()
                if time_filter == "Last 10 Minutes": mask = (df['Timestamp'] >= now - timedelta(minutes=10))
                elif time_filter == "Last Hour": mask = (df['Timestamp'] >= now - timedelta(hours=1))
                elif time_filter == "Last 24 Hours": mask = (df['Timestamp'] >= now - timedelta(days=1))
                else: mask = df['Timestamp'] == df['Timestamp']

                graph_df = df.loc[mask]

                if not graph_df.empty:
                    v_tab1, v_tab2, v_tab3, v_tab4, v_tab5, v_tab6, v_tab7 = st.tabs(["Temperature", "Humidity", "Pressure", "Soil Moisture", "TDS", "VPD", "Light Levels"])
                    with v_tab1: fig1 = create_mpl_chart(graph_df, 'Temp', "Ambient Temperature", "#ff5555", "°C"); st.pyplot(fig1); plt.close(fig1)
                    with v_tab2: fig2 = create_mpl_chart(graph_df, 'Humidity', "Relative Humidity", "#00aaff", "%"); st.pyplot(fig2); plt.close(fig2)
                    with v_tab3: fig3 = create_mpl_chart(graph_df, 'Pressure', "Atmospheric Pressure", "#ffffff", "hPa"); st.pyplot(fig3); plt.close(fig3)
                    with v_tab4: fig4 = create_mpl_chart(graph_df, 'Moisture', "Soil Moisture Levels", "#00ff00", "Raw"); st.pyplot(fig4); plt.close(fig4)
                    with v_tab5: fig5 = create_mpl_chart(graph_df, 'Compensated_TDS', "Nutrient Concentration (TDS)", "#ffaa00", "ppm"); st.pyplot(fig5); plt.close(fig5)
                    with v_tab6: fig6 = create_mpl_chart(graph_df, 'VPD', "Vapor Pressure Deficit (VPD)", "#ff00ff", "kPa"); st.pyplot(fig6); plt.close(fig6)
                    with v_tab7: fig7 = create_mpl_chart(graph_df, 'Light', "Light Intensity (LDR)", "#ffff00", "Raw"); st.pyplot(fig7); plt.close(fig7)

            with main_tab2:
                st.subheader("📅 Long-Term Ecosystem Profiling")
                df_daily = df.copy().set_index('Timestamp')
                daily_stats = pd.DataFrame()
                daily_stats['Max_Temp'] = df_daily['Temp'].resample('D').max()
                daily_stats['Min_Temp'] = df_daily['Temp'].resample('D').min()
                daily_stats['DIF'] = daily_stats['Max_Temp'] - daily_stats['Min_Temp']
                daily_stats['Avg_Moisture'] = df_daily['Moisture'].resample('D').mean()
                daily_stats['Avg_TDS'] = df_daily['Compensated_TDS'].resample('D').mean()
                daily_stats['Light_Budget'] = df_daily['Light'].resample('D').sum() / 1000
                daily_stats.dropna(inplace=True)

                if len(daily_stats) > 0:
                    hist_col1, hist_col2, hist_col3 = st.columns(3)
                    with hist_col1: st.metric("Daily Temp Swing (DIF)", f"{daily_stats['DIF'].iloc[-1]:.1f} °C")
                    with hist_col2:
                        if len(daily_stats) > 1:
                            t_trend = daily_stats['Avg_TDS'].iloc[-1] - daily_stats['Avg_TDS'].iloc[-2]
                            m_trend = daily_stats['Avg_Moisture'].iloc[-1] - daily_stats['Avg_Moisture'].iloc[-2]
                            status = "Lockout Warning ⚠️" if t_trend > 0 and m_trend < 0 else ("Active Feeding 🟢" if t_trend < 0 and m_trend < 0 else "Baseline ⏸️")
                        else: status = "Processing..."
                        st.metric("Nutrient Uptake Status", status)
                    with hist_col3: st.metric("Daily Light Integral (Proxy)", f"{daily_stats['Light_Budget'].iloc[-1]:.0f} Photons")

                    st.markdown("---")
                    st.subheader("📉 Evapotranspiration Curve")
                    fig_h, ax_h = plt.subplots(figsize=(12, 4))
                    ax_h.plot(df['Timestamp'], df['Moisture'], color="#00ff00", alpha=0.7)
                    ax_h.set_title("Historical Soil Moisture Depletion Profile")
                    ax_h.grid(color='gray', linestyle='--', alpha=0.3)
                    fig_h.autofmt_xdate(rotation=45)
                    st.pyplot(fig_h); plt.close(fig_h)
                else:
                    st.info("📊 Insufficient data for 24h logging reports.")

        else:
            st.error("❌ Data structure anomaly. Verify CSV or delete file to reset.")

    except pd.errors.EmptyDataError:
        pass
    except Exception as e:
        st.error(f"⚠️ System Exception: {e}")
else:
    st.warning("⏳ System initializing. Awaiting data from hardware...")

time.sleep(2)
st.rerun()
