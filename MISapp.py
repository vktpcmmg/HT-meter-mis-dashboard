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
# Convert numeric meter columns to integers (remove decimals)
meter_cols = ['Total Meters Assigned', 'Total Meters Patched', 'Meters Pending', 'Meters Patched Today']
final_summary[meter_cols] = final_summary[meter_cols].astype(int)
# Add Total row to MIS summary
total_row = final_summary[meter_cols].sum(numeric_only=True).to_frame().T
total_row.insert(0, 'Zone', 'Total')
final_summary = pd.concat([final_summary, total_row], ignore_index=True)


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
# 1. Line chart for cumulative patched per day (all zones)
daily_total = df_daily.groupby('Date')['Meters Patched'].sum().reset_index()
daily_total['Date'] = pd.to_datetime(daily_total['Date'])
daily_total['Cumulative Meters Patched'] = daily_total['Meters Patched'].cumsum()
line_chart_data = daily_total.set_index('Date')

fig, ax = plt.subplots(figsize=(6, 2))

ax.plot(line_chart_data.index, line_chart_data['Cumulative Meters Patched'], color='b', label='Cumulative Meters Patched')

# Add data labels
for i, value in enumerate(line_chart_data['Cumulative Meters Patched']):
    ax.text(line_chart_data.index[i], value, str(int(value)), fontsize=9, color='blue', ha='center', va='bottom')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
plt.xticks(rotation=45)
ax.set_xlabel('Date')
ax.set_ylabel('Cumulative Meters Patched')
ax.set_title('Cumulative Meters Patched Per Day')
st.pyplot(fig)




# 2. Bar charts for per-zone metrics (without "Meters Patched Today" section)
fig, ax = plt.subplots(figsize=(8, 4))

bars1 = ax.bar(final_summary['Zone'], final_summary['Total Meters Patched'], label='Total Meters Patched', color='skyblue')
bars2 = ax.bar(final_summary['Zone'], final_summary['Meters Pending'], bottom=final_summary['Total Meters Patched'], label='Meters Pending', color='lightcoral')

# Add data labels for Total Meters Patched
for bar in bars1:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, str(int(yval)), ha='center', va='bottom', fontsize=10)

# Add data labels for Meters Pending
for bar in bars2:
    yval = bar.get_height()
    base = final_summary['Total Meters Patched'][bars2.index(bar)]
    ax.text(bar.get_x() + bar.get_width() / 2, base + yval + 1, str(int(yval)), ha='center', va='bottom', fontsize=10)

ax.set_xlabel('Zone')
ax.set_ylabel('Meters Count')
ax.set_title('Meters Patched vs Pending by Zone')
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
st.pyplot(fig)


# ---------- Place this just after final_summary is created ----------
def save_summary_as_image(df): 
    import matplotlib.pyplot as plt
    import io

    rows, cols = df.shape
    col_width = 1.5     # Keep column width narrow
    row_height = 1.2    # Regular row height
    header_extra_height = 0.6  # Add extra space for header

    fig_width = col_width * cols
    fig_height = row_height * rows + header_extra_height  # Add header height

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=150)
    ax.axis('off')

    # Create table with wrapped column labels
    table = ax.table(
        cellText=df.values,
        colLabels=[label.replace(" ", "\n") for label in df.columns],  # wrap headers
        cellLoc='center',
        loc='center',
        edges='closed'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.0, 2.0)  # Keep regular scaling for cells

    # Style cells
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('black')
        cell.set_linewidth(1)
        cell.set_text_props(ha='center', va='center')
        if row == 0:
            cell.get_text().set_fontweight('bold')
            cell.set_facecolor('#f0f0f0')
            cell.set_height(cell.get_height() + header_extra_height / fig_height)  # increase only header height
        elif row == len(df):  # Bold the Total row only
            cell.get_text().set_fontweight('bold')

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf







# ---------- Add this where you want the download button to appear, below the table ----------
image_buf = save_summary_as_image(final_summary)

st.download_button(
    label="📥 Download MIS Summary as Image",
    data=image_buf,
    file_name=f"MIS_Summary_{datetime.now().strftime('%Y%m%d')}.png",
    mime="image/png"
)
