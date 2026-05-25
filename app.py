import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import os

# We import the official Google GenAI library
try:
    from google import genai
except ImportError:
    st.error("Please run 'pip install google-genai' in your terminal!")

st.title("🚗 Smart Car Tracker")

# --- 1. MEMORY STORAGE ---
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = [
        {"Date": "2026-05-01", "Odometer (km)": 45000, "Liters": 40.0, "Cost (₹)": 3800.0},
        {"Date": "2026-05-12", "Odometer (km)": 45550, "Liters": 42.5, "Cost (₹)": 4030.0},
    ]

df = pd.DataFrame(st.session_state.fuel_logs)

# --- 2. ROLLING MATH ENGINE ---
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

# --- 3. METRICS ---
st.markdown("### 📊 Live Averages")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Average Fuel Mileage", value=f"{avg_mileage:.2f} km/L")
with col_m2:
    st.metric(label="Running Cost per KM", value=f"₹ {cost_per_km:.2f}")

st.markdown("---")

# --- 4. LIVE AI BILL SCANNER ENGINE ---
st.subheader("📷 Step 1: Scan Bill")

# Create a place to paste your free Google API Key safely right in the app UI
api_key = st.text_input("Paste your Gemini API Key here:", type="password")
st.caption("Get a free key instantly from Google AI Studio if you don't have one.")

uploaded_bill = st.file_input("Take a photo or upload your petrol receipt bill", type=["jpg", "jpeg", "png"])

scanned_liters = 0.0
scanned_price = 0.0

if uploaded_bill is not None:
    img = Image.open(uploaded_bill)
    st.image(img, caption="Receipt Preview", width=200)
    
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API Key above to read this bill.")
    else:
        st.info("⚡ AI is reading your receipt lines...")
        try:
            # Initialize the live Google Vision client
            client = genai.Client(api_key=api_key)
            
            # Instruct the AI to find specific data points and format them cleanly as JSON
            prompt = """
            Look at this fuel receipt image. Extract the total volume of fuel/petrol filled in liters and the total bill amount paid in Rupees. 
            Return the output strictly as a clean JSON object with keys "liters" and "total_cost". 
            Example output format: {"liters": 35.4, "total_cost": 3400.0}
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[img, prompt]
            )
            
            # Clean up and parse the text answer back into numbers
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            
            scanned_liters = float(data.get("liters", 0.0))
            scanned_price = float(data.get("total_cost", 0.0))
            
            st.success(f"🤖 Scanner Success! Found: {scanned_liters}L | ₹ {scanned_price}")
            
        except Exception as e:
            st.error(f"Error reading bill: {e}")

st.markdown("---")

# --- 5. LOGGING FORM ---
st.subheader("⛽ Step 2: Verify & Log Details")
form_col1, form_col2 = st.columns(2)

with form_col1:
    log_date = st.date_input("Date of Fill-up", value=datetime.today())
    odometer = st.number_input("Current Odometer Reading (km)", min_value=0, step=1)

with form_col2:
    # Form fields automatically latch onto whatever the AI model extracted!
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
        st.success("Entry recorded successfully!")
        st.rerun()
    else:
        st.error("Please enter valid numbers before saving.")

# --- 6. HISTORY LOG ---
st.markdown("---")
st.subheader("📋 Saved Entries Log")
st.dataframe(df, use_container_width=True, hide_index=True)