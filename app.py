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
        /* Main application container styling */
        .stApp {
            background-color: #0e1117;
        }
        /* Custom styling for primary action buttons */
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
        /* Style for metric cards background */
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

# --- FIXED AUTOLOGIN PERSISTENCE LAYER ---
# Using streamlit query parameters to act as a permanent local device session cookie
if "logged_in_user" not in st.session_state:
    # Check if a saved operator tag is already written to the browser tab query string
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
                    # Write the session cookie token directly to the browser storage link parameters
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
    
    # Sign-out function completely flushes device cache rules parameters
    if st.sidebar.button("🔒 Secure Sign-Out / Forget Me", use_container_width=True):
        st.session_state.logged_in_user = None
        st.query_params.clear()
        st.rerun()

    raw_cloud_data = fetch_from_supabase("fuel_logs")
    
    parsed_logs = []
    for row in raw_cloud_data:
        uid = row.get("user_id", "")
        base_user = uid.split(" | ")[0] if " | " in uid else uid
        
        if base_user == current_user:
            row_copy = row.copy()
            row_copy["Air Checked"] = "Yes" if "Air: Yes" in uid else "No"
            
            if "Service Cost: ₹" in uid:
                try:
                    row_copy["Service Cost"] = f"₹{uid.split('Service Cost: ₹')[1]}"
                except Exception:
                    row_copy["Service Cost"] = "₹0.00"
            else:
                row_copy["Service Cost"] = "No"
                
            parsed_logs.append(row_copy)
            
    user_df = pd.DataFrame(parsed_logs)

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
    with st.container():
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="📊 Your Average Mileage", value=f"{avg_mileage:.2f} km/L")
        with col_m2:
            st.metric(label="💸 Your Running Cost", value=f"₹ {cost_per_km:.2f} / km")

    # --- LIVE ADJACENT SCANNER & ATTACHMENT PORTS ---
    st.markdown("### 📷 Step 1: Scan Bill via Vision AI")
    scanned_liters = 0.0
    scanned_price = 0.0
    target_bill_file = None
    
    with st.container(border=True):
        cam_col, upload_col = st.columns(2, gap="small")
        
        with cam_col:
            st.markdown("**Option A: Camera Scanner**")
            activate_camera = st.checkbox("Turn On Camera Hardware", value=False)
            if activate_camera:
                camera_snap = st.camera_input("Take live photo of receipt")
                if camera_snap:
                    target_bill_file = camera_snap
                
        with upload_col:
            st.markdown("**Option B: Document Upload**")
            activate_upload = st.checkbox("Turn On File Attachment", value=False)
            if activate_upload:
                file_upload = st.file_uploader("Upload receipt image copy", type=["png", "jpg", "jpeg"])
                if file_upload:
                    target_bill_file = file_upload

        # Process through Gemini API
        if target_bill_file is not None:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if not api_key:
                st.error("⚠️ App Secret Missing: Please add 'GEMINI_API_KEY' to settings.")
            else:
                with st.spinner("⚡ AI is scanning document strings..."):
                    try:
                        img = Image.open(target_bill_file)
                        from google import genai
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
                        
                        st.success(f"🤖 AI Scanner Captured: {scanned_liters}L | Total Bill: ₹ {scanned_price}")
                    except Exception as e:
                        st.error(f"Error parsing document text: {e}")

    # --- TELEMETRY FILL FORM WITH RESTORED MAINTENANCE INPUTS ---
    st.markdown("### ⛽ Step 2: Verify & Log Fuel Telemetry")
    with st.container(border=True):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            log_date = st.date_input("Transaction Date Stamping", value=datetime.today())
            odometer = st.number_input("Odometer Tracker (km)", min_value=0, step=1)
        with form_col2:
            liters = st.number_input("Infused Volume (Liters)", min_value=0.0, value=scanned_liters, step=0.1, format="%.2f")
            price = st.number_input("Transaction Total Value (₹)", min_value=0.0, value=scanned_price, step=10.0)
        
        st.markdown("---")
        st.markdown("**🛠️ Additional Maintenance Trackers**")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            air_checked = st.radio("Air Pressure Calibrated?", ["No", "Yes"], horizontal=True)
        with m_col2:
            service_done = st.radio("General Vehicle Service Carried Out?", ["No", "Yes"], horizontal=True)
        
        service_cost = 0.0
        if service_done == "Yes":
            service_cost = st.number_input("Enter Service Invoice Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
        
        if st.button("⚡ Commit Entry to Cloud Matrix", use_container_width=True, type="primary"):
            if odometer > 0 and liters > 0 and price > 0:
                notes_stamp = f" | Air: {air_checked}"
                if service_done == "Yes":
                    notes_stamp += f" | Service Cost: ₹{service_cost:.2f}"
                
                new_entry_payload = {
                    "user_id": f"{current_user}{notes_stamp}", 
                    "log_date": log_date.strftime("%Y-%m-%d"),
                    "odometer": int(odometer),
                    "liters": float(liters),
                    "cost": float(price)
                }
                if commit_to_supabase("fuel_logs", new_entry_payload):
                    st.success("Log safely synced to permanent cloud servers database!")
                    st.rerun()
                else:
                    st.error("Network Error: Cloud connection timeout.")
            else:
                st.error("Validation Halt: Readings must be set higher than zero.")

    # --- HISTORICAL TRANSACTIONS LEDGER DISPLAY ---
    st.markdown("### 📋 Your Personal Log Ledger")
    if not user_df.empty:
        clean_user_df = user_df.sort_values("log_date", ascending=False)
        st.dataframe(clean_user_df[['log_date', 'odometer', 'liters', 'cost', 'Air Checked', 'Service Cost']], use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ Delete/Remove a Log Record"):
            row_to_delete = st.selectbox(
                "Select one of your log entries to delete permanently:",
                options=clean_user_df.to_dict(orient="records"),
                format_func=lambda x: f"Date: {x['log_date']} | Odo: {x['odometer']} km | Cost: ₹{x['cost']}"
            )
            if st.button("Confirm Deletion from Cloud", type="secondary", use_container_width=True):
                if delete_from_supabase("fuel_logs", row_to_delete["id"]):
                    st.success("Entry successfully removed from your personal ledger.")
                    st.rerun()
                else:
                    st.error("Error executing row delete instruction.")
    else:
        st.info("Your individual garage registry sheet is currently vacant.")

# --- TAB 2: GLOBAL LEADERBOARD STANDINGS ---
with leaderboard_tab:
    st.title("🏆 Workspace Efficiency Standings")
    st.caption("Rankings calculated globally via Lifetime Average Mileage.")
    
    raw_cloud_data = fetch_from_supabase("fuel_logs")
    if raw_cloud_data:
        leaderboard_records = []
        parsed_all = []
        for r in raw_cloud_data:
            uid = r.get("user_id", "")
            base_user = uid.split(" | ")[0] if " | " in uid else uid
            row_copy = r.copy()
            row_copy["clean_user"] = base_user
            parsed_all.append(row_copy)
            
        if parsed_all:
            master_df = pd.DataFrame(parsed_all)
            for user in master_df['clean_user'].unique():
                sub_df = master_df[master_df['clean_user'] == user].sort_values("odometer").reset_index(drop=True)
                if len(sub_df) >= 2:
                    sub_df['dist'] = sub_df['odometer'].diff()
                    total_km = sub_df['dist'].sum()
                    total_liters = sub_df['liters'].iloc[1:].sum()
                    
                    if total_liters > 0:
                        lifetime_avg = total_km / total_liters
                        leaderboard_records.append({
                            "Driver": f"👤 {user.upper()}",
                            "Lifetime Average Mileage": f"{lifetime_avg:.2f} km/L",
                            "Sort_Val": lifetime_avg
                        })
            
            if leaderboard_records:
                final_leaderboard = pd.DataFrame(leaderboard_records).sort_values("Sort_Val", ascending=False).drop(columns=["Sort_Val"])
                st.dataframe(final_leaderboard, use_container_width=True, hide_index=True)
            else:
                st.info("Insufficient system logs globally to render tournament standings yet.")
        else:
            st.info("Insufficient system logs globally to render tournament standings yet.")
    else:
        st.info("No logs present across cloud servers.")

# --- TAB 3: GLOBAL ADMIN CONTROL COCKPIT (RESTRICTED TO MANTRI ONLY) ---
if is_admin and admin_tab:
    with admin_tab:
        st.title("🛠️ Global Admin System Cockpit")
        st.caption("Elevated access active. You have full visibility over all drivers across the country.")
        
        raw_cloud_data = fetch_from_supabase("fuel_logs")
        if raw_cloud_data:
            admin_df = pd.DataFrame(raw_cloud_data).sort_values("log_date", ascending=False)
            st.markdown("### 🌍 Comprehensive System Master Ledger")
            st.dataframe(admin_df[['id', 'user_id', 'log_date', 'odometer', 'liters', 'cost']], use_container_width=True, hide_index=True)
            
            st.markdown("### 🚨 Global Row Override Control")
            admin_row_to_delete = st.selectbox(
                "Select ANY driver log entry to force delete:",
                options=admin_df.to_dict(orient="records"),
                format_func=lambda x: f"[{x['user_id'].upper()}] Date: {x['log_date']} | Odo: {x['odometer']} km | Cost: ₹{x['cost']}"
            )
            if st.button("Force Administrative Delete", type="primary", use_container_width=True):
                if delete_from_supabase("fuel_logs", admin_row_to_delete["id"]):
                    st.success(f"Administrative override successful. Row ID {admin_row_to_delete['id']} cleared.")
                    st.rerun()
                else:
                    st.error("Admin Instruction Error: Could not delete row.")
        else:
            st.info("The global log grid is completely empty.")

st.markdown("<br><br><div style='text-align: center; opacity: 0.2; font-size: 0.7rem;'>by mantri | elite edition platform v5.0</div>", unsafe_allow_html=True)
