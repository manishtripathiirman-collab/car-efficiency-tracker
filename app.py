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
                st.error("⚠️ App Secret Missing: Please add 'GEMINI_API_KEY' to your settings.")
            else:
                with st.spinner("⚡ AI is scanning receipt strings..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        prompt = """
                        Examine this fuel receipt image carefully. Extract the total volume of fuel/petrol filled in liters and the absolute total cost paid in Rupees. 
                        Return the output strictly formatted as a single JSON object containing only keys "liters" and "total_cost".
                        """
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=[img, prompt])
                        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(cleaned_text)
                        
                        scanned_liters = float(data.get("liters", 0.0))
                        scanned_price = float(data.get("total_cost", 0.0))
                        
                        st.success(f"🤖 Scanner Success! Captured: {scanned_liters}L | Total Bill: ₹ {scanned_price}")
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
        lit