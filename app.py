import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🚗 Car Efficiency Tracker")

# --- 1. INITIALIZE APP MEMORY ---
if "fuel_logs" not in st.session_state:
    # Starting with two realistic dummy entries so you can see the math work instantly!
    st.session_state.fuel_logs = [
        {"Date": "2026-05-01", "Odometer (km)": 45000, "Liters": 40.0, "Cost (₹)": 3800.0},
        {"Date": "2026-05-12", "Odometer (km)": 45550, "Liters": 42.5, "Cost (₹)": 4030.0},
    ]

# Convert our memory bank into a structured spreadsheet table (DataFrame)
df = pd.DataFrame(st.session_state.fuel_logs)

# --- 2. THE ROLLING MATH ENGINE ---
if len(df) >= 2:
    # Sort by odometer to keep calculation chronological
    df = df.sort_values("Odometer (km)").reset_index(drop=True)
    
    # Math Trick: .diff() subtracts the previous row value from the current row value
    df['Distance Driven (km)'] = df['Odometer (km)'].diff()
    
    # Calculate Mileage: Distance divided by liters filled
    df['km/L'] = df['Distance Driven (km)'] / df['Liters']
    
    # Global Lifetime Totals
    total_tracked_km = df['Distance Driven (km)'].sum()
    total_money_spent = df['Cost (₹)'].sum()
    
    # Final Averages to Display
    avg_mileage = total_tracked_km / df['Liters'].iloc[1:].sum()
    cost_per_km = total_money_spent / total_tracked_km
else:
    # Fallback values if the user clears data or only has 1 log entry
    avg_mileage = 0.0
    cost_per_km = 0.0

# --- 3. DISPLAY PERFORMANCE METRIC CARDS ---
st.markdown("### 📊 Live Averages")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Average Fuel Mileage", value=f"{avg_mileage:.2f} km/L")
with col_m2:
    st.metric(label="Running Cost per KM", value=f"₹ {cost_per_km:.2f}")

st.markdown("---")

# --- 4. DATA INPUT FORM ---
st.subheader("⛽ Log New Petrol Fill-Up")
form_col1, form_col2 = st.columns(2)

with form_col1:
    log_date = st.date_input("Date of Fill-up", value=datetime.today())
    odometer = st.number_input("Current Odometer Reading (km)", min_value=0, step=1)

with form_col2:
    liters = st.number_input("Liters of Petrol Filled", min_value=0.0, step=0.1)
    price = st.number_input("Total Bill Amount (₹)", min_value=0.0, step=10.0)

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
        st.rerun() # This reloads the page instantly to show updated math!
    else:
        st.error("Please enter valid numbers before saving.")

# --- 5. DISPLAY THE HISTORICAL LOG TABLE ---
st.markdown("---")
st.subheader("📋 Saved Entries Log")
st.dataframe(df, use_container_width=True, hide_index=True)