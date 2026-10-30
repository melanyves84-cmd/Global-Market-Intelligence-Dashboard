"""Design B: polished light financial dashboard, with restrained blue accents."""
import streamlit as st

NAVY='#17344D'
BLUE='#215F9A'
TEAL='#14856D'
RED='#CC4D58'

CSS="""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root {--brand:#215F9A;--ink:#17344D;--muted:#6A7B90;--canvas:#F5F8FC;--panel:#FFFFFF;}
html,body,[class*="css"],.stApp {font-family:'DM Sans',Arial,sans-serif!important;}
.stApp {background:#F5F8FC;color:#17344D;}
[data-testid="stHeader"] {background:rgba(245,248,252,.94);border-bottom:1px solid #E3EAF2;}
[data-testid="stSidebar"] {background:#FFFFFF;border-right:1px solid #DFE8F2;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#556E88;}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {color:#17344D!important;}
[data-testid="stAppViewContainer"] > .main .block-container {max-width:1450px;padding-top:2.0rem;padding-bottom:4rem;}
.block-container h1,.block-container h2,.block-container h3 {font-family:'Manrope','DM Sans',sans-serif;letter-spacing:-.025em;color:#17344D;}
.block-container h1 {font-size:2rem;font-weight:800;}
.block-container h2 {font-size:1.35rem;font-weight:750;}
.block-container h3 {font-size:1.1rem;font-weight:700;}
[data-testid="stCaptionContainer"] {color:#7B8DA4;}
[data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:14px;}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid #E3EAF3;border-radius:14px;padding:16px 18px;box-shadow:0 4px 18px rgba(26,59,95,.035);}
[data-testid="stMetricLabel"] {color:#687D96;}
[data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;font-weight:800;color:#17344D;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {border:1px solid #E4EAF2;border-radius:14px;overflow:hidden;background:white;box-shadow:0 5px 20px rgba(25,55,90,.035);}
[data-testid="stPlotlyChart"] {padding:8px;}
[data-testid="stSelectbox"], [data-testid="stMultiSelect"], [data-testid="stRadio"] {color:#17344D;}
[data-baseweb="select"] > div,[data-testid="stFileUploader"] section {border-radius:9px!important;border-color:#CFDCEC!important;}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"] {border-radius:9px;background:#215F9A;border:1px solid #215F9A;}
.stDownloadButton button {border-radius:9px;color:#215F9A;border:1px solid #C5D8EA;background:#EFF7FD;font-weight:600;}
[data-testid="stAlert"] {border-radius:11px;}
.hero {background:linear-gradient(111deg,#FFFFFF 0%,#EFF7FD 100%);border:1px solid #DCEAF7;border-radius:19px;padding:22px 28px;margin-bottom:14px;box-shadow:0 7px 28px rgba(33,95,154,.04);}
.hero .eyebrow {font-size:.71rem;letter-spacing:.17em;font-weight:800;color:#215F9A;}
.hero .headline {font-family:'Manrope',sans-serif;font-size:1.9rem;font-weight:800;color:#17344D;letter-spacing:-.045em;line-height:1.35;margin:.35rem 0;}
.hero .subtitle {font-size:.92rem;color:#60778F;}
.brand-sidebar {font-family:'Manrope',sans-serif;font-size:1.12rem;color:#17344D;font-weight:800;letter-spacing:-.03em;margin:.3rem 0 1rem;}
.brand-sidebar span {color:#215F9A;}
.section-eyebrow {font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:#215F9A;font-weight:800;margin-top:12px;}

/* Design B Plus — refined layout, restrained editorial design */
[data-testid="stAppViewContainer"] {background:radial-gradient(ellipse 750px 350px at 100% 0%,#E9F3FD 0%,transparent 70%),#F6F9FD;}
[data-testid="stAppViewContainer"] > .main .block-container {max-width:1530px;padding:1.2rem 2.4rem 5rem;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFF 100%);}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.85rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {border-radius:10px;transition:background .15s;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:#EDF5FE;}
[data-testid="stSidebar"] [data-testid="stRadio"] p {font-weight:550;}
[data-testid="stSidebar"] hr {border-color:#E5EDF5;}
[data-testid="stMetric"] {position:relative;overflow:hidden;border:1px solid #DEE9F4;box-shadow:0 10px 28px rgba(26,59,95,.045);border-radius:16px;padding:21px 23px;}
[data-testid="stMetric"]:before {content:'';position:absolute;height:3px;top:0;left:0;right:0;background:linear-gradient(90deg,#215F9A,#8DBDDF);}
[data-testid="stMetricValue"] {font-size:1.85rem;letter-spacing:-.04em;}
[data-testid="stPlotlyChart"] {border:1px solid #E2EBF5;border-radius:18px;box-shadow:0 10px 34px rgba(26,59,95,.04);padding:14px;}
[data-testid="stDataFrame"] {border:1px solid #E2EBF5;border-radius:16px;box-shadow:0 8px 25px rgba(26,59,95,.035);}
[data-testid="stSelectbox"] label p,[data-testid="stMultiSelect"] label p,[data-testid="stRadio"] > label p {font-size:.82rem;font-weight:700;color:#526A84;}
[data-baseweb="select"] > div {min-height:44px;border-radius:11px!important;border-color:#D4E2F0!important;background:#FFFFFF;}
[data-testid="stFileUploader"] section {background:#FBFDFF;border:1px dashed #B9CEE4!important;border-radius:15px!important;}
.stButton button,.stDownloadButton button {min-height:42px;border-radius:11px!important;font-weight:700;}
.block-container h2 {border-bottom:1px solid #E2EAF3;padding-bottom:.65rem;margin-top:1.3rem;}
.block-container h3 {margin-top:.95rem;}
.hero {position:relative;overflow:hidden;background:linear-gradient(112deg,#FFFFFF 14%,#F0F7FF 66%,#E3F1FD 100%);border:1px solid #D9E8F6;border-radius:23px;padding:29px 32px;margin:12px 0 20px;box-shadow:0 12px 40px rgba(33,95,154,.065);}
.hero:after {content:'';position:absolute;width:250px;height:250px;right:-100px;top:-100px;border:45px solid rgba(33,95,154,.055);border-radius:50%;pointer-events:none;}
.hero .eyebrow {display:inline-flex;border:1px solid #C9DFF3;background:#FFFFFF;border-radius:100px;padding:6px 11px;letter-spacing:.13em;font-size:.66rem;}
.hero .headline {font-size:clamp(1.75rem,3vw,2.4rem);letter-spacing:-.052em;margin:.6rem 0 .35rem;}
.hero .subtitle {font-size:.92rem;line-height:1.65;max-width:960px;}
.market-strip {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:0 0 24px;}
.market-tile {background:#FFFFFF;border:1px solid #E0EAF5;border-radius:15px;padding:14px 18px;box-shadow:0 7px 21px rgba(24,60,97,.035);}
.market-tile .label {font-size:.7rem;color:#647F99;text-transform:uppercase;letter-spacing:.10em;font-weight:800;}
.market-tile .metric {font:800 1rem 'Manrope',Arial,sans-serif;color:#17344D;margin-top:5px;}
.market-tile .small {color:#8193A7;font-size:.73rem;margin-top:4px;}
.data-status {display:inline-flex;align-items:center;gap:7px;font-size:.75rem;color:#55728E;background:#EDF5FC;border:1px solid #D8E8F7;border-radius:999px;padding:6px 11px;}
.data-status .dot {background:#279978;width:7px;height:7px;border-radius:50%;}
@media(max-width:800px) {.market-strip{grid-template-columns:1fr;}.hero{padding:21px;}.hero .headline{font-size:1.72rem;}[data-testid="stAppViewContainer"] > .main .block-container{padding:1.1rem 1rem 3rem;}}
footer {visibility:hidden;}
</style>
"""

