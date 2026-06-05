import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import requests
from google import genai

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

def fetch_from_supabase(table_name):
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/{table_name}?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def commit_to_supabase(table_name, payload):
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/{table_name}", headers=HEADERS, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except Exception:
        return False

def delete_from_supabase(table_name, row_id):
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/{table_name}?id=eq.{row_id}", headers=HEADERS, timeout=10)
        return response.status_code in [200, 204]
    except Exception:
        return False

# Initialize Session State
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "auto_odo" not in st.session_state:
    st.session_state.auto_odo = 0

# --- AUTH PORTAL ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Fleet Gateway Portal")
    gate_mode = st.radio("Choose Gateway Action:", ["Sign-In Existing Operator", "Register New Driver Account"], horizontal=True)
    with st.container(border=True):
        reg_username = st.text_input("Operator Username").strip().lower()
        reg_password = st.text_input("Security Passkey", type="password")
        raw_users = fetch_from_supabase("app_users")
        user_credentials_map = {row["username"]: row["passkey"] for row in raw_users}
        if "mantri" not in user_credentials_map: user_credentials_map["mantri"] = "petrol123"
        
        if gate_mode == "Sign-In Existing Operator":
            if st.button("Authenticate Identity", use_container_width=True, type="primary"):
                if reg_username in user_credentials_map and user_credentials_map[reg_username] == reg_password:
                    st.session_state.logged_in_user = reg_username
                    st.rerun()
        elif gate_mode == "Register New Driver Account":
            if st.button("🚀 Provision New Account", use_container_width=True, type="primary"):
                if commit_to_supabase("app_users", {"username": reg_username, "passkey": reg_password}):
                    st.success("Account provisioned.")
    st.stop()

current_user = st.session_state.logged_in_user
is_admin = (current_user == "mantri")

# --- MAIN INTERFACE ---
tabs = st.tabs(["🚙 My Telemetry Console", "🏆 Global Performance Leaderboard"] + (["🛠️ Global Admin Panel"] if is_admin else []))

with tabs[0]:
    st.title(f"⚡ Welcome, {current_user}")
    if st.sidebar.button("🔒 Secure Sign-Out"):
        st.session_state.logged_in_user = None
        st.rerun()

    raw_cloud_data = fetch_from_supabase("fuel_logs")
    parsed_logs = []
    for row in raw_cloud_data:
        uid = row.get("user_id", "")
        base_user = uid.split(" | ")[0] if " | " in uid else uid
        if base_user == current_user:
            row_copy = row.copy()
            row_copy["Air Checked"] = "Yes" if "Air: Yes" in uid else "No"
            row_copy["Service Cost"] = uid.split('Service Cost: ₹')[1] if "Service Cost: ₹" in uid else "No"
            parsed_logs.append(row_copy)
    
    user_df = pd.DataFrame(parsed_logs)
    
    # --- INTERACTIVE LEDGER ---
    st.markdown("### 📋 Your Personal Log Ledger (Click a row to select Odometer)")
    if not user_df.empty:
        clean_user_df = user_df.sort_values("log_date", ascending=False).reset_index(drop=True)
        event = st.dataframe(clean_user_df[['log_date', 'odometer', 'liters', 'cost', 'Air Checked', 'Service Cost']], 
                             use_container_width=True, on_select="rerun", selection_mode="single-row")
        
        if event.selection.rows:
            st.session_state.auto_odo = int(clean_user_df.iloc[event.selection.rows[0]]['odometer'])
    
    # --- FUEL LOG FORM ---
    st.markdown("### ⛽ Step 2: Verify & Log Fuel Telemetry")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        log_date = col1.date_input("Date", value=datetime.today())
        # The magic line: use auto_odo from selection
        odometer = col2.number_input("Odometer (km)", min_value=0, value=st.session_state.auto_odo, step=1)
        
        liters = col1.number_input("Liters", min_value=0.0, step=0.1)
        price = col2.number_input("Cost (₹)", min_value=0.0, step=10.0)
        
        if st.button("⚡ Commit Entry to Cloud", type="primary"):
            payload = {"user_id": current_user, "log_date": log_date.strftime("%Y-%m-%d"), 
                       "odometer": int(odometer), "liters": float(liters), "cost": float(price)}
            if commit_to_supabase("fuel_logs", payload):
                st.rerun()

with tabs[1]:
    st.title("🏆 Leaderboard")
    # ... (Keep your existing leaderboard logic here)

if is_admin:
    with tabs[2]:
        st.title("🛠️ Admin Panel")
        # ... (Keep your existing admin logic here)
