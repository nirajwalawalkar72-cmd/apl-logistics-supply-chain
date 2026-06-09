# ============================================================
# APL Logistics — Complete Streamlit Dashboard
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
div[data-testid="metric-container"] {
    background-color: white;
    border-radius: 12px;
    padding: 10px 15px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #1F4E79;
}
.section-header {
    background: linear-gradient(90deg, #1F4E79, #2E75B6);
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    margin: 10px 0 15px 0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(filepath):
    df = pd.read_csv(filepath, encoding='latin1')
    df.dropna(subset=['Days for shipping (real)',
                       'Days for shipment (scheduled)',
                       'Delivery Status',
                       'Late_delivery_risk'], inplace=True)
    df.columns = (df.columns.str.strip()
                    .str.replace(' ', '_')
                    .str.replace('(', '')
                    .str.replace(')', ''))
    df['Delay_Gap'] = (df['Days_for_shipping_real'] -
                       df['Days_for_shipment_scheduled'])
    def classify(gap):
        if gap > 0:    return 'Delayed'
        elif gap == 0: return 'On-Time'
        else:          return 'Early'
    df['Delivery_Class'] = df['Delay_Gap'].apply(classify)
    start = datetime(2015, 1, 1)
    total_days = (datetime(2018, 12, 31) - start).days
    np.random.seed(42)
    rdays = np.sort(np.random.randint(0, total_days, size=len(df)))
    df['Order_Date']       = [start + timedelta(days=int(d)) for d in rdays]
    df['Order_Year']       = df['Order_Date'].dt.year
    df['Order_Month_Name'] = df['Order_Date'].dt.strftime('%b %Y')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df[df['Latitude'].between(-90, 90) &
            df['Longitude'].between(-180, 180)]
    return df

CSV_PATH = r"H:\NIRAJ\Projects\APL_Logistics_Small.csv"
try:
    df = load_data(CSV_PATH)
except FileNotFoundError:
    st.error("CSV file not found! Update CSV_PATH.")
    st.stop()

# ── SIDEBAR ──────────────────────────────────────────────────
st.sidebar.title("📦 APL Logistics")
st.sidebar.markdown("---")
st.sidebar.subheader("🔴 Live Dashboard")
live_mode    = st.sidebar.toggle("Enable Live Refresh", value=False)
refresh_rate = st.sidebar.slider("Refresh Every (sec)", 5, 60, 15)
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")
st.sidebar.markdown("📅 **Date Range**")
min_date   = df['Order_Date'].min().date()
max_date   = df['Order_Date'].max().date()
start_date = st.sidebar.date_input("From", value=min_date,
                                    min_value=min_date, max_value=max_date)
end_date   = st.sidebar.date_input("To", value=max_date,
                                    min_value=min_date, max_value=max_date)
if start_date > end_date:
    st.sidebar.error("Start must be before End date!")
st.sidebar.markdown("---")
sel_mode = st.sidebar.multiselect("📦 Shipping Mode",
    options=df['Shipping_Mode'].unique().tolist(),
    default=df['Shipping_Mode'].unique().tolist())
sel_region = st.sidebar.multiselect("🌍 Order Region",
    options=df['Order_Region'].unique().tolist(),
    default=df['Order_Region'].unique().tolist())
sel_market = st.sidebar.multiselect("🗺️ Market",
    options=df['Market'].unique().tolist(),
    default=df['Market'].unique().tolist())
sel_segment = st.sidebar.multiselect("👥 Customer Segment",
    options=df['Customer_Segment'].unique().tolist(),
    default=df['Customer_Segment'].unique().tolist())

fdf = df[
    (df['Order_Date'].dt.date >= start_date) &
    (df['Order_Date'].dt.date <= end_date)   &
    (df['Shipping_Mode'].isin(sel_mode))      &
    (df['Order_Region'].isin(sel_region))     &
    (df['Market'].isin(sel_market))           &
    (df['Customer_Segment'].isin(sel_segment))
]
st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(fdf):,}** of **{len(df):,}** records")
st.sidebar.info(f"📅 **{start_date}** → **{end_date}**")

# ── HEADER ───────────────────────────────────────────────────
c1, c2, c3 = st.columns([5, 1, 2])
with c1:
    st.title("📦 APL Logistics — Delivery Performance Dashboard")
    st.markdown("**Global Supply Chain | Delivery & Delay Risk Intelligence**")
with c2:
    if live_mode:
        st.markdown("🔴 **LIVE**")
with c3:
    st.markdown(f"🕐 **{datetime.now().strftime('%d %b %Y %I:%M:%S %p')}**")
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 1 — DELIVERY PERFORMANCE OVERVIEW
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 MODULE 1 — Delivery Performance Overview</div>',
            unsafe_allow_html=True)

