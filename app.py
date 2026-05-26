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
        
        # Super-admin default failsafe configuration
        if "mantri" not in user_credentials_map:
            user_credentials_map