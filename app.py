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

# Set up page configuration with premium styling layout
st.set_page_config(page_title="EcoSport Grand Tracker", page_icon="🏎️", layout="centered")

# --- PREMIUM EXECUTIVE BANNER DESIGN ---
st.markdown("""
    <div style='background: linear-gradient(135deg, #0F172A, #1E293B); padding: 22px 20px; border-radius: 12px; margin-bottom: 20px; text-align: center; border-left: 5px solid #3B82F6;'>
        <h1 style='margin: 0; font-size: 1.7rem; font-weight: 800; color: #F8FAFC; letter-spacing: 1px;'>🏎️ ECOSPORT EXECUTIVE</h1>
        <p style='margin: 4px 0 0 0; color: #94A3B8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px;'>AI Intelligence & Fleet Logbook</p>
    </div>
""", unsafe_allow_html=True)

# --- LIVE CAR STATUS BLOCK ---
with st.container(border=True):
    col_st1, col_st2 = st.columns([2, 1])
    with col_st1:
        st.markdown("##### ⚙️ Vehicle Status Monitor")
        st.caption("System Diagnosis: **Optimal Operational Efficiency**")
    with col_st2:
        st.markdown("<span style='float:right; background-color:#DCFCE7; color:#166534; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; margin-top: 5px;'>CONNECTED</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 1. INITIALIZE APP MEMORY ---
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = []

# Build working DataFrame
df = pd.DataFrame(st.session_state.fuel_logs)

# --- 2. THE ROLLING MATH ENGINE ---
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

# --- 3. EXECUTIVE ANALYTICS MATRIX ---
st.markdown("### 📊 Performance Analytics")
col_card1, col_card2 = st.columns(2)

with col_card1:
    with st.container(border=True):
        st.markdown("<p style='margin:0; font-size:0.8rem; color:#64748B; font-weight:600;'>AVERAGE MILEAGE</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin:5px 0; color:#3B82F6; font-weight:800;'>{avg_mileage:.2f} <span style='font-size:1rem; font-weight:400; color:#64748B;'>km/L</span></h2>", unsafe_allow_html=True)
        
with col_card2:
    with st.container(border=True):
        st.markdown("<p style='margin:0; font-size:0.8rem; color:#64748B; font-weight:600;'>RUNNING COST</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin:5px 0; color:#10B981; font-weight:800;'>₹ {cost_per_km:.2f} <span style='font-size:1rem; font-weight:400; color:#64748B;'>/ km</span></h2>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 4. LIVE AUTOMATED AI BILL SCANNER ---
st.markdown("### 📷 Phase 1: Optical Receipt Intake")
with st.container(border=True):
    activate_camera = st.checkbox("Initialize AI Scanner Lens", value=False)
    
    scanned_liters = 0.0
    scanned_price = 0.0
    api_key = st.secrets.get("GEMINI_API_KEY")

    if activate_camera:
        uploaded_bill = st.camera_input("Position fuel bill inside camera guidelines")

        if uploaded_bill is not None:
            img = Image.open(uploaded_bill)
            
            if not api_key:
                st.error("⚠️ System Error: 'GEMINI_API_KEY' is missing in server configuration secrets.")
            else:
                with st.spinner("⚡ Processing receipt layout structure via Gemini Vision AI..."):
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
                        
                        st.success(f"🤖 Extraction Verified: {scanned_liters} Liters | Total Cost: ₹ {scanned_price}")
                    except Exception as e:
                        st.error(f"Error parsing receipt text: {e}")
    else:
        st.caption("🔒 Scanner telemetry offline. Check box above to initialize camera array.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. VEHICLE LOG ENTRY FORM WITH INTEGRATED CHECKS ---
st.markdown("### ⛽ Phase 2: Telemetry Log Entry")
with st.container(border=True):
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        log_date = st.date_input("Log Date Stamping", value=datetime.today(), key="log_date_main")
        odometer = st.number_input("Current Odometer Track (km)", min_value=0, step=1)
    with form_col2:
        liters = st.number_input("Fuel Volume Infused (Liters)", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
        price = st.number_input("Total Transaction Cost (₹)", min_value=0.0, value=scanned_price, step=10.0)
    
    st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#475569; margin-bottom:5px;'>CONCURRENT MAINTENANCE CHECKLIST:</p>", unsafe_allow_html=True)
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        air_filled = st.checkbox("💨 Air Pressure Replenished", value=False)
    with col_chk2:
        had_service = st.checkbox("🔧 Full Mechanical Service Executed", value=False)
    
    service_date_str = "-"
    if had_service:
        service_date = st.date_input("Confirm Service Event Date", value=datetime.today(), key="srv_date_main")
        service_date_str = service_date.strftime("%Y-%m-%d")

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    if st.button("💾 Commit Log to Matrix", use_container_width=True, type="primary"):
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
            st.success("Log successfully compiled into storage matrix!")
            st.rerun()
        else:
            st.error("Validation Error: Please fill in all mechanical readings before saving.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. VISUAL ANALYTICS CHART ---
if len(df) >= 2:
    st.markdown("### 📈 Efficiency Velocity Curve")
    chart_data = df.dropna(subset=['km/L']).set_index('Date')
    st.line_chart(chart_data['km/L'], color="#3B82F6")
    st.markdown("<br>", unsafe_allow_html=True)

# --- 7. HISTORICAL TRANSACTIONS SHEET ---
st.markdown("### 📋 Historic Fleet Ledger Sheets")
if len(df) > 0:
    display_df = df.copy()
    if 'km/L' in display_df.columns:
        display_df['km/L'] = display_df['km/L'].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("The master log sheet registry is completely vacant. Input logs to initialize history ledger.")

st.markdown("<br><br><hr style='border:0.5px solid #E2E8F0;'>", unsafe_allow_html=True)

# --- 8. DISCREET MANAGEMENT CONSOLE EXPANDER ---
with st.expander("🛠️ System Console Settings", expanded=False):
    if len(st.session_state.fuel_logs) > 0:
        log_options = [f"#{i+1} | {log['Date']} | {log['Odometer (km)']} km" for i, log in enumerate(st.session_state.fuel_logs)]
        selected_option = st.selectbox("Select Target Registry Block:", log_options)
        
        selected_index = log_options.index(selected_option)
        target_log = st.session_state.fuel_logs[selected_index]
        
        st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#64748B;'>FIELD MODIFICATION ARRAYS:</p>", unsafe_allow_html=True)
        edit_date = st.date_input("Adjust Block Date", value=datetime.strptime(target_log["Date"], "%Y-%m-%d"), key="edit_date_pick")
        edit_odo = st.number_input("Adjust Odometer Reading (km)", min_value=0, value=int(target_log["Odometer (km)"]))
        edit_liters = st.number_input("Adjust Liters Field", min_value=0.0, value=float(target_log["Liters"]), step=0.01)
        edit_cost = st.number_input("Adjust Cost Sheet (₹)", min_value=0.0, value=float(target_log["Cost (₹)"]))
        
        edit_air = st.checkbox("Override Air Status (Checked = Filled)", value=(target_log.get("Air Filled", "No") == "Yes"))
        edit_srv_check = st.checkbox("Override Service Status (Checked = Executed)", value=(target_log.get("Last Service Date", "-") != "-"))
        
        edit_srv_date_str = "-"
        if edit_srv_check:
            current_srv_val = target_log.get("Last Service Date", "-")
            default_srv_date = datetime.today() if current_srv_val == "-" else datetime.strptime(current_srv_val, "%Y-%m-%d")
            edit_srv_date = st.date_input("Adjust Core Service Date", value=default_srv_date, key="edit_srv_pick")
            edit_srv_date_str = edit_srv_date.strftime("%Y-%m-%d")

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            if st.button("💾 Apply Overwrite", use_container_width=True):
                st.session_state.fuel_logs[selected_index] = {
                    "Date": edit_date.strftime("%Y-%m-%d"),
                    "Odometer (km)": edit_odo,
                    "Liters": edit_liters,
                    "Cost (₹)": edit_cost,
                    "Air Filled": "Yes" if edit_air else "No",
                    "Last Service Date": edit_srv_date_str
                }
                st.success("Log block entry overwritten successfully!")
                st.rerun()
        with col_ed2:
            if st.button("🗑️ Purge Block Entry", use_container_width=True):
                st.session_state.fuel_logs.pop(selected_index)
                st.warning("Entry block permanently wiped from database storage.")
                st.rerun()
    else:
        st.caption("No diagnostic entry arrays available for backend manipulation.")