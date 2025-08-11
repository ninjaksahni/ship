import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="Ship State & City Counter", layout="wide", page_icon="📦")

# ----------------------
# Instructions for users
# ----------------------
st.markdown(
    """
    <div style="padding:12px; background-color:#E8F0FF; border-radius:8px; border: 1px solid #0B5CFF; margin-bottom:15px;">
    <h3 style="color:#0B1A2B; margin-bottom:6px;">📥 Step 1: Download Your Amazon Orders Report</h3>
    <p style="margin:0; font-size:15px;">
    Go to <a href="https://sellercentral.amazon.in/reportcentral/FlatFileAllOrdersReport/1" target="_blank" style="color:#0B5CFF; font-weight:600;">Amazon Seller Central – Flat File All Orders Report</a><br>
    Select <b>Last 30 days</b>, generate the report, and download it as a <b>.txt</b> file.
    </p>
    <h3 style="color:#0B1A2B; margin-top:12px; margin-bottom:6px;">📤 Step 2: Upload Here</h3>
    <p style="margin:0; font-size:15px;">Use the uploader below to select the downloaded <b>.txt</b> file for analysis.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------
# Styling
# ----------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #F7FAFC; color: #0B1A2B; }
    .css-1d391kg { color: #0b1a2b; }
    .app-header { font-size: 28px; font-weight: 700; color: #0B1A2B; margin-bottom: 6px; }
    .app-sub { color: #3A4857; margin-top: -6px; margin-bottom: 14px; }
    .metric-card {
      background: #ffffff;
      border: 1px solid #E6EEF8;
      border-radius: 10px;
      padding: 10px 14px;
      color: #0B1A2B;
    }
    .stButton>button, .stDownloadButton>button, div.stDownloadButton > button {
      background-color: #0B5CFF !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 8px 14px !important;
      font-weight: 600 !important;
      box-shadow: 0 6px 18px rgba(11,92,255,0.15) !important;
    }
    .stSelectbox > div[role="combobox"] > div, .stSlider > div {
      color: #0B1A2B !important;
    }
    .stDataFrame table thead tr th {
      background: #0B5CFF !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      padding: 8px !important;
      border-bottom: 2px solid #E6EEF8 !important;
    }
    .stDataFrame table tbody tr td {
      background: #ffffff !important;
      color: #0B1A2B !important;
      padding: 8px !important;
      border-bottom: 1px solid #EEF5FF !important;
    }
    .stDataFrame table, .stDataFrame th, .stDataFrame td {
      font-size: 14px !important;
    }
    div.stDownloadButton > button {
      background-color: #0B5CFF !important;
      color: #fff !important;
    }
    .stMetricValue {
      color: #0B1A2B !important;
      font-size: 22px !important;
      font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------
# City merge mapping
# ----------------------
CITY_MERGE = {
    "MUMBAI": "Mumbai",
    "NAVI MUMBAI": "Mumbai",
    "NAVI-MUMBAI": "Mumbai",
    "NEW MUMBAI": "Mumbai",
    "DELHI": "Delhi NCR",
    "NEW DELHI": "Delhi NCR",
    "GURGAON": "Delhi NCR",
    "GURUGRAM": "Delhi NCR",
    "NOIDA": "Delhi NCR",
    "FARIDABAD": "Delhi NCR",
    "GHAZIABAD": "Delhi NCR",
}

def normalize_city(raw):
    if pd.isna(raw) or str(raw).strip() == "":
        return "Unknown"
    s = str(raw).strip()
    mapped = CITY_MERGE.get(s.upper())
    return mapped if mapped is not None else s.title()

def display_city_label(name):
    if name == "Mumbai":
        return "Mumbai ++"
    if name == "Delhi NCR":
        return "Delhi ++"
    return name

# ----------------------
# Sidebar
# ----------------------
st.sidebar.header("Options")
top_n = st.sidebar.slider("Top N to show in charts", 3, 20, 6, 1)
show_raw = st.sidebar.checkbox("Show sample of raw rows", False)
download_all = st.sidebar.checkbox("Enable full-data CSV download", True)

# ----------------------
# Main header
# ----------------------
st.markdown('<div class="app-header">📦 Ship State & City Counter</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">Upload your Amazon TXT/CSV (tab-delimited) to get cleaned counts + top charts.</div>', unsafe_allow_html=True)

# ----------------------
# File uploader
# ----------------------
uploaded = st.file_uploader("Upload Amazon TXT/CSV (tab-delimited) file", type=["txt", "csv"])
if not uploaded:
    st.stop()

def read_csv_flexible(u):
    try:
        return pd.read_csv(u, sep="\t", dtype=str)
    except:
        u.seek(0)
        return pd.read_csv(u, dtype=str)

try:
    df = read_csv_flexible(uploaded)
except Exception as e:
    st.error(f"Could not parse file: {e}")
    st.stop()

# ----------------------
# Column detection
# ----------------------
cols_lower = {c.lower(): c for c in df.columns}
if "ship-state" in cols_lower and "ship-city" in cols_lower:
    state_col = cols_lower["ship-state"]
    city_col = cols_lower["ship-city"]
else:
    st.error("Missing 'ship-state' and/or 'ship-city' columns.")
    st.stop()

# ----------------------
# Data cleaning
# ----------------------
df[state_col] = df[state_col].astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown"})
df[city_col] = df[city_col].astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown"})
df["ship_city_norm"] = df[city_col].apply(normalize_city)
df["ship_state_clean"] = df[state_col].apply(lambda s: s.title() if (s and s != "Unknown") else "Unknown")

state_counts = df["ship_state_clean"].value_counts().rename_axis("Ship State").reset_index(name="Count")
city_counts = df["ship_city_norm"].value_counts().rename_axis("Ship City").reset_index(name="Count")
city_counts_display = city_counts.copy()
city_counts_display["Ship City"] = city_counts_display["Ship City"].apply(display_city_label)

# ----------------------
# Metrics
# ----------------------
total_rows = len(df)
c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
with c1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Rows (orders)", f"{total_rows:,}")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Unique states", f"{state_counts.shape[0]:,}")
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Unique cities", f"{city_counts.shape[0]:,}")
    st.markdown('</div>', unsafe_allow_html=True)
with c4:
    top_state_name = state_counts.iloc[0]["Ship State"] if not state_counts.empty else "—"
    top_city_name = city_counts_display.iloc[0]["Ship City"] if not city_counts_display.empty else "—"
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Top state / city", f"{top_state_name} / {top_city_name}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ----------------------
# Tables & downloads
# ----------------------
left, right = st.columns([1.05, 1.25])
with left:
    st.subheader("📍 Ship State Counts")
    st.dataframe(state_counts.style.format({"Count": "{:,}"}), use_container_width=True, height=320)

    st.subheader("🏙 Ship City Counts")
    st.dataframe(city_counts_display.style.format({"Count": "{:,}"}), use_container_width=True, height=320)

    st.download_button("Download state counts CSV", state_counts.to_csv(index=False), file_name="state_counts.csv", mime="text/csv")
    st.download_button("Download city counts CSV", city_counts_display.to_csv(index=False), file_name="city_counts.csv", mime="text/csv")

    if download_all:
        csv_all = df.to_csv(index=False)
        st.download_button("Download full cleaned dataset", csv_all, file_name="all_orders_cleaned.csv", mime="text/csv")

    if show_raw:
        with st.expander("Sample raw rows"):
            st.dataframe(df.head(250), use_container_width=True)

# ----------------------
# Charts
# ----------------------
with right:
    st.subheader(f"📊 Top {top_n} Ship States")
    top_states = state_counts.head(top_n).copy()
    if not top_states.empty:
        fig_states = px.bar(
            top_states.sort_values("Count"),
            x="Count", y="Ship State",
            orientation="h", text="Count",
            height=380, color_discrete_sequence=["#0B5CFF"]
        )
        fig_states.update_traces(texttemplate='<b>%{x:,}</b>', textposition='outside')
        fig_states.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#000000"),
            xaxis=dict(tickfont=dict(color="#000000")),
            yaxis=dict(tickfont=dict(color="#000000")),
            xaxis_title="", yaxis_title=""
        )
        st.plotly_chart(fig_states, use_container_width=True)

    st.subheader(f"📊 Top {top_n} Ship Cities")
    top_cities = city_counts.head(top_n).copy()
    if not top_cities.empty:
        top_cities_plot = top_cities.copy()
        top_cities_plot["Ship City"] = top_cities_plot["Ship City"].apply(display_city_label)
        fig_cities = px.bar(
            top_cities_plot.sort_values("Count"),
            x="Count", y="Ship City",
            orientation="h", text="Count",
            height=380, color_discrete_sequence=["#FF7A00"]
        )
        fig_cities.update_traces(texttemplate='<b>%{x:,}</b>', textposition='outside')
        fig_cities.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#000000"),
            xaxis=dict(tickfont=dict(color="#000000")),
            yaxis=dict(tickfont=dict(color="#000000")),
            xaxis_title="", yaxis_title=""
        )
        st.plotly_chart(fig_cities, use_container_width=True)