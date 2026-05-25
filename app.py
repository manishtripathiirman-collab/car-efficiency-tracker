import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🚗 Car Efficiency Tracker")

# --- 1. INITIALIZE APP MEMORY ---
# We create a temporary memory list inside Streamlit's session state to hold data
if "fuel_logs" not in st.session_state:
    st.session_state.fuel_logs = []

# --- 2. INPUT FORM ---
st.subheader("⛽ Log Petrol Fill-Up")

col1, col2 = st.columns(2)
with col1:
    log_date = st.date_input("Date of Fill-up", value=datetime.today())
    odometer = st.number_input("Current Odometer Reading (km)", min_value=0, step=1)
with col2:
    liters = st.number_input("Liters of Petrol Filled", min_value=0.0, step=0.1)
    price = st.number_input("Total Bill Amount (₹)", min_value=0.0, step=10.0)

# Save Button Logic
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
    else:
        st.error("Please enter valid numbers before saving.")

# --- 3. DISPLAY HISTORICAL TABLE ---
st.markdown("---")
st.subheader("📋 Saved Entries Log")

if len(st.session_state.fuel_logs) > 0:
    df = pd.DataFrame(st.session_state.fuel_logs)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No logs recorded yet. Enter your first fill-up above!")