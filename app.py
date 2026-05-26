import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import requests

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
    """Pulls raw logs from designated cloud tables safely"""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/{table_name}?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def commit_to_supabase(table_name, payload):
    """Inserts a fresh data payload row directly into a cloud table"""
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/{table_name}", headers=HEADERS, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except Exception:
        return False

def delete_from_supabase(table_name, row_id):
    """Removes a row from the database using its unique identifier ID"""
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/{table_name}?id=eq.{row_id}", headers=HEADERS, timeout=10)
        return response.status_code in [200, 204]
    except Exception:
        return False

# --- DYNAMIC MULTI-USER IDENTITY PORTAL ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("🔐 Fleet Gateway Portal")
    st.caption("Sign in to your console or provision a new user registry record.")
    
    gate_mode = st.radio("Choose Gateway Action:", ["Sign-In Existing Operator", "Register New Driver Account"], horizontal=True)
    
    with st.container(border=True):
        reg_username = st.text_input("Operator Username").strip().lower()
        reg_password = st.text_input("Security Passkey", type="password")
        
        raw_users = fetch_from_supabase("app_users")
        user_credentials_map = {row["username"]: row["passkey"] for row in raw_users}
        
        if "mantri" not in user_credentials_map:
            user_credentials_map["mantri"] = "petrol123"
        
        if gate_mode == "Sign-In Existing Operator":
            if st.button("Authenticate Identity", use_container_width=True, type="primary"):
                if not reg_username or not reg_password:
                    st.warning("Please complete both access fields.")
                elif reg_username in user_credentials_map and user_credentials_map[reg_username] == reg_password:
                    st.session_state.logged_in_user = reg_username
                    st.success(f"Access Granted. Welcome back.")
                    st.rerun()
                else:
                    st.error("Authentication Failure: Invalid credentials.")
                    
        elif gate_mode == "Register New Driver Account":
            st.caption("⚠️ Your password will be saved securely to your cloud database.")
            if st.button("🚀 Provision New Account", use_container_width=True, type="primary"):
                if len(reg_username) < 3 or len(reg_password) < 4:
                    st.error("Account Policy: Username must be ≥3 characters, Passkey ≥4 characters.")
                elif reg_username in user_credentials_map:
                    st.error("Registry Collision: This username is already claimed.")
                else:
                    user_payload = {"username": reg_username, "passkey": reg_password}
                    if commit_to_supabase("app_users", user_payload):
                        st.success(f"Success! Account '{reg_username}' provisioned. Switch to 'Sign-In' to log in.")
                    else:
                        st.error("Database error connecting to storage vault.")
                        
    st.stop()

current_user = st.session_state.logged_in_user
is_admin = (current_user == "mantri")

# --- TOP INTERACTIVE NAVIGATION WRAPPER ---
tabs_list = ["🚙 My Telemetry Console", "🏆 Global Performance Leaderboard"]
if is_admin:
    tabs_list.append("🛠️ Global Admin Panel")

tabs = st.tabs(tabs_list)
menu_tab = tabs[0]
leaderboard_tab = tabs[1]
admin_tab = tabs[2] if is_admin else None

# --- TAB 1: THE CORE INDIVIDUAL DRIVER CONSOLE ---
if menu_tab:
    st.title(f"⚡ Welcome, {current_user}")
    st.caption(f"Secure Workspace Session Active | Connected to Cloud Ledger")
    
    if st.sidebar.button("🔒 Secure Sign-Out", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

    raw_cloud_data = fetch_from_supabase("fuel_logs")
    all_df = pd.DataFrame(raw_cloud_data)
    
    if not all_df.empty:
        user_df = all_df[all_df['user_id'] == current_user].copy()
    else:
        user_df = pd.DataFrame()

    # Math Calculation Engine
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

    st.markdown("### 📊 Your Performance Analytics")
    with st.container(border=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="Your Average Mileage", value=f"{avg_mileage:.2f} km/L")
        with col_m2:
            st.metric(label="Your Running Cost", value=f"₹ {cost_per_km:.2f} / km")

    # --- LIVE ADJACENT SCANNER & ATTACHMENT PORTS ---
    st.markdown("### 📷 Step 1: Scan Bill via Vision AI")
    scanned_liters = 0.0
    scanned_price = 0.0
    target_bill_file = None
    
    with st.container(border=True):
        cam_col, upload_col = st.columns(2)
        
        with cam_col:
            st.markdown("**Option A: Camera Scanner**")
            # Toggles added back to control feed explicitly
            activate_camera = st.checkbox("Turn On Camera Hardware", value=False)
            if activate_camera:
                camera