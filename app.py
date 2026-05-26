import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import requests

# Ensure the Google GenAI library is present
try:
    from google import genai
except ImportError:
    st.error("Please ensure 'google-genai' is listed in your requirements.txt file!")

# Set up clean mobile-first viewport architecture
st.set_page_config(page_title="EcoSport Team Cockpit", page_icon="⚡", layout="centered")

# --- INITIALIZE CONNECTION TO SUPABASE VIA REST API ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def fetch_logs_from_cloud():
    """Pulls all raw data from Supabase cloud ledger safely"""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/fuel_logs?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def save_log_to_cloud(payload):
    """Commits a brand new telemetry row directly into the database row matrix"""
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/fuel_logs", headers=HEADERS, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except Exception:
        return False

# --- USER PASS GATEWAY (SIMPLE SECURITY MATRIX) ---
# Hardcoded credentials for your team - you can add more friends here anytime!
USER_DB = {
    "mantri": "petrol123",
    "abhishek": "diesel456",
    "rahul": "cng789"
}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("🔐 Fleet Gateway Login")
    st.caption("Access restricted to authorized vehicle operators.")
    
    with st.container(border=True):
        username_input = st.text_input("Operator Username").strip().lower()
        password_input = st.text_input("Security Passkey", type="password")
        
        if st.button("Authenticate Identity", use_container_width=True, type="primary"):
            if username_input in USER_DB and USER_DB[username_input] == password_input:
                st.session_state.logged_in_user = username_input
                st.success(f"Access Granted. Welcome back, {username_input}.")
                st.rerun()
            else:
                st.error("Authentication Failure: Invalid username or passkey.")
    st.stop() # Halts app rendering here until user passes login screen

# Track current session context
current_user = st.session_state.logged_in_user

# --- TOP INTERACTIVE NAVIGATION WRAPPER ---
menu_tab, leaderboard_tab = st.tabs(["🚙 My Telemetry Console", "🏆 Global Performance Leaderboard"])

# --- TAB 1: THE CORE INDIVIDUAL DRIVER CONSOLE ---
if menu_tab:
    st.title(f"⚡ Welcome, {current_user}")
    st.caption(f"Secure Workspace Session Active | Connected to Cloud Ledger")
    
    # Logout action trigger link
    if st.sidebar.button("🔒 Secure Sign-Out", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

    # Pull latest cloud matrix data
    raw_cloud_data = fetch_logs_from_cloud()
    all_df = pd.DataFrame(raw_cloud_data)
    
    # ISOLATION GATEWAY: Filter data strictly for current active operator session
    if not all_df.empty:
        user_df = all_df[all_df['user_id'] == current_user].copy()
    else:
        user_df = pd.DataFrame()

    # --- INDIVIDUAL THE ROLLING MATH ENGINE ---
    if len(user_df) >= 2:
        user_df = user_df.sort_values("odometer").reset_index(drop=True)
        user_df['distance_driven'] = user_df['odometer'].diff()
        user_df['km_l'] = user_df['distance_driven'] / user_df['liters']
        
        total_tracked_km = user_df['distance_driven'].sum()
        total_money_spent = user_df['cost'].sum()
        
        avg_mileage = total_tracked_km / user_df['liters'].iloc[1:].sum()
        cost_per_km = total_money_spent / total_tracked_km
    else:
        avg_mileage, cost_per_km = 0.0, 0.0

    # --- MAIN SCREEN METRIC CARDS ---
    st.markdown("### 📊 Your Performance Analytics")
    with st.container(border=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="Your Average Mileage", value=f"{avg_mileage:.2f} km/L")
        with col_m2:
            st.metric(label="Your Running Cost", value=f"₹ {cost_per_km:.2f} / km")

    # --- LIVE AUTOMATED AI BILL SCANNER ---
    st.markdown("### 📷 Step 1: Scan Bill via Vision AI")
    scanned_liters = 0.0
    scanned_price = 0.0
    
    with st.container(border=True):
        activate_camera = st.checkbox("Initialize AI Scanner Camera", value=False)
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
            st.caption("🔒 Scanner telemetry offline.")

    # --- TELEMETRY FILL FORM ---
    st.markdown("### ⛽ Step 2: Verify & Log Fuel Telemetry")
    with st.container(border=True):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            log_date = st.date_input("Transaction Date Stamping", value=datetime.today())
            odometer = st.number_input("Odometer Tracker (km)", min_value=0, step=1)
        with form_col2:
            # Dynamically pre-filled if the scanner picked up text data
            liters = st.number_input("Infused Volume (Liters)", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
            price = st.number_input("Transaction Total Value (₹)", min_value=0.0, value=scanned_price, step=10.0)
        
        if st.button("⚡ Commit Entry to Cloud Matrix", use_container_width=True, type="primary"):
            if odometer > 0 and liters > 0 and price > 0:
                # Package record dictionary with hidden user_id stamp!
                new_entry_payload = {
                    "user_id": current_user, 
                    "log_date": log_date.strftime("%Y-%m-%d"),
                    "odometer": int(odometer),
                    "liters": float(liters),
                    "cost": float(price)
                }
                if save_log_to_cloud(new_entry_payload):
                    st.success("Log safely synced to permanent cloud servers database!")
                    st.rerun()
                else:
                    st.error("Network Error: Cloud connection timeout. Try again.")
            else:
                st.error("Validation Halt: Readings must be set higher than zero.")

    # --- HISTORICAL TRANSACTIONS RECORD SHEET ---
    st.markdown("### 📋 Your Personal Log Ledger")
    if not user_df.empty:
        clean_user_df = user_df.sort_values("log_date", ascending=False)[['log_date', 'odometer', 'liters', 'cost']]
        st.dataframe(clean_user_df, use_container_width=True, hide_index=True)
    else:
        st.info("Your individual garage registry sheet is currently vacant.")

# --- TAB 2: GLOBAL LEADERBOARD STANDINGS ---
with leaderboard_tab:
    st.title("🏆 Workspace Efficiency Standings")
    st.caption("Rankings calculated globally via Lifetime Average Mileage.")
    
    raw_cloud_data = fetch_logs_from_cloud()
    
    if raw_cloud_data:
        master_df = pd.DataFrame(raw_cloud_data)
        leaderboard_records = []
        
        # Loop through each individual user independently to calculate global standings
        for user in master_df['user_id'].unique():
            sub_df = master_df[master_df['user_id'] == user].sort_values("odometer").reset_index(drop=True)
            
            if len(sub_df) >= 2:
                sub_df['dist'] = sub_df['odometer'].diff()
                total_km = sub_df['dist'].sum()
                total_liters = sub_df['liters'].iloc[1:].sum()
                
                if total_liters > 0:
                    lifetime_avg = total_km / total_liters
                    leaderboard_records.append({
                        "Driver": f"👤 {user}",
                        "Lifetime Average Mileage": f"{lifetime_avg:.2f} km/L",
                        "Sort_Val": lifetime_avg
                    })
        
        if leaderboard_records:
            final_leaderboard = pd.DataFrame(leaderboard_records).sort_values("Sort_Val", ascending=False).drop(columns=["Sort_Val"])
            st.dataframe(final_leaderboard, use_container_width=True, hide_index=True)
        else:
            st.info("Insufficient system logs globally to render tournament tables yet.")
    else:
        st.info("No logs present across cloud servers.")

# Non-descript master developer signature flag at the base
st.markdown("<br><br><div style='text-align: center; opacity: 0.2; font-size: 0.7rem;'>by mantri | core pipeline matrix v2.6</div>", unsafe_allow_html=True)