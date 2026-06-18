import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import requests
import base64

# Set up clean mobile-first viewport architecture
st.set_page_config(page_title="EcoSport Team Cockpit", page_icon="⚡", layout="centered")

# --- PREMIUM DASHBOARD CUSTOM THEME INJECTION ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        div.stButton > button:first-child {
            background-color: #ff4b4b !important; color: white !important;
            border: none !important; font-weight: bold !important;
            border-radius: 8px !important; padding: 0.5rem 1rem !important;
        }
        [data-testid="stMetricContainer"] {
            background-color: #1a1f2c; border: 1px solid #2d3748;
            padding: 15px; border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- GITHUB FILE STORAGE CONFIGURATION ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO_OWNER = "manishtripathiirman-collab"
REPO_NAME = "car-efficiency-tracker"
FILE_PATH = "fuel_logs.json"
BRANCH = "main"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_from_github():
    """Reads the permanent logs file directly from your GitHub repository"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}?ref={BRANCH}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            content_data = response.json()
            file_content = base64.b64decode(content_data["content"]).decode("utf-8")
            return json.loads(file_content), content_data["sha"]
    except Exception:
        pass
    return [], None

def commit_to_github(data_list, sha=None):
    """Writes the updated logs back to your GitHub repository file automatically"""
    if not GITHUB_TOKEN:
        st.error("⚠️ App Secret Missing: Please add 'GITHUB_TOKEN' to settings.")
        return False
        
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    updated_json = json.dumps(data_list, indent=4)
    encoded_content = base64.b64encode(updated_json.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"Automated telemetry sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": encoded_content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    response = requests.put(url, headers=HEADERS, json=payload, timeout=10)
    return response.status_code in [200, 201]

# --- USER IDENTITY ---
current_user = st.query_params.get("operator", "mantri").lower()

# --- REPOSITORIES DATA LAYER ---
raw_cloud_data, current_sha = fetch_from_github()

# Process data entries
parsed_logs = []
all_user_dates = []

for row in raw_cloud_data:
    uid = row.get("user_id", "")
    base_user = uid.split(" | ")[0] if " | " in uid else uid
    
    if base_user == current_user:
        all_user_dates.append(row.get("log_date"))
        row_copy = row.copy()
        row_copy["Air Checked"] = "Yes" if "Air: Yes" in uid else "No"
        row_copy["Full Tank?"] = "Yes" if "Full Tank: Yes" in uid else "No"
        row_copy["Service Cost"] = f"₹{uid.split('Service Cost: ₹')[1]}" if "Service Cost: ₹" in uid else "No"
        parsed_logs.append(row_copy)
        
user_df = pd.DataFrame(parsed_logs)

# --- PERFORMANCE ANALYTICS MATH ENGINE (REPAIRED INTERVAL COST LOGIC) ---
avg_mileage, cost_per_km = 0.0, 0.0
if len(user_df) >= 2:
    user_df = user_df.sort_values("odometer").reset_index(drop=True)
    user_df['distance_driven'] = user_df['odometer'].diff()
    
    valid_tank_distances = []
    valid_tank_liters = []
    valid_tank_costs = []
    
    for i in range(1, len(user_df)):
        if user_df.iloc[i]["Full Tank?"] == "Yes" and user_df.iloc[i-1]["Full Tank?"] == "Yes":
            valid_tank_distances.append(user_df.iloc[i]["distance_driven"])
            valid_tank_liters.append(user_df.iloc[i]["liters"])
            valid_tank_costs.append(user_df.iloc[i]["cost"])
    
    if sum(valid_tank_distances) > 0 and sum(valid_tank_liters) > 0:
        avg_mileage = sum(valid_tank_distances) / sum(valid_tank_liters)
        cost_per_km = sum(valid_tank_costs) / sum(valid_tank_distances)
    else:
        total_km = user_df['distance_driven'].sum()
        avg_mileage = total_km / user_df['liters'].iloc[1:].sum() if user_df['liters'].iloc[1:].sum() > 0 else 0.0
        cost_per_km = user_df['cost'].iloc[1:].sum() / total_km if total_km > 0 else 0.0

st.title(f"⚡ Welcome, {current_user.upper()}")
st.markdown("### 📊 Your Performance Analytics")
col_m1, col_m2 = st.columns(2)
col_m1.metric(label="📊 True Tank-to-Tank Mileage", value=f"{avg_mileage:.2f} km/L")
col_m2.metric(label="💸 Your Running Cost", value=f"₹ {cost_per_km:.2f} / km")

# --- DATA ENTRY FORM ---
st.markdown("### ⛽ Step 1: Verify & Log Fuel Telemetry")
with st.container(border=True):
    form_col1, form_col2 = st.columns(2)
    log_date = form_col1.date_input("Transaction Date Stamping", value=datetime.today())
    odometer = form_col1.number_input("Odometer Tracker (km)", min_value=0, step=1)
    liters = form_col2.number_input("Infused Volume (Liters)", min_value=0.0, step=0.1, format="%.2f")
    price = form_col2.number_input("Transaction Total Value (₹)", min_value=0.0, step=10.0)
