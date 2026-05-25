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

# --- VISUAL HERO BANNER (INTEGRATED ECOSPORT THEME) ---
# This asset creates the "premium cockpit" feel by replacing standard headers
st.image(
    "https://raw.githubusercontent.com/vmantri/car-dashboard-asset/main/mantri_ecosport_hero.png", 
    use_container_width=True
)

st.markdown("<br>", unsafe_allow_html=True)

# --- 1. INITIALIZE APP MEMORY ---
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = []

# Build working DataFrame from session data
df = pd.DataFrame(st.session_state.fuel_logs)

# --- 2. THE ROLLING MATH ENGINE ---
if len(df) >= 2:
    # Sort and calculate rolling distance
    df = df.sort_values("Odometer (km)").reset_index(drop=True)
    df['Distance Driven (km)'] = df['Odometer (km)'].diff()
    df['km/L'] = df['Distance Driven (km)'] / df['Liters']
    
    # Life-to-date metrics
    total_tracked_km = df['Distance Driven (km)'].sum()
    total_money_spent = df['Cost (₹)'].sum()
    
    # Calculate averages
    avg_mileage = total_tracked_km / df['Liters'].iloc[1:].sum()
    cost_per_km = total_money_spent / total_tracked_km
else:
    avg_mileage = 0.0
    cost_per_km = 0.0

# --- 3. PREMIUM ANALYTICS MATRIX ---
st.markdown("### 📊 Performance Analytics")
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Average Fuel Mileage", value=f"{avg_mileage:.2f} km/L")
    
with col2:
    st.metric(label="Running Cost", value=f"₹ {cost_per_km:.2f} / km")

st.markdown("<br>", unsafe_allow_html=True)

# --- 4. LIVE AUTOMATED AI BILL SCANNER (THE LENS) ---
st.markdown("### 📷 Phase 1: Receipt Optical Intake")
with st.container(border=True):
    # Camera toggle lock for security/lean layout
    activate_camera = st.checkbox("Initialize AI Scanner Camera", value=False)
    
    # Placeholders for AI results
    scanned_liters = 0.0
    scanned_price = 0.0
    
    # Get secret key from Streamlit Cloud dashboard settings
    api_key = st.secrets.get("GEMINI_API_KEY")

    if activate_camera:
        uploaded_bill = st.camera_input("Position fuel bill inside guidelines")

        if uploaded_bill is not None:
            img = Image.open(uploaded_bill)
            
            if not api_key:
                st.error("⚠️ System Secret Missing: Add 'GEMINI_API_KEY' to settings.")
            else:
                with st.spinner("⚡ AI is deciphering receipt matrix..."):
                    try:
                        # Initialize Gemini Client and prompt
                        client = genai.Client(api_key=api_key)
                        prompt = """
                        Examine this fuel receipt image carefully. Extract total volume in liters and total cost in Rupees. 
                        Return output strictly formatted as JSON object with keys "liters" and "total_cost".
                        """
                        # Generate content (image + prompt)
                        response = client.models.generate_content(
                            model='gemini-2.0-flash-exp',
                            contents=[img, prompt]
                        )
                        
                        # Parse JSON response
                        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(cleaned_text)
                        
                        # Populate data fields
                        scanned_liters = float(data.get("liters", 0.0))
                        scanned_price = float(data.get("total_cost", 0.0))
                        
                        st.success(f"🤖 Scanner Captured: {scanned_liters}L | Total Bill: ₹ {scanned_price}")
                    
                    except Exception as e:
                        st.error(f"System Error parsing receipt: {e}")
    else:
        st.caption("🔒 Scanner telemetry offline.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. VEHICLE LOG ENTRY FORM (THE MATRIX) ---
st.markdown("### ⛽ Phase 2: Log Entry Matrix")
with st.container(border=True):
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        log_date = st.date_input("Log Date Stamping", value=datetime.today())
        odometer = st.number_input("Current Odometer Track (km)", min_value=0, step=1)
    with form_col2:
        # These are dynamically filled by the AI scanner results
        liters = st.number_input("Fuel Volume Infused (Liters)", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
        price = st.number_input("Total Transaction Cost (₹)", min_value=0.0, value=scanned_price, step=10.0)
    
    if st.button("Save Entry", use_container_width=True, type="primary"):
        # Logic gate check
        if odometer > 0 and liters > 0 and price > 0:
            # Create data dictionary
            new_entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "Odometer (km)": odometer,
                "Liters": liters,
                "Cost (₹)": price,
            }
            # Commit to session memory
            st.session_state.fuel_logs.append(new_entry)
            st.success("Log compiled into the database matrix!")
            st.rerun() # Refresh layout to show math update
        else:
            st.error("Please provide valid readings across all four telemetry fields.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. VISUAL ANALYTICS CURVE ---
if len(df) >= 2:
    st.markdown("### 📈 Efficiency Trend Velocity")
    # Plot Km/L over time
    chart_data = df.set_index('Date')
    st.line_chart(chart_data['km/L'], color="#3B82F6")
    st.markdown("<br>", unsafe_allow_html=True)

# --- 7. HISTORICAL TRANSACTION SHEET ---
st.markdown("### 📋 Historic Ledger Sheets")
if len(df) > 0:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("The master logbook ledger is completely vacant. Input logs to initialize history.")

st.markdown("<br><br><br>", unsafe_allow_html=True)

# --- THE SIGNATURE (DISCREET & LEAN) ---
# A simplified, non-descript signature dropped to the bottom
st.markdown("<div style='text-align: right; opacity: 0.5; font-size: 0.7rem;'>by mantri | v.09.26</div>", unsafe_allow_html=True)