on_time_rate = (fdf['Delivery_Class'] == 'On-Time').mean() * 100
late_rate    = (fdf['Delivery_Class'] == 'Delayed').mean() * 100
early_rate   = (fdf['Delivery_Class'] == 'Early').mean()   * 100
avg_delay    = fdf['Delay_Gap'].mean()
late_risk    = fdf['Late_delivery_risk'].mean() * 100
total        = len(fdf)
delayed_cnt  = (fdf['Delivery_Class'] == 'Delayed').sum()
ontime_cnt   = (fdf['Delivery_Class'] == 'On-Time').sum()

st.markdown("##### 📌 On-Time vs Late Delivery KPIs")
c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ On-Time Rate",   f"{on_time_rate:.1f}%",
          delta=f"{on_time_rate - 80:.1f}% vs 80% target", delta_color="normal")
c2.metric("❌ Delayed Rate",   f"{late_rate:.1f}%")
c3.metric("🟢 Early Rate",     f"{early_rate:.1f}%")
c4.metric("📦 Total Orders",   f"{total:,}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("⏱️ Avg Delay Gap",  f"{avg_delay:.2f} days")
c2.metric("🚨 Late Risk",      f"{late_risk:.1f}%")
c3.metric("✅ On-Time Orders", f"{ontime_cnt:,}")
c4.metric("❌ Delayed Orders", f"{delayed_cnt:,}")

st.markdown("")
st.markdown("##### 📋 Average Delay Scorecards")
modes     = fdf['Shipping_Mode'].unique().tolist()
mcols     = st.columns(len(modes))
icons_map = {"Standard Class":"📦","First Class":"✈️",
             "Second Class":"📮","Same Day":"🚀"}
for i, mode in enumerate(modes):
    md   = fdf[fdf['Shipping_Mode'] == mode]
    dlay = md['Delay_Gap'].mean()
    risk = md['Late_delivery_risk'].mean() * 100
    mcols[i].metric(f"{icons_map.get(mode,'📦')} {mode}",
                    f"{dlay:.2f} days",
                    delta=f"Risk: {risk:.1f}%",
                    delta_color="inverse")
st.markdown("")

c1, c2 = st.columns(2)
with c1:
    dc = fdf['Delivery_Class'].value_counts().reset_index()
    dc.columns = ['Class', 'Count']
    f1 = px.bar(dc, x='Class', y='Count', color='Class',
                color_discrete_map={'Delayed':'#e74c3c',
                                    'On-Time':'#2ecc71',
                                    'Early':'#3498db'},
                title='On-Time vs Late vs Early Delivery',
                text='Count')
    f1.update_traces(textposition='outside')
    f1.update_layout(showlegend=False,
                     plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f1, use_container_width=True)
with c2:
    sc = fdf['Delivery_Status'].value_counts().reset_index()
    sc.columns = ['Status', 'Count']
    f2 = px.pie(sc, names='Status', values='Count',
                title='Delivery Status Breakdown', hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set3)
    f2.update_layout(paper_bgcolor='white')
    st.plotly_chart(f2, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    monthly = fdf.groupby('Order_Month_Name').agg(
        Late_Risk=('Late_delivery_risk','mean')).reset_index()
    monthly['Late_Risk'] = monthly['Late_Risk'] * 100
    f3 = px.line(monthly, x='Order_Month_Name', y='Late_Risk',
                 title='📅 Monthly Late Risk Trend (%)',
                 markers=True, color_discrete_sequence=['#e74c3c'])
    f3.add_hline(y=80, line_dash='dash', line_color='blue',
                 annotation_text='80% Target')
    f3.update_layout(xaxis_tickangle=-45,
                     plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f3, use_container_width=True)
with c2:
    yearly = fdf.groupby('Order_Year').agg(
        Total_Orders=('Late_delivery_risk','count'),
        Late_Risk   =('Late_delivery_risk','mean')).reset_index()
    yearly['Late_Risk'] = yearly['Late_Risk'] * 100
    f4 = px.bar(yearly, x='Order_Year', y='Total_Orders',
                color='Late_Risk', color_continuous_scale='Reds',
                title='📅 Yearly Orders & Late Risk',
                text='Total_Orders')
    f4.update_traces(textposition='outside')
    f4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f4, use_container_width=True)
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 2 — DELAY RISK ANALYSIS DASHBOARD
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🚨 MODULE 2 — Delay Risk Analysis Dashboard</div>',
            unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    f5 = px.histogram(fdf, x='Delay_Gap', nbins=20,
                      color_discrete_sequence=['#e74c3c'],
                      title='Delay Gap Histogram (Actual − Scheduled Days)',
                      labels={'Delay_Gap':'Delay Gap (Days)'})
    f5.add_vline(x=0, line_dash='dash', line_color='green',
                 annotation_text='On-Time Line',
                 annotation_position='top right')
    f5.add_vline(x=fdf['Delay_Gap'].mean(), line_dash='dash',
                 line_color='blue',
                 annotation_text=f'Mean:{fdf["Delay_Gap"].mean():.2f}',
                 annotation_position='top left')
    f5.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f5, use_container_width=True)
