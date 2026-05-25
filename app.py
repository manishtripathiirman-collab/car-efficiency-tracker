import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import os

# Ensure the Google GenAI library is present
try:
    from google import genai
except ImportError:
    st.error("Please ensure 'google-genai' is listed in your requirements.txt file!")

# Set up page configuration
st.set_page_config(page_title="EcoSport Cockpit Pro", page_icon="⚡", layout="centered")

# --- ADVANCED GLOBAL CUSTOM COLOR SCHEME (CSS INJECTION) ---
st.markdown("""
    <style>
        /* Global App Background Override */
        .stApp {
            background-color: #0B0F19 !important;
            color: #E2E8F0 !important;
        }
        
        /* Modernized Custom Cards */
        div[data-testid="stContainer"] {
            background-color: #111827 !important;
            border: 1px solid #1F2937 !important;
            border-radius: 12px !important;
            padding: 15px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
        }
        
        /* Input Field Styling Customizations */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: #1F2937 !important;
            border: 1px solid #374151 !important;
            border-radius: 8px !important;
        }
        
        /* Label Typography Enhancements */
        label, p {
            color: #94A3B8 !important;
            font-weight: 500 !important;
        }
        
        /* Premium Accent Headers */
        h1, h2, h3 {
            color: #F8FAFC !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- NEON TECH COCKPIT HEADER BANNER ---
st.markdown("""
    <div style='background: linear-gradient(135deg, #1E1B4B, #0F172A); padding: 20px; border-radius: 12px; margin-bottom: 25px; text-align: center; border: 1px solid #3B82F6; box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);'>
        <h1 style='margin: 0; font-size: 1.6rem; font-weight: 900; color: #06B6D4; letter-spacing: 1.5px; text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);'>⚡ ECOSPORT COCKPIT PRO</h1>
        <p style='margin: 4px 0 0 0; color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 3px;'>Intelligent Dynamic Telemetry & Asset Log</p>
    </div>
""", unsafe_allow_html=True)

# --- DYNAMIC VEHICLE HEALTH READOUT ---
with st.container():
    col_st1, col_st2 = st.columns([3, 1])
    with col_st1:
        st.markdown("<p style='margin:0; font-weight:700; color:#F8FAFC !important; font-size:1rem;'>⚙️ Status Telemetry Matrix</p>", unsafe_allow_html=True)
        st.caption("Core Diagnostics: System online, state memory fully locked.")
    with col_st2:
        st.markdown("<span style='float:right; background: linear-gradient(135deg, #06B6D4, #3B82F6); color:#FFFFFF; padding: 5px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.5px; box-shadow: 0 0 10px rgba(6, 182, 212, 0.4);'>CONNECTED</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- INITIALIZE APP MEMORY ---
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = []

df = pd.DataFrame(st.session_state.fuel_logs)

# --- THE ROLLING MATH ENGINE ---
if len(df) >= 2:
    df = df.sort_values("Odometer (km)").reset_index(drop=True)
    df['Distance Driven (km)'] = df['Odometer (km)'].diff()
    df['km/L'] = df['Distance Driven (km)'] / df['Liters']
    
    total_tracked_km = df['Distance Driven (km)'].sum()
    total_money_spent = df['Cost (₹)'].sum()
    
    avg_mileage = total_tracked_km / df['Liters'].iloc[1:].sum()
    cost_per_km = total_money_spent / total_tracked_km
else:
    avg_mileage, cost_per_km = 0.0, 0.0

# --- HIGH-CONTRAST CHROME PERFORMANCE MATRICES ---
st.markdown("### 📊 Performance Analytics")
col_card1, col_card2 = st.columns(2)

with col_card1:
    st.markdown(f"""
        <div style='background-color: #111827; border-left: 4px solid #06B6D4; padding: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>
            <p style='margin:0; font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;'>Average Fuel Mileage</p>
            <h2 style='margin:5px 0; color:#F8FAFC; font-weight:800; font-size:1.8rem;'>{avg_mileage:.2f} <span style='font-size:0.9rem; color:#06B6D4; font-weight:500;'>km/L</span></h2>
        </div>
    """, unsafe_allow_html=True)
        
with col_card2:
    st.markdown(f"""
        <div style='background-color: #111827; border-left: 4px solid #10B981; padding: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>
            <p style='margin:0; font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;'>Running Cost / KM</p>
            <h2 style='margin:5px 0; color:#F8FAFC; font-weight:800; font-size:1.8rem;'>₹ {cost_per_km:.2f} <span style='font-size:0.9rem; color:#10B981; font-weight:500;'>/ km</span></h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- AUTOMATED AI BILL SCANNER MODULE ---
st.markdown("### 📷 Step 1: Optical Receipt Intake")
with st.container():
    activate_camera = st.checkbox("Initialize Vision Scanner Lens", value=False)
    
    scanned_liters = 0.0
    scanned_price = 0.0
    api_key = st.secrets.get("GEMINI_API_KEY")

    if activate_camera:
        uploaded_bill = st.camera_input("Align fuel bill inside lens field")

        if uploaded_bill is not None:
            img = Image.open(uploaded_bill)
            
            if not api_key:
                st.error("⚠️ App Secret Missing: Configure 'GEMINI_API_KEY'.")
            else:
                with st.spinner("⚡ Deciphering receipt telemetry matrix..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        prompt = """
                        Examine this fuel receipt image carefully. Extract total volume in liters and total cost in Rupees. 
                        Return output strictly formatted as JSON object with keys "liters" and "total_cost".
                        """
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=[img, prompt])
                        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(cleaned_text)
                        
                        scanned_liters = float(data.get("liters", 0.0))
                        scanned_price = float(data.get("total_cost", 0.0))
                        
                        st.success(f"🤖 Verified: {scanned_liters} Liters | Bill Total: ₹ {scanned_price}")
                    except Exception as e:
                        st.error(f"Error parsing receipt text: {e}")
    else:
        st.caption("🔒 Scanner array currently idling.")

st.markdown("<br>", unsafe_allow_html=True)

# --- MASTER TELEMETRY FILL FORM ---
st.markdown("### ⛽ Step 2: Telemetry Log Entry")
with st.container():
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        log_date = st.date_input("Stamping Date", value=datetime.today(), key="log_date_main")
        odometer = st.number_input("Odometer Tracker (km)", min_value=0, step=1)
    with form_col2:
        liters = st.number_input("Infused Volume (Liters)", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
        price = st.number_input("Transaction Bill Value (₹)", min_value=0.0, value=scanned_price, step=10.0)
    
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#94A3B8 !important; margin: 10px 0 5px 0; text-transform:uppercase;'>CONCURRENT LOG METRICS:</p>", unsafe_allow_html=True)
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        air_filled = st.checkbox("💨 Air Pressure Calibrated", value=False)
    with col_chk2:
        had_service = st.checkbox("🔧 Core Mechanical Service Executed", value=False)
    
    service_date_str = "-"
    if had_service:
        service_date = st.date_input("Confirm Service Event Date", value=datetime.today(), key="srv_date_main")
        service_date_str = service_date.strftime("%Y-%m-%d")

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    if st.button("⚡ Commit Log to Database", use_container_width=True, type="primary"):
        if odometer > 0 and liters > 0 and price > 0:
            new_entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "Odometer (km)": odometer,
                "Liters": liters,
                "Cost (₹)": price,
                "Air Filled": "Yes" if air_filled else "No",
                "Last Service Date": service_date_str
            }
            st.session_state.fuel_logs.append(new_entry)
            st.success("Entry securely logged!")
            st.rerun()
        else:
            st.error("Validation Halt: Ensure all core fields are set above zero.")

st.markdown("<br>", unsafe_allow_html=True)

# --- VISUAL ANALYTICS CURVE ---
if len(df) >= 2:
    st.markdown("### 📈 Efficiency Velocity Curve")
    chart_data = df.dropna(subset=['km/L']).set_index('Date')
    st.line_chart(chart_data['km/L'], color="#06B6D4")
    st.markdown("<br>", unsafe_allow_html=True)

# --- HISTORICAL TRANSACTIONS RECORD MATRIX ---
st.markdown("### 📋 Fleet Record Ledger")
if len(df) > 0:
    display_df = df.copy()
    if 'km/L' in display_df.columns:
        display_df['km/L'] = display_df['km/L'].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("Logbook ledger database empty.")

st.markdown("<br><br><hr style='border:0.5px solid #1F2937;'>", unsafe_allow_html=True)

# --- UNDERGROUND ADMINISTRATIVE WORKSTATION ---
with st.expander("🛠️ Console Engine Settings", expanded=False):
    if len(st.session_state.fuel_logs) > 0:
        log_options = [f"#{i+1} | {log['Date']} | {log['Odometer (km)']} km" for i, log in enumerate(st.session_state.fuel_logs)]
        selected_option = st.selectbox("Target Block Row:", log_options)
        
        selected_index = log_options.index(selected_option)
        target_log = st.session_state.fuel_logs[selected_index]
        
        edit_date = st.date_input("Edit Stamping Date", value=datetime.strptime(target_log["Date"], "%Y-%m-%d"), key="edit_date_pick")
        edit_odo = st.number_input("Edit Odometer Reading", min_value=0, value=int(target_log["Odometer (km)"]))
        edit_liters = st.number_input("Edit Liters Metric", min_value=0.0, value=float(target_log["Liters"]), step=0.01)
        edit_cost = st.number_input("Edit Total Price Stamped", min_value=0.0, value=float(target_log["Cost (₹)"]))
        
        edit_air = st.checkbox("Toggle Air Filled Status", value=(target_log.get("Air Filled", "No") == "Yes"))
        edit_srv_check = st.checkbox("Toggle Mechanical Service Status", value=(target_log.get("Last Service Date", "-") != "-"))
        
        edit_srv_date_str = "-"
        if edit_srv_check:
            current_srv_val = target_log.get("Last Service Date", "-")
            default_srv_date = datetime.today() if current_srv_val == "-" else datetime.strptime(current_srv_val, "%Y-%m-%d")
            edit_srv_date = st.date_input("Edit Service Link Date", value=default_srv_date, key="edit_srv_pick")
            edit_srv_date_str = edit_srv_date.strftime("%Y-%m-%d")

        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            if st.button("💾 Apply Modifications", use_container_width=True):
                st.session_state.fuel_logs[selected_index] = {
                    "Date": edit_date.strftime("%Y-%m-%d"),
                    "Odometer (km)": edit_odo,
                    "Liters": edit_liters,
                    "Cost (₹)": edit_cost,
                    "Air Filled": "Yes" if edit_air else "No",
                    "Last Service Date": edit_srv_date_str
                }
                st.success("Log block modified!")
                st.rerun()
        with col_ed2:
            if st.button("🗑️ Wipe Registry Record", use_container_width=True):
                st.session_state.fuel_logs.pop(selected_index)
                st.warning("Entry cleared from registry matrix.")
                st.rerun()
    else:
        st.caption("Administrative override console empty.")