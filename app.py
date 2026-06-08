import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import requests

# Set up clean mobile-first viewport architecture
st.set_page_config(page_title="EcoSport Team Cockpit", page_icon="⚡", layout="centered")

# --- PREMIUM DASHBOARD CUSTOM THEME INJECTION ---
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
        }
        div.stButton > button:first-child {
            background-color: #ff4b4b !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #ff3333 !important;
            transform: scale(1.01);
        }
        [data-testid="stMetricContainer"] {
            background-color: #1a1f2c;
            border: 1px solid #2d3748;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
    </style>
""", unsafe_allow_html=True)

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

# --- DYNAMIC DEVICE AUTOLOGIN PERSISTENCE LAYER ---
if "logged_in_user" not in st.session_state:
    saved_session = st.query_params.get("operator")
    if saved_session:
        st.session_state.logged_in_user = saved_session
    else:
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
                    st.query_params["operator"] = reg_username
                    st.success(f"Access Granted. Remembering device credentials...")
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
    st.title(f"⚡ Welcome, {current_user.upper()}")
    st.caption(f"Connected Device Securely Stamped | Persistent Session Active")
    
    if st.sidebar.button("🔒 Secure Sign-Out / Forget Me", use_container_width=True):
        st.session_state.logged_in_user = None
        st.query_params.clear()
        st.rerun()

    raw_cloud_data = fetch_from_supabase("fuel_logs")
    
    # Process metadata values stored inside user string parameters safely
    parsed_logs = []
    for row in raw_cloud_data:
        uid = row.get("user_id", "")
        base_user = uid.split(" | ")[0] if " | " in uid else uid
        
        if base_user == current_user:
            row_copy = row.copy()
            row_copy["Air Checked"] = "Yes" if "Air: Yes" in uid else "No"
            row_copy["Full Tank?"] = "Yes" if "Full Tank: Yes" in uid else "No"
            
            if "Service Cost: ₹" in uid:
                try:
                    row_copy["Service Cost"] = f"₹{uid.split('Service Cost: ₹')[1]}"
                except Exception:
                    row_copy["Service Cost"] = "₹0.00"
            else:
                row_copy["Service Cost"] = "No"
                
            parsed_logs.append(row_copy)
