import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime
from twilio.rest import Client

# Setup page config
st.set_page_config(page_title="Meter Patch MIS", layout="wide")
st.title("📊 Meter Patch Daily MIS Dashboard")

# Google Sheets authentication
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread"], scopes=scope)
gc = gspread.authorize(creds)

# Connect to your spreadsheet
sheet_url = "https://docs.google.com/spreadsheets/d/1z_yeGs78FZeT3EjblCOKuDKS74r7rzXGOOP-Iue9P3U/edit?gid=182645172#gid=182645172"
spreadsheet = gc.open_by_url(sheet_url)

# Load sheets
df_daily = get_as_dataframe(spreadsheet.worksheet("Daily Data Entry")).dropna(subset=["Date"])
df_alloc = get_as_dataframe(spreadsheet.worksheet("Total Meter Allocation per Zone")).dropna()

# Clean and format
df_daily['Date'] = pd.to_datetime(df_daily['Date']).dt.normalize()
df_daily['Meters Patched'] = pd.to_numeric(df_daily['Meters Patched'])
df_alloc['Total Meters Assigned'] = pd.to_numeric(df_alloc['Total Meters Assigned'])

# Cumulative patched per zone
patched = df_daily.groupby('Zone')['Meters Patched'].sum().reset_index()
patched.columns = ['Zone', 'Total Meters Patched']

# Merge allocation + patched
summary = pd.merge(df_alloc, patched, on='Zone', how='left').fillna(0)
summary['Meters Pending'] = summary['Total Meters Assigned'] - summary['Total Meters Patched']

# Today's data
today = pd.Timestamp.now().normalize()
patched_today = df_daily[df_daily['Date'] == today].groupby('Zone')['Meters Patched'].sum().reset_index()
patched_today.columns = ['Zone', 'Meters Patched Today']

# Final summary
final_summary = pd.merge(summary, patched_today, on='Zone', how='left').fillna(0)

# Display MIS Summary with timestamp
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### 📋 **MIS Summary**")
with col2:
    st.markdown(f"#### 🕒 *As of {datetime.now().strftime('%d-%m-%Y')}*")

# Show styled table with center alignment
st.markdown("""
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: center;
        }
        td {
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(final_summary.to_html(index=False, escape=False), unsafe_allow_html=True)

# Function to send message via Twilio to WhatsApp
def send_whatsapp_message():
    account_sid = 'your_account_sid'  # Replace with your Twilio Account SID
    auth_token = 'your_auth_token'    # Replace with your Twilio Auth Token
    twilio_number = 'whatsapp:+1415XXXXXXX'  # Replace with your Twilio WhatsApp number
    group_id = 'whatsapp:+1415XXXXXXX'  # Replace with your target WhatsApp number or group ID

    # Create the message body
    message = "MIS Summary Report\n" + final_summary.to_string(index=False)

    # Initialize Twilio Client
    client = Client(account_sid, auth_token)

    # Send message via Twilio API
    message = client.messages.create(
        body=message,
        from_=twilio_number,  # Your Twilio WhatsApp number
        to=group_id          # Target recipient's WhatsApp number
    )
    
    # Return message SID for confirmation
    return f"Message sent with SID: {message.sid}"

# Create button in Streamlit to trigger sending WhatsApp message
if st.button("📤 Share MIS Summary via WhatsApp"):
    result = send_whatsapp_message()  # Call the function to send the message
    st.success(result)  # Display a success message with SID
