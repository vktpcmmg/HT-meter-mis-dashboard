import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
import io
from weasyprint import HTML

# Set page configuration
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
        th, td {
            text-align: center;
            padding: 8px;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: center !important;
        }
    </style>
""", unsafe_allow_html=True)

# Convert the final summary DataFrame to HTML
html_table = final_summary.to_html(index=False, escape=False)

# Function to save the MIS summary table as an image using WeasyPrint
def save_table_as_image(html_content):
    # Use WeasyPrint to convert HTML to an image
    html = HTML(string=html_content)
    img = html.write_png()  # Saving the HTML table as PNG image
    return img

# Convert the MIS summary table into an image
img_buf = save_table_as_image(html_table)

# Provide a download button to download the image
st.download_button(
    label="Download MIS Summary as Image",
    data=img_buf,
    file_name="mis_summary.png",
    mime="image/png"
)
