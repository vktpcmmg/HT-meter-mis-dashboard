import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime

st.set_page_config(page_title="Meter Patch MIS", layout="wide")
st.title("📊 Meter Patch Daily MIS Dashboard")

# Google Sheets authentication
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread"], scopes=scope)

gc = gspread.authorize(creds)

# Connect to your spreadsheet
sheet_url = "https://docs.google.com/spreadsheets/d/1z_yeGs78FZeT3EjblCOKuDKS74r7rzXGOOP-Iue9P3U/edit?gid=182645172#gid=182645172"
spreadsheet = gc.open_by_url(sheet_url)

# Load sheets
df_daily = get_as_dataframe(spreadsheet.worksheet("Daily Data Entry")).dropna(subset=["Date"])
df_alloc = get_as_dataframe(spreadsheet.worksheet("Total Meter Allocation per Zone")).dropna()

# Clean up
df_daily['Date'] = pd.to_datetime(df_daily['Date'])
df_daily['Meters Patched'] = pd.to_numeric(df_daily['Meters Patched'])
df_alloc['Total Meters Assigned'] = pd.to_numeric(df_alloc['Total Meters Assigned'])

# Cumulative patched
patched = df_daily.groupby('Zone')['Meters Patched'].sum().reset_index()
patched.columns = ['Zone', 'Total Meters Patched']

# Merge with allocation
summary = pd.merge(df_alloc, patched, on='Zone', how='left').fillna(0)
summary['Meters Pending'] = summary['Total Meters Assigned'] - summary['Total Meters Patched']

# Today’s data
today = pd.Timestamp.now().normalize()
patched_today = df_daily[df_daily['Date'] == today].groupby('Zone')['Meters Patched'].sum().reset_index()
patched_today.columns = ['Zone', 'Meters Patched Today']

# Merge to final
final_summary = pd.merge(summary, patched_today, on='Zone', how='left').fillna(0)

# Display
st.subheader("📋 MIS Summary")
st.dataframe(final_summary)

# Charts
st.subheader("📈 Progress Charts")
st.bar_chart(final_summary.set_index('Zone')[['Total Meters Patched']])
st.bar_chart(final_summary.set_index('Zone')[['Meters Pending']])
st.bar_chart(final_summary.set_index('Zone')[['Meters Patched Today']])
