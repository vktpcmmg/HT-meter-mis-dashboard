# Display
st.subheader("📋 MIS Summary")

# Convert DataFrame to HTML with custom styling
styled_html = final_summary.to_html(
    index=False,
    classes='styled-table',
    border=0
)

# Inject CSS for centering headers and cells
st.markdown("""
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 16px;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
    }
    .styled-table th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Render the styled table
st.markdown(styled_html, unsafe_allow_html=True)