with c2:
    rc = fdf['Late_delivery_risk'].value_counts().reset_index()
    rc.columns = ['Risk', 'Count']
    rc['Risk'] = rc['Risk'].map({1:'🚨 Late Risk (1)',
                                  0:'✅ No Risk (0)'})
    f6 = px.pie(rc, names='Risk', values='Count',
                title='Late_delivery_risk Distribution', hole=0.45,
                color_discrete_sequence=['#e74c3c','#2ecc71'])
    f6.update_layout(paper_bgcolor='white')
    st.plotly_chart(f6, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    f7 = px.box(fdf, x='Delivery_Status', y='Delay_Gap',
                color='Delivery_Status',
                title='Delay Gap Distribution by Delivery Status',
                color_discrete_sequence=px.colors.qualitative.Set2)
    f7.add_hline(y=0, line_dash='dash', line_color='red',
                 annotation_text='On-Time Line')
    f7.update_layout(showlegend=False,
                     plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f7, use_container_width=True)
with c2:
    sd = fdf.groupby('Delivery_Status').agg(
        Avg_Delay_Gap=('Delay_Gap','mean'),
        Late_Risk_Pct=('Late_delivery_risk','mean')).reset_index()
    sd['Avg_Delay_Gap'] = sd['Avg_Delay_Gap'].round(2)
    sd['Late_Risk_Pct'] = (sd['Late_Risk_Pct'] * 100).round(2)
    f8 = px.bar(sd, x='Avg_Delay_Gap', y='Delivery_Status',
                orientation='h', color='Avg_Delay_Gap',
                color_continuous_scale='RdYlGn_r',
                title='Avg Delay Gap by Delivery Status',
                text=sd['Avg_Delay_Gap'].astype(str))
    f8.update_traces(textposition='outside')
    f8.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f8, use_container_width=True)
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 3 — SHIPPING MODE COMPARISON
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🚚 MODULE 3 — Shipping Mode Comparison</div>',
            unsafe_allow_html=True)

mode_stats = fdf.groupby('Shipping_Mode').agg(
    Total_Orders =('Delay_Gap','count'),
    Avg_Delay_Gap=('Delay_Gap','mean'),
    Late_Risk_Pct=('Late_delivery_risk','mean'),
    Delayed_Count=('Delivery_Class', lambda x: (x=='Delayed').sum())
).reset_index()
mode_stats['Late_Risk_Pct']    = (mode_stats['Late_Risk_Pct']*100).round(2)
mode_stats['Avg_Delay_Gap']    =  mode_stats['Avg_Delay_Gap'].round(2)
mode_stats['SLA_Compliance_%'] = (100-mode_stats['Late_Risk_Pct']).round(2)

c1, c2 = st.columns(2)
with c1:
    f9 = px.bar(mode_stats, x='Shipping_Mode', y='Avg_Delay_Gap',
                color='Avg_Delay_Gap', color_continuous_scale='Reds',
                title='Mode-wise Delay Performance (Avg Delay Gap)',
                text=mode_stats['Avg_Delay_Gap'].astype(str))
    f9.update_traces(textposition='outside')
    f9.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f9, use_container_width=True)
