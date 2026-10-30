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
footer {visibility:hidden;}
</style>
"""

def apply_theme():
    st.markdown(CSS,unsafe_allow_html=True)

def hero():
    st.markdown('''<div class="hero"><div class="eyebrow">GLOBAL EQUITY ANALYTICS</div><div class="headline">Market Intelligence <span style="color:#215F9A">/ Sector Rotation</span></div><div class="subtitle">United States · Europe · Mainland China &nbsp;|&nbsp; Daily price trends · Weekly relative strength · Coverage-aware analytics</div></div>''',unsafe_allow_html=True)

def plot(fig,**kwargs):
    fig.update_layout(
       template='plotly_white',paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
       font=dict(family='DM Sans, Arial, sans-serif',color=NAVY,size=12),
       title_font=dict(family='Manrope, Arial, sans-serif',size=18,color=NAVY),
       margin=dict(l=45,r=25,t=62,b=50),
       xaxis=dict(showgrid=True,gridcolor='#EDF2F8',zeroline=False,showline=False),
       yaxis=dict(showgrid=True,gridcolor='#EDF2F8',zeroline=False,showline=False),
       hoverlabel=dict(bgcolor='#FFFFFF',font_color=NAVY),
       legend=dict(bgcolor='rgba(255,255,255,.8)'))
    # Blue first trace + pleasant comparison palette; preserve heatmap/diverging scale.
    if fig.data and all(getattr(t,'type','')=='scatter' for t in fig.data):
        palette=['#215F9A','#17A68A','#E4A846','#6F8BC4','#B372B6','#67778A']
        for i,trace in enumerate(fig.data):trace.line.color=palette[i%len(palette)];trace.line.width=2.5
    st.plotly_chart(fig,**kwargs)
