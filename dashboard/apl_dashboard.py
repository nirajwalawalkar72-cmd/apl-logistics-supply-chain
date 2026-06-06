# ============================================================
# APL Logistics — Live Streamlit Dashboard (Complete Final)
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="APL Logistics Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stMetric {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
    }
    h1 { color: #1a237e; }
    .live-badge {
        background-color: #e74c3c;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv(r"H:\NIRAJ\Projects\APL_Logistics.csv", encoding='latin1')
    df.dropna(subset=['Days for shipping (real)',
                       'Days for shipment (scheduled)',
                       'Delivery Status',
                       'Late_delivery_risk'], inplace=True)
    df.columns = (df.columns
                    .str.strip()
                    .str.replace(' ', '_')
                    .str.replace('(', '')
                    .str.replace(')', ''))
    df['Delay_Gap'] = df['Days_for_shipping_real'] - df['Days_for_shipment_scheduled']
    def classify_delivery(gap):
        if gap > 0:    return 'Delayed'
        elif gap == 0: return 'On-Time'
        else:          return 'Early'
    df['Delivery_Class'] = df['Delay_Gap'].apply(classify_delivery)
    start_date = datetime(2015, 1, 1)
    end_date   = datetime(2018, 12, 31)
    total_days = (end_date - start_date).days
    np.random.seed(42)
    random_days = np.sort(np.random.randint(0, total_days, size=len(df)))
    df['Order_Date']       = [start_date + timedelta(days=int(d)) for d in random_days]
    df['Order_Year']       = df['Order_Date'].dt.year
    df['Order_Month_Name'] = df['Order_Date'].dt.strftime('%b %Y')
    return df

df = load_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("📦 APL Logistics")
st.sidebar.markdown("---")
st.sidebar.subheader("🔴 Live Dashboard")
live_mode    = st.sidebar.toggle("Enable Live Refresh", value=False)
refresh_rate = st.sidebar.slider("Refresh Every (seconds)", 5, 60, 10)
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")

st.sidebar.markdown("📅 **Date Range**")
min_date   = df['Order_Date'].min().date()
max_date   = df['Order_Date'].max().date()
start_date = st.sidebar.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
end_date   = st.sidebar.date_input("To Date",   value=max_date, min_value=min_date, max_value=max_date)
if start_date > end_date:
    st.sidebar.error("⚠️ Start date must be before End date!")
st.sidebar.markdown("---")

selected_mode = st.sidebar.multiselect(
    "📦 Shipping Mode",
    options=df['Shipping_Mode'].unique().tolist(),
    default=df['Shipping_Mode'].unique().tolist()
)
selected_region = st.sidebar.multiselect(
    "🌍 Order Region",
    options=df['Order_Region'].unique().tolist(),
    default=df['Order_Region'].unique().tolist()
)
selected_market = st.sidebar.multiselect(
    "🗺️ Market",
    options=df['Market'].unique().tolist(),
    default=df['Market'].unique().tolist()
)
selected_segment = st.sidebar.multiselect(
    "👥 Customer Segment",
    options=df['Customer_Segment'].unique().tolist(),
    default=df['Customer_Segment'].unique().tolist()
)

filtered_df = df[
    (df['Order_Date'].dt.date >= start_date) &
    (df['Order_Date'].dt.date <= end_date)   &
    (df['Shipping_Mode'].isin(selected_mode))        &
    (df['Order_Region'].isin(selected_region))       &
    (df['Market'].isin(selected_market))             &
    (df['Customer_Segment'].isin(selected_segment))
]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Showing **{len(filtered_df):,}** of **{len(df):,}** records")
st.sidebar.info(f"📅 **{start_date}** → **{end_date}**")

# ============================================================
# HEADER
# ============================================================
col_title, col_badge, col_time = st.columns([5, 1, 2])
with col_title:
    st.title("📦 APL Logistics — Delivery Performance Dashboard")
    st.markdown("**Global Supply Chain | Delivery & Delay Risk Intelligence**")
with col_badge:
    if live_mode:
        st.markdown('<br><span class="live-badge">🔴 LIVE</span>', unsafe_allow_html=True)
with col_time:
    st.markdown(f"<br>🕐 **{datetime.now().strftime('%d %b %Y %I:%M:%S %p')}**", unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# MODULE 1 — KPI CARDS
# ============================================================
st.subheader("📊 Key Performance Indicators")
on_time_rate    = (filtered_df['Delivery_Class'] == 'On-Time').mean() * 100
avg_delay       = filtered_df['Delay_Gap'].mean()
late_risk_ratio = filtered_df['Late_delivery_risk'].mean() * 100
total_orders    = len(filtered_df)
delayed_orders  = (filtered_df['Delivery_Class'] == 'Delayed').sum()
early_orders    = (filtered_df['Delivery_Class'] == 'Early').sum()

col1,col2,col3,col4,col5,col6 = st.columns(6)
col1.metric("✅ On-Time Rate",  f"{on_time_rate:.1f}%")
col2.metric("⏱️ Avg Delay",     f"{avg_delay:.2f} days")
col3.metric("🚨 Late Risk",     f"{late_risk_ratio:.1f}%")
col4.metric("📦 Total Orders",  f"{total_orders:,}")
col5.metric("❌ Delayed",       f"{delayed_orders:,}")
col6.metric("✅ Early",         f"{early_orders:,}")
st.markdown("---")

# ============================================================
# MODULE 2 — AVERAGE DELAY SCORECARDS (NEW ✅)
# ============================================================
st.subheader("📋 Average Delay Scorecards by Shipping Mode")

modes = filtered_df['Shipping_Mode'].unique().tolist()
cols  = st.columns(len(modes))
icons = {"Standard Class":"📦","First Class":"✈️","Second Class":"📮","Same Day":"🚀"}

for i, mode in enumerate(modes):
    mode_data  = filtered_df[filtered_df['Shipping_Mode'] == mode]
    mode_delay = mode_data['Delay_Gap'].mean()
    mode_risk  = mode_data['Late_delivery_risk'].mean() * 100
    icon       = icons.get(mode, "📦")
    cols[i].metric(
        label=f"{icon} {mode}",
        value=f"{mode_delay:.2f} days",
        delta=f"Risk: {mode_risk:.1f}%",
        delta_color="inverse"
    )
st.markdown("---")

# ============================================================
# MODULE 3 — DELIVERY PERFORMANCE OVERVIEW
# ============================================================
st.subheader("📦 Delivery Performance Overview")
col1, col2 = st.columns(2)
with col1:
    dc = filtered_df['Delivery_Class'].value_counts().reset_index()
    dc.columns = ['Delivery_Class','Count']
    fig1 = px.bar(dc, x='Delivery_Class', y='Count', color='Delivery_Class',
                  color_discrete_map={'Delayed':'#e74c3c','On-Time':'#2ecc71','Early':'#3498db'},
                  title='On-Time vs Late Delivery Distribution', text='Count')
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    sc = filtered_df['Delivery_Status'].value_counts().reset_index()
    sc.columns = ['Delivery_Status','Count']
    fig2 = px.pie(sc, names='Delivery_Status', values='Count',
                  title='Delivery Status Breakdown', hole=0.4,
                  color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 4 — DATE TRENDS
# ============================================================
st.subheader("📅 Delivery Trends Over Time")
col1, col2 = st.columns(2)
with col1:
    monthly = filtered_df.groupby('Order_Month_Name').agg(
        Late_Risk=('Late_delivery_risk','mean')).reset_index()
    monthly['Late_Risk'] = monthly['Late_Risk'] * 100
    fig3 = px.line(monthly, x='Order_Month_Name', y='Late_Risk',
                   title='Monthly Late Risk Trend (%)', markers=True,
                   color_discrete_sequence=['#e74c3c'])
    fig3.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)
with col2:
    yearly = filtered_df.groupby('Order_Year').agg(
        Total_Orders=('Late_delivery_risk','count'),
        Late_Risk=('Late_delivery_risk','mean')).reset_index()
    yearly['Late_Risk'] = yearly['Late_Risk'] * 100
    fig4 = px.bar(yearly, x='Order_Year', y='Total_Orders', color='Late_Risk',
                  color_continuous_scale='Reds', title='Yearly Orders & Late Risk',
                  text='Total_Orders')
    fig4.update_traces(textposition='outside')
    st.plotly_chart(fig4, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 5 — DELAY RISK ANALYSIS
# ============================================================
st.subheader("🚨 Delay Risk Analysis Dashboard")
col1, col2 = st.columns(2)
with col1:
    fig5 = px.histogram(filtered_df, x='Delay_Gap', nbins=20,
                        color_discrete_sequence=['#e74c3c'],
                        title='Delay Gap Histogram',
                        labels={'Delay_Gap':'Delay Gap (Days)'})
    fig5.add_vline(x=0, line_dash='dash', line_color='green',
                   annotation_text='On-Time Line')
    fig5.add_vline(x=filtered_df['Delay_Gap'].mean(),
                   line_dash='dash', line_color='blue',
                   annotation_text=f'Mean:{filtered_df["Delay_Gap"].mean():.2f}')
    st.plotly_chart(fig5, use_container_width=True)
with col2:
    rc = filtered_df['Late_delivery_risk'].value_counts().reset_index()
    rc.columns = ['Risk','Count']
    rc['Risk'] = rc['Risk'].map({1:'🚨 Late Risk', 0:'✅ No Risk'})
    fig6 = px.pie(rc, names='Risk', values='Count',
                  title='Late_delivery_risk Distribution', hole=0.4,
                  color_discrete_sequence=['#e74c3c','#2ecc71'])
    st.plotly_chart(fig6, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 6 — SHIPPING MODE + SLA COMPLIANCE (NEW ✅)
# ============================================================
st.subheader("🚚 Shipping Mode Comparison")
col1, col2 = st.columns(2)
with col1:
    md = filtered_df.groupby('Shipping_Mode')['Delay_Gap'].mean().reset_index()
    fig7 = px.bar(md, x='Shipping_Mode', y='Delay_Gap', color='Delay_Gap',
                  color_continuous_scale='Reds',
                  title='Mode-wise Delay Performance',
                  text=md['Delay_Gap'].round(2))
    fig7.update_traces(textposition='outside')
    st.plotly_chart(fig7, use_container_width=True)
with col2:
    mr = filtered_df.groupby('Shipping_Mode')['Late_delivery_risk'].mean().reset_index()
    mr['Late_delivery_risk'] = mr['Late_delivery_risk'] * 100
    fig8 = px.bar(mr, x='Shipping_Mode', y='Late_delivery_risk', color='Late_delivery_risk',
                  color_continuous_scale='Oranges',
                  title='Late Risk % by Shipping Mode',
                  text=mr['Late_delivery_risk'].round(1))
    fig8.update_traces(textposition='outside')
    st.plotly_chart(fig8, use_container_width=True)

# ---- SLA COMPLIANCE (NEW) ----
st.markdown("#### 📋 SLA Compliance by Shipping Mode")
sla = filtered_df.groupby('Shipping_Mode').agg(
    Total_Orders=('Late_delivery_risk','count'),
    Late_Orders =('Late_delivery_risk','sum')
).reset_index()
sla['SLA_Compliance_%'] = ((sla['Total_Orders'] - sla['Late_Orders'])
                            / sla['Total_Orders'] * 100).round(2)
sla['Late_Risk_%']      = (sla['Late_Orders']
                            / sla['Total_Orders'] * 100).round(2)

col1, col2 = st.columns(2)
with col1:
    fig_sla = px.bar(sla, x='Shipping_Mode', y='SLA_Compliance_%',
                     color='SLA_Compliance_%',
                     color_continuous_scale='Greens',
                     title='✅ SLA Compliance % by Shipping Mode',
                     text=sla['SLA_Compliance_%'].astype(str) + '%')
    fig_sla.update_traces(textposition='outside')
    fig_sla.add_hline(y=80, line_dash='dash', line_color='red',
                      annotation_text='80% SLA Target')
    st.plotly_chart(fig_sla, use_container_width=True)
with col2:
    fig_sla2 = px.pie(sla, names='Shipping_Mode', values='SLA_Compliance_%',
                      title='SLA Compliance Share by Mode', hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_sla2, use_container_width=True)

st.markdown("**📊 SLA Summary Table:**")
st.dataframe(sla[['Shipping_Mode','Total_Orders','Late_Orders',
                   'SLA_Compliance_%','Late_Risk_%']],
             use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 7 — REGIONAL HEATMAP (NEW ✅)
# ============================================================
st.subheader("🌍 Regional & Market Heatmaps")

# Heatmap — Region vs Shipping Mode
heatmap_data = filtered_df.groupby(
    ['Order_Region','Shipping_Mode'])['Late_delivery_risk'].mean().reset_index()
heatmap_data['Late_delivery_risk'] = heatmap_data['Late_delivery_risk'] * 100
heatmap_pivot = heatmap_data.pivot(index='Order_Region',
                                    columns='Shipping_Mode',
                                    values='Late_delivery_risk')
fig_heat = px.imshow(heatmap_pivot,
                     color_continuous_scale='Reds',
                     title='🌍 Late Delivery Risk Heatmap — Region vs Shipping Mode',
                     labels=dict(color='Late Risk %'),
                     text_auto='.1f',
                     aspect='auto')
fig_heat.update_layout(height=450)
st.plotly_chart(fig_heat, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    rr = filtered_df.groupby('Order_Region')['Late_delivery_risk'].mean().reset_index()
    rr['Late_delivery_risk'] = rr['Late_delivery_risk'] * 100
    rr = rr.sort_values('Late_delivery_risk', ascending=True)
    fig9 = px.bar(rr, x='Late_delivery_risk', y='Order_Region', orientation='h',
                  color='Late_delivery_risk', color_continuous_scale='Reds',
                  title='Late Risk % by Region',
                  text=rr['Late_delivery_risk'].round(1))
    fig9.update_traces(textposition='outside')
    st.plotly_chart(fig9, use_container_width=True)
with col2:
    mk = filtered_df.groupby('Market')['Late_delivery_risk'].mean().reset_index()
    mk['Late_delivery_risk'] = mk['Late_delivery_risk'] * 100
    fig10 = px.pie(mk, names='Market', values='Late_delivery_risk',
                   title='Market-wise Logistics Efficiency (Late Risk %)', hole=0.4,
                   color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig10, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 8 — CUSTOMER SEGMENT
# ============================================================
st.subheader("👥 Customer Segment Analysis")
col1, col2 = st.columns(2)
with col1:
    sd = filtered_df.groupby('Customer_Segment')['Delay_Gap'].mean().reset_index()
    fig11 = px.bar(sd, x='Customer_Segment', y='Delay_Gap', color='Customer_Segment',
                   title='Avg Delay by Customer Segment',
                   text=sd['Delay_Gap'].round(2))
    fig11.update_traces(textposition='outside')
    st.plotly_chart(fig11, use_container_width=True)
with col2:
    sr = filtered_df.groupby('Customer_Segment')['Late_delivery_risk'].mean().reset_index()
    sr['Late_delivery_risk'] = sr['Late_delivery_risk'] * 100
    fig12 = px.bar(sr, x='Customer_Segment', y='Late_delivery_risk',
                   color='Customer_Segment',
                   title='Late Risk % by Segment',
                   text=sr['Late_delivery_risk'].round(1))
    fig12.update_traces(textposition='outside')
    st.plotly_chart(fig12, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 9 — GEOGRAPHIC MAP
# ============================================================
st.subheader("🗺️ Geographic Delay Visualization")
map_data = filtered_df.groupby(
    ['Latitude','Longitude','Order_City','Order_Country']).agg(
    Late_Risk   =('Late_delivery_risk','mean'),
    Total_Orders=('Late_delivery_risk','count')).reset_index()
map_data['Late_Risk'] = map_data['Late_Risk'] * 100
fig_map = px.scatter_geo(map_data,
                          lat='Latitude', lon='Longitude',
                          color='Late_Risk', size='Total_Orders',
                          hover_name='Order_City',
                          hover_data={'Order_Country':True,
                                      'Late_Risk':':.1f',
                                      'Total_Orders':True},
                          color_continuous_scale='Reds',
                          title='🌍 Global Late Delivery Risk Map',
                          projection='natural earth')
fig_map.update_layout(height=500)
st.plotly_chart(fig_map, use_container_width=True)
st.markdown("---")

# ============================================================
# MODULE 10 — RAW DATA
# ============================================================
st.subheader("📋 Raw Data Explorer")
st.dataframe(filtered_df[[
    'Order_Date','Shipping_Mode','Order_Region','Market',
    'Customer_Segment','Delivery_Status',
    'Days_for_shipping_real','Days_for_shipment_scheduled',
    'Delay_Gap','Delivery_Class','Late_delivery_risk'
]].head(500), use_container_width=True)

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Filtered Data as CSV",
    data=csv,
    file_name='APL_Filtered_Data.csv',
    mime='text/csv'
)

st.markdown("---")
st.caption("📦 APL Logistics | Live Delivery Performance Dashboard | Built with Streamlit")

if live_mode:
    time.sleep(refresh_rate)
    st.rerun()
