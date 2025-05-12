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

st.markdown(final_summary.to_html(index=False, escape=False), unsafe_allow_html=True)

# Charts section
st.subheader("📈 Progress Charts")

# 1. Line chart for total patched per day (all zones)
daily_total = df_daily.groupby('Date')['Meters Patched'].sum().reset_index()
daily_total['Date'] = pd.to_datetime(daily_total['Date'])

# Line chart data
line_chart_data = daily_total.set_index('Date')

# Create a smaller figure using matplotlib for custom formatting
fig, ax = plt.subplots(figsize=(6, 2))  # You can adjust the width and height here

ax.plot(line_chart_data.index, line_chart_data['Meters Patched'])

# Format the x-axis to show only the date (without time)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
plt.xticks(rotation=45)  # Rotate the x-axis labels for better readability

# Set labels and title
ax.set_xlabel('Date')
ax.set_ylabel('Meters Patched')
ax.set_title('Total Meters Patched Per Day')

# Display the plot
st.pyplot(fig)


# 2. Bar charts for per-zone metrics (without "Meters Patched Today" section)
fig, ax = plt.subplots(figsize=(8, 4))

# Bar chart for Total Meters Patched
ax.bar(final_summary['Zone'], final_summary['Total Meters Patched'], label='Total Meters Patched', color='skyblue')
# Bar chart for Meters Pending
ax.bar(final_summary['Zone'], final_summary['Meters Pending'], bottom=final_summary['Total Meters Patched'], label='Meters Pending', color='lightcoral')

# Add labels and title
ax.set_xlabel('Zone')
ax.set_ylabel('Meters Count')
ax.set_title('Meters Patched vs Pending by Zone')

# Add legend to the left of the bar chart
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# Display the chart
st.pyplot(fig)

# Function to save the figure as an image and make it downloadable
def save_fig_to_image(fig):
    # Save the figure to a BytesIO object
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches='tight')
    img_buf.seek(0)
    img = Image.open(img_buf)
    return img_buf

# Save the bar chart and line chart figures as images
img_buf_line_chart = save_fig_to_image(fig)
img_buf_bar_chart = save_fig_to_image(fig)

# Provide a download button to download the image
st.download_button(
    label="Download Line Chart as Image",
    data=img_buf_line_chart,
    file_name="line_chart.png",
    mime="image/png"
)

st.download_button(
    label="Download Bar Chart as Image",
    data=img_buf_bar_chart,
    file_name="bar_chart.png",
    mime="image/png"
)
