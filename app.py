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
st.set_page_config(page_title="Smart Car Tracker", page_icon="⚡", layout="centered")

# --- CUSTOM APPLICATION HEADER (MOBILE OPTIMIZED) ---
st.markdown("""
    <div style='background: linear-gradient(135deg, #1E3A8A, #3B82F6); padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; text-align: center; color: white;'>
        <h2 style='margin: 0; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.5px;'>⚡ Smart Car Tracker</h2>
        <p style='margin: 2px 0 0 0; opacity: 0.85; font-size: 0.8rem;'>AI Fuel Analytics & Maintenance Logbook</p>
    </div>
""", unsafe_allow_html=True)

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

# --- 3. PREMIUM METRICS DASHBOARD ---
st.markdown("### 📊 Analytics Summary")
with st.container(border=True):
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Average Fuel Mileage", value=f"{avg_mileage:.2f} km/L")
    with col_m2:
        st.metric(label="Running Cost per KM", value=f"₹ {cost_per_km:.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# --- 4. LIVE AUTOMATED AI BILL SCANNER ---
st.markdown("### 📷 Step 1: Scan Bill")
with st.container(border=True):
    activate_camera = st.checkbox("Toggle to Turn On Scanner Camera", value=False)
    
    scanned_liters = 0.0
    scanned_price = 0.0
    api_key = st.secrets.get("GEMINI_API_KEY")

    if activate_camera:
        uploaded_bill = st.camera_input("Snap a crisp photo of your petrol bill")

        if uploaded_bill is not None:
            img = Image.open(uploaded_bill)
            
            if not api_key:
                st.error("⚠️ App Secret Missing: Please add 'GEMINI_API_KEY' to settings.")
            else:
                with st.spinner("⚡ AI is scanning receipt strings..."):
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
                        
                        st.success(f"🤖 Scanner Captured: {scanned_liters}L | Total Bill: ₹ {scanned_price}")
                    except Exception as e:
                        st.error(f"Error parsing receipt text: {e}")
    else:
        st.caption("🔒 Camera hardware is currently offline.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. VEHICLE LOG ENTRY FORM WITH INTEGRATED CHECKS ---
st.markdown("### ⛽ Step 2: Verify & Log Details")
with st.container(border=True):
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        log_date = st.date_input("Date of Fill-up", value=datetime.today())
        odometer = st.number_input("Current Odometer Reading (km)", min_value=0, step=1)
    with form_col2:
        liters = st.number_input("Liters of Petrol Filled", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
        price = st.number_input("Total Bill Amount (₹)", min_value=0.0, value=scanned_price, step=10.0)
    
    st.markdown("**Additional Checks at Pump:**")
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        air_filled = st.checkbox("💨 Air filled today?", value=False)
    with col_chk2:
        had_service = st.checkbox("🔧 Was vehicle serviced today?", value=False)
    
    service_date_str = "-"
    if had_service:
        service_date = st.date_input("Confirm Service Date", value=datetime.today())
        service_date_str = service_date.strftime("%Y-%m-%d")

    if st.button("Save Entry", use_container_width=True, type="primary"):
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
            st.success("Log added successfully!")
            st.rerun()
        else:
            st.error("Please provide valid data inputs across all fields.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. VISUAL ANALYTICS CHART ---
if len(df) >= 2:
    st.markdown("### 📈 Efficiency Trend (km/L over time)")
    chart_data = df.dropna(subset=['km/L']).set_index('Date')
    st.line_chart(chart_data['km/L'], color="#3B82F6")

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. MOBILE-FRIENDLY EDIT & DELETE PANEL ---
st.markdown("### 🛠️ Step 3: Edit or Delete Old Entries")
with st.container(border=True):
    if len(st.session_state.fuel_logs) > 0:
        log_options = [f"#{i+1} | {log['Date']} | {log['Odometer (km)']} km" for i, log in enumerate(st.session_state.fuel_logs)]
        selected_option = st.selectbox("Select a log entry to modify:", log_options)
        
        selected_index = log_options.index(selected_option)
        target_log = st.session_state.fuel_logs[selected_index]
        
        with st.expander("📝 Modify Selected Entry Details"):
            edit_date = st.date_input("Edit Date", value=datetime.strptime(target_log["Date"], "%Y-%m-%d"))
            edit_odo = st.number_input("Edit Odometer (km)", min_value=0, value=int(target_log["Odometer (km)"]))
            edit_liters = st.number_input("Edit Liters", min_value=0.0, value=float(target_log["Liters"]), step=0.01)
            edit_cost = st.number_input("Edit Cost (₹)", min_value=0.0, value=float(target_log["Cost (₹)"]))
            
            edit_air = st.checkbox("Edit Air Status (Checked = Yes)", value=(target_log.get("Air Filled", "No") == "Yes"))
            edit_srv_check = st.checkbox("Edit Service Status (Checked = Serviced)", value=(target_log.get("Last Service Date", "-") != "-"))
            
            edit_srv_date_str = "-"
            if edit_srv_check:
                current_srv_val = target_log.get("Last Service Date", "-")
                default_srv_date = datetime.today() if current_srv_val == "-" else datetime.strptime(current_srv_val, "%Y-%m-%d")
                edit_srv_date = st.date_input("Adjust Service Date", value=default_srv_date)
                edit_srv_date_str = edit_srv_date.strftime("%Y-%m-%d")

            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                if st.button("💾 Save Changes", use_container_width=True):
                    st.session_state.fuel_logs[selected_index] = {
                        "Date": edit_date.strftime("%Y-%m-%d"),
                        "Odometer (km)": edit_odo,
                        "Liters": edit_liters,
                        "Cost (₹)": edit_cost,
                        "Air Filled": "Yes" if edit_air else "No",
                        "Last Service Date": edit_srv_date_str
                    }
                    st.success("Changes saved!")
                    st.rerun()
            with col_ed2:
                if st.button("🗑️ Delete Entry Permanently", use_container_width=True):
                    st.session_state.fuel_logs.pop(selected_index)
                    st.warning("Entry deleted successfully.")
                    st.rerun()
    else:
        st.info("No logs stored to modify yet.")

# --- 8. HISTORICAL TRANSACTIONS SHEET ---
st.markdown("### 📋 Saved Entries Log")
if len(df) > 0:
    display_df = df.copy()
    if 'km/L' in display_df.columns:
        display_df['km/L'] = display_df['km/L'].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("Your logbook is empty. Use Step 1 & Step 2 above to log your first real fuel receipt!")