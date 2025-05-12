import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
st.set_page_config(page_title="HT Meter TOD Patch MIS", layout="wide")
st.title("📊 HT Meter TOD Patch Daily MIS Dashboard")

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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Line chart for total patched per day (all zones)
daily_total = df_daily.groupby('Date')['Meters Patched'].sum().reset_index()
daily_total['Date'] = pd.to_datetime(daily_total['Date'])

# Line chart data
# 1. Line chart for cumulative patched per day (all zones)
daily_total = df_daily.groupby('Date')['Meters Patched'].sum().reset_index()
daily_total['Date'] = pd.to_datetime(daily_total['Date'])

# Calculate cumulative sum of meters patched over time
daily_total['Cumulative Meters Patched'] = daily_total['Meters Patched'].cumsum()

# Line chart data
line_chart_data = daily_total.set_index('Date')

# Create a smaller figure using matplotlib for custom formatting
fig, ax = plt.subplots(figsize=(6, 2))  # You can adjust the width and height here

ax.plot(line_chart_data.index, line_chart_data['Cumulative Meters Patched'], color='b', label='Cumulative Meters Patched')

# Format the x-axis to show only the date (without time)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
plt.xticks(rotation=45)  # Rotate the x-axis labels for better readability

# Set labels and title
ax.set_xlabel('Date')
ax.set_ylabel('Cumulative Meters Patched')
ax.set_title('Cumulative Meters Patched Per Day')

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

# ---------- Place this just after final_summary is created ----------
import matplotlib.pyplot as plt
import io

def save_summary_as_image(df):
    rows, cols = df.shape
    col_width = 2  # Width per column (in inches)
    row_height = 0.5  # Height per row (in inches)
    fig_width = max(8, col_width * cols)
    fig_height = max(2, row_height * (rows + 1))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')

    # Create table
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     cellLoc='center',
                     loc='center',
                     edges='closed')

    # Styling
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    # Bold header and center align
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('black')
        cell.set_linewidth(1)
        cell.set_text_props(ha='center', va='center')
        if row == 0:
            cell.set_fontweight('bold')
            cell.set_facecolor('#f0f0f0')

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    return buf

# ---------- Add this where you want the download button to appear, below the table ----------
image_buf = save_summary_as_image(final_summary)

st.download_button(
    label="📥 Download MIS Summary as Image",
    data=image_buf,
    file_name=f"MIS_Summary_{datetime.now().strftime('%Y%m%d')}.png",
    mime="image/png"
)