def apply_theme():
    st.markdown(CSS,unsafe_allow_html=True)

def hero():
    st.markdown('''<div class="hero"><div class="eyebrow">GLOBAL EQUITY ANALYTICS</div><div class="headline">Market Intelligence <span style="color:#215F9A">/ Sector Rotation</span></div><div class="subtitle">United States · Europe · Mainland China &nbsp;|&nbsp; Daily price trends · Weekly relative strength · Coverage-aware analytics</div></div>''',unsafe_allow_html=True)

def market_strip():
    st.markdown('''<div class="market-strip"><div class="market-tile"><div class="label">01 / United States</div><div class="metric">S&amp;P 500</div><div class="small">Daily prices · weekly signals</div></div><div class="market-tile"><div class="label">02 / Europe</div><div class="metric">STOXX Europe 600</div><div class="small">11 ICB industries · coverage-aware</div></div><div class="market-tile"><div class="label">03 / Mainland China</div><div class="metric">CSI 300</div><div class="small">11 mapped sectors · import supported</div></div></div>''',unsafe_allow_html=True)

def plot(fig,**kwargs):
    fig.update_layout(
       template='plotly_white',paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
       font=dict(family='DM Sans, Arial, sans-serif',color=NAVY,size=12),
       title_font=dict(family='Manrope, Arial, sans-serif',size=18,color=NAVY),
       margin=dict(l=42,r=30,t=67,b=48),
       xaxis=dict(showgrid=True,gridcolor='#EDF2F8',zeroline=False,showline=False),
       yaxis=dict(showgrid=True,gridcolor='#EDF2F8',zeroline=False,showline=False),
       hoverlabel=dict(bgcolor='#FFFFFF',font_color=NAVY),
       legend=dict(bgcolor='rgba(255,255,255,.8)',orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1),hovermode='x unified')
    # Blue first trace + pleasant comparison palette; preserve heatmap/diverging scale.
    if fig.data and all(getattr(t,'type','')=='scatter' for t in fig.data):
        palette=['#215F9A','#17A68A','#E4A846','#6F8BC4','#B372B6','#67778A']
        for i,trace in enumerate(fig.data):trace.line.color=palette[i%len(palette)];trace.line.width=2.5
    st.plotly_chart(fig,**kwargs)