with c2:
    f10 = px.bar(mode_stats, x='Shipping_Mode', y='SLA_Compliance_%',
                 color='SLA_Compliance_%', color_continuous_scale='Greens',
                 title='SLA Compliance % by Shipping Mode',
                 text=mode_stats['SLA_Compliance_%'].astype(str)+'%')
    f10.add_hline(y=80, line_dash='dash', line_color='red',
                  annotation_text='80% SLA Target',
                  annotation_position='top right')
    f10.update_traces(textposition='outside')
    f10.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f10, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    f11 = px.pie(mode_stats, names='Shipping_Mode',
                 values='Late_Risk_Pct',
                 title='Late Risk Share by Shipping Mode', hole=0.45,
                 color_discrete_sequence=px.colors.qualitative.Set2)
    f11.update_layout(paper_bgcolor='white')
    st.plotly_chart(f11, use_container_width=True)
with c2:
    st.markdown("#### 📋 SLA Summary Table")
    st.dataframe(
        mode_stats[['Shipping_Mode','Total_Orders','Avg_Delay_Gap',
                    'Late_Risk_Pct','SLA_Compliance_%','Delayed_Count']]
        .sort_values('SLA_Compliance_%', ascending=False)
        .reset_index(drop=True),
        use_container_width=True)
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 4 — REGIONAL & MARKET HEATMAPS
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🌍 MODULE 4 — Regional & Market Heatmaps</div>',
            unsafe_allow_html=True)

st.markdown("#### 🌍 Late Delivery Risk Heatmap — Region × Shipping Mode")
hmap   = (fdf.groupby(['Order_Region','Shipping_Mode'])
          ['Late_delivery_risk'].mean() * 100)
hpivot = hmap.unstack().round(1)
fheat  = px.imshow(hpivot, color_continuous_scale='Reds',
                   title='Regional Heatmap — Late Risk % (Region × Shipping Mode)',
                   labels=dict(color='Late Risk %'),
                   text_auto='.1f', aspect='auto')
fheat.update_layout(height=620, paper_bgcolor='white',
                    xaxis_title='Shipping Mode',
                    yaxis_title='Order Region')
st.plotly_chart(fheat, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    rr = (fdf.groupby('Order_Region')['Late_delivery_risk']
          .mean()*100).round(2).reset_index()
    rr.columns = ['Region','Late_Risk_%']
    rr = rr.sort_values('Late_Risk_%', ascending=True)
    f12 = px.bar(rr, x='Late_Risk_%', y='Region', orientation='h',
                 color='Late_Risk_%', color_continuous_scale='Reds',
                 title='Regional Delay Index — Late Risk % by Region',
                 text=rr['Late_Risk_%'].astype(str)+'%')
    f12.add_vline(x=rr['Late_Risk_%'].mean(), line_dash='dash',
                  line_color='blue',
                  annotation_text=f'Avg:{rr["Late_Risk_%"].mean():.1f}%')
    f12.update_traces(textposition='outside')
    f12.update_layout(height=600, plot_bgcolor='white',
                      paper_bgcolor='white')
    st.plotly_chart(f12, use_container_width=True)
with c2:
    mk = (fdf.groupby('Market')['Late_delivery_risk']
          .mean()*100).round(2).reset_index()
    mk.columns = ['Market','Late_Risk_%']
    f13 = px.pie(mk, names='Market', values='Late_Risk_%',
                 title='Market-wise Logistics Efficiency (Late Risk %)',
                 hole=0.45,
                 color_discrete_sequence=px.colors.qualitative.Set2)
    f13.update_layout(paper_bgcolor='white')
    st.plotly_chart(f13, use_container_width=True)

    f14 = px.bar(mk.sort_values('Late_Risk_%', ascending=False),
                 x='Market', y='Late_Risk_%',
                 color='Late_Risk_%', color_continuous_scale='Oranges',
                 title='Market-wise Late Delivery Risk %',
                 text=mk.sort_values('Late_Risk_%', ascending=False)
                 ['Late_Risk_%'].astype(str)+'%')
    f14.update_traces(textposition='outside')
    f14.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f14, use_container_width=True)

