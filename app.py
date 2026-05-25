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
    # Always keep rows ordered by odometer progression for accurate rolling calculations
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

# --- 4. LIVE AUTOMATED AI BILL SCANNER ---
st.subheader("📷 Step 1: Scan Bill")

uploaded_bill = st.camera_input("Snap a crisp photo of your petrol bill")

scanned_liters = 0.0
scanned_price = 0.0

api_key = st.secrets.get("GEMINI_API_KEY")

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

# --- 6. INTERACTIVE EDIT SHEET & LOG HISTORY ---
st.markdown("---")
st.subheader("📋 Saved Entries Log (Tap cells to Edit/Delete)")

# We present a highly interactive spreadsheet view to the user
edited_df = st.data_editor(
    df, 
    use_container_width=True, 
    num_rows="dynamic", # Enables row insertion and deletion buttons seamlessly
    disabled=["Distance Driven (km)", "km/L"], # Protects mathematical engines from overrides
    column_config={
        "Date": st.column_config.TextColumn("Date"),
        "Odometer (km)": st.column_config.NumberColumn("Odometer (km)", format="%d"),
        "Liters": st.column_config.NumberColumn("Liters", format="%.2f"),
        "Cost (₹)": st.column_config.NumberColumn("Cost (₹)", format="₹ %d")
    }
)

# If modifications are intercepted inside the interactive worksheet sheet layout
if not edited_df.equals(df):
    # Strip operational columns out to clean master logs array tracking structure
    cleaned_export = edited_df[["Date", "Odometer (km)", "Liters", "Cost (₹)"]]
    st.session_state.fuel_logs = cleaned_export.to_dict(orient="records")
    st.rerun()