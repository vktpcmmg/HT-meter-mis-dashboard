import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
import matplotlib.pyplot as plt
from datetime import datetime

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

# Charts section
st.subheader("📈 Progress Charts")

# 1. Line chart for total patched per day (all zones)
daily_total = df_daily.groupby('Date')['Meters Patched'].sum().reset_index()
daily_total['Date'] = pd.to_datetime(daily_total['Date'])

line_chart_data = daily_total.set_index('Date')

st.line_chart(line_chart_data)

# 2. Bar charts for per-zone metrics with legends on the left
fig, ax = plt.subplots(1, 3, figsize=(18, 6))

# Total Meters Patched bar chart
ax[0].bar(final_summary['Zone'], final_summary['Total Meters Patched'], color='blue', label='Total Meters Patched')
ax[0].set_title('Total Meters Patched')
ax[0].legend(loc='upper left')

# Meters Pending bar chart
ax[1].bar(final_summary['Zone'], final_summary['Meters Pending'], color='red', label='Meters Pending')
ax[1].set_title('Meters Pending')
ax[1].legend(loc='upper left')

# Meters Patched Today bar chart
ax[2].bar(final_summary['Zone'], final_summary['Meters Patched Today'], color='green', label='Meters Patched Today')
ax[2].set_title('Meters Patched Today')
ax[2].legend(loc='upper left')

# Set labels and titles
for a in ax:
    a.set_xlabel('Zone')
    a.set_ylabel('Count')

# Display the plot
st.pyplot(fig)