st.markdown("#### 🗺️ Geographic Delay Visualization")
try:
    mapdf = (fdf.groupby(['Latitude','Longitude',
                           'Order_City','Order_Country'])
             .agg(Late_Risk   =('Late_delivery_risk','mean'),
                  Total_Orders=('Late_delivery_risk','count'))
             .reset_index())
    mapdf['Late_Risk'] = (mapdf['Late_Risk']*100).round(2)
    mapdf = mapdf.dropna(subset=['Latitude','Longitude'])
    mapdf = mapdf[mapdf['Latitude'].between(-90,90) &
                  mapdf['Longitude'].between(-180,180)]
    if len(mapdf) > 0:
        fmap = px.scatter_geo(
            mapdf, lat='Latitude', lon='Longitude',
            color='Late_Risk', size='Total_Orders',
            hover_name='Order_City',
            hover_data={'Order_Country':True,'Late_Risk':':.1f',
                        'Total_Orders':True,'Latitude':False,
                        'Longitude':False},
            color_continuous_scale='Reds',
            title='🌍 Global Late Delivery Risk Map',
            projection='natural earth', size_max=25)
        fmap.update_layout(height=560, paper_bgcolor='white',
                            geo=dict(showframe=True,
                                     showcoastlines=True,
                                     coastlinecolor='DarkGray',
                                     showland=True,
                                     landcolor='#f0f0f0',
                                     showocean=True,
                                     oceancolor='#d6eaf8',
                                     showcountries=True,
                                     countrycolor='gray'))
        st.plotly_chart(fmap, use_container_width=True)
        st.info(f"🌍 Displaying **{len(mapdf):,}** delivery locations")
    else:
        st.warning("No valid geographic data for current filters.")
except Exception as e:
    st.error(f"Map Error: {str(e)}")
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 5 — CUSTOMER SEGMENT ANALYSIS
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">👥 MODULE 5 — Customer Segment Analysis</div>',
            unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    segD = fdf.groupby('Customer_Segment')['Delay_Gap'].mean().reset_index()
    f15  = px.bar(segD, x='Customer_Segment', y='Delay_Gap',
                  color='Customer_Segment',
                  title='Avg Delay Gap by Customer Segment',
                  text=segD['Delay_Gap'].round(2))
    f15.update_traces(textposition='outside')
    f15.update_layout(showlegend=False,
                      plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f15, use_container_width=True)
with c2:
    segR = fdf.groupby('Customer_Segment').agg(
        Late_Risk_Pct=('Late_delivery_risk','mean'),
        SLA_Exposure =('Late_delivery_risk','sum'),
        Total_Orders =('Late_delivery_risk','count')).reset_index()
    segR['Late_Risk_Pct']    = (segR['Late_Risk_Pct']*100).round(2)
    segR['SLA_Compliance_%'] = (100-segR['Late_Risk_Pct']).round(2)
    f16 = px.bar(segR, x='Customer_Segment', y='Late_Risk_Pct',
                 color='Customer_Segment',
                 title='Late Risk % by Customer Segment',
                 text=segR['Late_Risk_Pct'].astype(str)+'%')
    f16.add_hline(y=segR['Late_Risk_Pct'].mean(), line_dash='dash',
                  line_color='blue',
                  annotation_text=f'Avg:{segR["Late_Risk_Pct"].mean():.1f}%')
    f16.update_traces(textposition='outside')
    f16.update_layout(showlegend=False,
                      plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(f16, use_container_width=True)
st.markdown("---")

# ══════════════════════════════════════════════════════════════
# MODULE 6 — RAW DATA EXPLORER
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📋 MODULE 6 — Raw Data Explorer</div>',
            unsafe_allow_html=True)
st.dataframe(
    fdf[['Order_Date','Shipping_Mode','Order_Region','Market',
         'Customer_Segment','Delivery_Status',
         'Days_for_shipping_real','Days_for_shipment_scheduled',
         'Delay_Gap','Delivery_Class','Late_delivery_risk']].head(500),
    use_container_width=True)
csv_export = fdf.to_csv(index=False).encode('utf-8')
st.download_button(label="⬇️ Download Filtered Data as CSV",
                   data=csv_export,
                   file_name='APL_Filtered_Data.csv',
                   mime='text/csv')
st.markdown("---")
st.caption("📦 APL Logistics | Delivery Performance Dashboard | KWE Group | 2024")

if live_mode:
    time.sleep(refresh_rate)
    st.rerun()
