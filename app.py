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

st.set_page_config(page_title="Smart Car Tracker", page_icon="🚗", layout="centered")
st.title("🚗 Smart Car Tracker")

# --- 1. INITIALIZE APP MEMORY ---
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = [
        {"Date": "2026-05-01", "Odometer (km)": 45000, "Liters": 40.0, "Cost (₹)": 3800.0},
        {"Date": "2026-05-12", "Odometer (km)": 45550, "Liters": 42.5, "Cost (₹)": 4030.0},
    ]

# Build our working DataFrame from memory
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

# --- 3. PERFORMANCE METRICS DASHBOARD ---
st.markdown("### 📊 Live Averages")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Average Fuel Mileage", value=f"{avg_mileage:.2f} km/L")
with col_m2:
    st.metric(label="Running Cost per KM", value=f"₹ {cost_per_km:.2f}")

st.markdown("---")

# --- 4. LIVE AUTOMATED AI BILL SCANNER (FIXED HARDWARE TRIGGER) ---
st.subheader("📷 Step 1: Scan Bill")

# HARDWARE GATE: A clean checkbox that acts as a strict power switch for the camera hardware
activate_camera = st.checkbox("Toggle to Turn On Scanner Camera", value=False)

scanned_liters = 0.0
scanned_price = 0.0

api_key = st.secrets.get("GEMINI_API_KEY")

# The camera code will now remain completely non-existent in the browser until checked
if activate_camera:
    uploaded_bill = st.camera_input("Snap a crisp photo of your petrol bill")

    if uploaded_bill is not None:
        img = Image.open(uploaded_bill)
        
        if not api_key:
            st.error("⚠️ App Secret Missing: Please add 'GEMINI_API_KEY' to your Streamlit Cloud Secrets settings tab.")
        else:
            st.info("⚡ AI is scanning receipt strings...")
            try:
                client = genai.Client(api_key=api_key)
                
                prompt = """
                Examine this fuel receipt image carefully. Extract the total volume of fuel/petrol filled in liters and the absolute total cost paid in Rupees. 
                Return the output strictly formatted as a single JSON object containing only keys "liters" and "total_cost".
                Example output format: {"liters": 38.5, "total_cost": 3650.0}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[img, prompt]
                )
                
                cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_text)
                
                scanned_liters = float(data.get("liters", 0.0))
                scanned_price = float(data.get("total_cost", 0.0))
                
                st.success(f"🤖 Scanner Success! Captured: {scanned_liters}L | Total Bill: ₹ {scanned_price}")
                
            except Exception as e:
                st.error(f"Error parsing receipt text: {e}")
else:
    st.caption("🔒 Camera hardware is currently offline and disconnected.")

st.markdown("---")

# --- 5. VEHICLE LOG ENTRY FORM ---
st.subheader("⛽ Step 2: Verify & Log Details")
form_col1, form_col2 = st.columns(2)

with form_col1:
    log_date = st.date_input("Date of Fill-up", value=datetime.today())
    odometer = st.number_input("Current Odometer Reading (km)", min_value=0, step=1)

with form_col2:
    liters = st.number_input("Liters of Petrol Filled", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
    price = st.number_input("Total Bill Amount (₹)", min_value=0.0, value=scanned_price, step=10.0)

if st.button("Save Entry", use_container_width=True):
    if odometer > 0 and liters > 0 and price > 0:
        new_entry = {
            "Date": log_date.strftime("%Y-%m-%d"),
            "Odometer (km)": odometer,
            "Liters": liters,
            "Cost (₹)": price
        }
        st.session_state.fuel_logs.append(new_entry)
        st.success("Log added successfully!")
        st.rerun()
    else:
        st.error("Please provide valid data inputs across all fields before compiling your log entry.")

# --- 6. MOBILE-FRIENDLY EDIT & DELETE PANEL ---
st.markdown("---")
st.subheader("🛠️ Step 3: Edit or Delete Old Entries")

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
        
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            if st.button("💾 Save Changes", use_container_width=True):
                st.session_state.fuel_logs[selected_index] = {
                    "Date": edit_date.strftime("%Y-%m-%d"),
                    "Odometer (km)": edit_odo,
                    "Liters": edit_liters,
                    "Cost (₹)": edit_cost
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

# --- 7. HISTORICAL TRANSACTIONS SHEET (READ-ONLY VIEW) ---
st.markdown("---")
st.subheader("📋 Saved Entries Log")
st.dataframe(df, use_container_width=True, hide_index=True)