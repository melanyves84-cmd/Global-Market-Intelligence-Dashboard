"""US sector rotation: daily visualizations and weekly analytical signals."""
import io
from datetime import date, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sector_data import read_prices, weekly_completed
from ui_theme import apply_theme, hero, plot, market_strip
import extension
from company_explorer import company_page
from pattern_scanner import page as pattern_scanner_page
from extension import (REGION_SECTORS, REGION_BENCHMARK, GICS_11, make_catalog, read_catalog, global_rotation_page, mapping_page)

st.set_page_config(page_title="Global Sector Rotation",page_icon="📈",layout="wide")
BLUE="#215F9A"
SECTORS={
"Information Technology":"XLK","Financials":"XLF","Healthcare":"XLV",
"Consumer Discretionary":"XLY","Communication Services":"XLC","Industrials":"XLI",
"Consumer Staples":"XLP","Energy":"XLE","Utilities":"XLU","Real Estate":"XLRE","Materials":"XLB"}
# Analytical ETF proxies, not exact indices or exclusive lists of S&P 500 members.
SUBSECTORS={
"Semiconductors & chip equipment":"SOXX","Software & cloud":"IGV","IT services & cybersecurity":"CIBR","Hardware & electronics":"XSD",
"Banks":"KBE","Insurance":"KIE","Capital markets & asset management":"IAI","Consumer finance & payments":"IPAY",
"Pharmaceuticals":"IHE","Biotechnology":"XBI","Medical equipment & diagnostics":"IHI","Healthcare providers & services":"IHF",
"Automotive & EV":"CARZ","Retail & e-commerce":"XRT","Hotels, restaurants & leisure":"PEJ","Apparel & luxury":None,"Household durables":"XHB",
"Digital advertising & internet platforms":"FDN","Telecommunications":"IYZ","Media & entertainment":"PBS","Video games":"ESPO",
"Aerospace & defense":"ITA","Machinery & automation":"PAVE","Construction & engineering":"PKB","Transportation & logistics":"IYT","Business services":None,
"Food & beverages":"PBJ","Grocery & essential retail":None,"Household & personal products":None,"Tobacco":None,
"Oil & gas exploration":"XOP","Integrated oil & gas":"XLE","Refining & pipelines":"AMLP","Oilfield equipment & services":"OIH",
"Electric utilities":"XLU","Gas & water utilities":"CGW","Independent power & renewable electricity":"ICLN",
"Industrial & logistics REITs":"INDS","Data center & telecom tower REITs":"SRVR","Residential & retail REITs":"REZ","Other property & real estate services":"VNQ",
"Chemicals":"XLB","Metals & mining":"XME","Construction materials":"PKB","Packaging & forest products":"WOOD"}
MAP={
"Information Technology":["Semiconductors & chip equipment","Software & cloud","IT services & cybersecurity","Hardware & electronics"],
"Financials":["Banks","Insurance","Capital markets & asset management","Consumer finance & payments"],
"Healthcare":["Pharmaceuticals","Biotechnology","Medical equipment & diagnostics","Healthcare providers & services"],
"Consumer Discretionary":["Automotive & EV","Retail & e-commerce","Hotels, restaurants & leisure","Apparel & luxury","Household durables"],
"Communication Services":["Digital advertising & internet platforms","Telecommunications","Media & entertainment","Video games"],
"Industrials":["Aerospace & defense","Machinery & automation","Construction & engineering","Transportation & logistics","Business services"],
"Consumer Staples":["Food & beverages","Grocery & essential retail","Household & personal products","Tobacco"],
"Energy":["Oil & gas exploration","Integrated oil & gas","Refining & pipelines","Oilfield equipment & services"],
"Utilities":["Electric utilities","Gas & water utilities","Independent power & renewable electricity"],
"Real Estate":["Industrial & logistics REITs","Data center & telecom tower REITs","Residential & retail REITs","Other property & real estate services"],
"Materials":["Chemicals","Metals & mining","Construction materials","Packaging & forest products"]}
# Regional choices are ETF proxies, not perfectly harmonized GICS index sectors.
# Unknown/unverified coverage is deliberately None; users can supply a custom CSV series.
EUROPE_SECTORS={
"Information Technology":"EXV3.DE", "Financials":"EXV1.DE", "Healthcare":"EXV4.DE",
"Consumer Discretionary":"EXV5.DE", "Communication Services":"EXV2.DE",
"Industrials":"EXH4.DE", "Consumer Staples":"EXH3.DE", "Energy":"EXH1.DE",
"Utilities":"EXH9.DE", "Real Estate":"EXI5.DE", "Materials":None}
CHINA_SECTORS={
"Information Technology":"512480.SS", "Financials":None, "Healthcare":"512010.SS",
"Consumer Discretionary":None, "Communication Services":None,
"Industrials":None,"Consumer Staples":None,"Energy":None,"Utilities":None,
"Real Estate":None,"Materials":None}
REGIONS={
"United States":{"benchmark":"SPY","sectors":SECTORS,"subsectors":SUBSECTORS,"currency":"USD","label":"S&P 500 (SPY)","extra":["RSP"]},
"Europe":{"benchmark":"EU_STOXX600","sectors":REGION_SECTORS["Europe"],"subsectors":{},"currency":"EUR","label":"STOXX Europe 600 official industry indices (CSV)","extra":[]},
"China (mainland A-shares)":{"benchmark":"CN_CSI300","sectors":REGION_SECTORS["China (mainland A-shares)"],"subsectors":{"Semiconductors":"512480.SS","CSI 300 Pharmaceuticals":"512010.SS"},"currency":"CNY","label":"CSI 300 (510300.SS)","extra":[]}}
# Country-specific mapping intentionally avoids liquidated Global X MSCI China sector ETFs.

PERIODS={"1M":32,"3M":96,"6M":190,"1Y":365,"2Y":730,"3Y":1095,"4Y":1461,"5Y":1827}

@st.cache_data(ttl=3600,show_spinner="Fetching daily adjusted ETF prices…")
def yahoo_prices(tickers):
    import yfinance as yf
    raw=yf.download(list(tickers),start=(date.today()-timedelta(days=2000)).isoformat(),
                    interval="1d",auto_adjust=True,progress=False,threads=True)
    if raw is None or raw.empty: raise RuntimeError("Provider returned no prices")
    close=raw["Close"] if isinstance(raw.columns,pd.MultiIndex) else raw[["Close"]].rename(columns={"Close":tickers[0]})
    if isinstance(close,pd.Series): close=close.to_frame(tickers[0])
    close.index=pd.to_datetime(close.index).tz_localize(None).normalize()
    return close.sort_index()

def import_csv(upload):
    return read_prices(upload)

def weekly(prices):
    # W-FRI buckets: last available trading close within each week (holidays allowed).
    return weekly_completed(prices).dropna(how='all')

def returns_for_horizon(w, weeks):
    # Week-to-week comparison, exactly `weeks` weekly observations back where available.
    if len(w)<weeks+1: return pd.Series(index=w.columns,dtype=float)
    latest=w.iloc[-1]; prior=w.iloc[-weeks-1]
    r=latest/prior-1
    return r.where(latest.notna()&prior.notna())

def signals(w, benchmark):
    # 4-week vs benchmark, plus 13-week and weekly acceleration.
    a=returns_for_horizon(w,4)
    b=returns_for_horizon(w,13)
    c=returns_for_horizon(w,1)
    if benchmark not in a or pd.isna(a[benchmark]): return pd.DataFrame()
    frame=pd.DataFrame({'4W return':a,'13W return':b,'Weekly change':c})
    frame['4W relative (pp)']=100*(frame['4W return']-a[benchmark])
    frame['13W relative (pp)']=100*(frame['13W return']-b[benchmark])
    frame['Rotation score (pp)']=0.6*frame['4W relative (pp)']+0.4*frame['13W relative (pp)']
    frame['Trend']=np.select([frame['Rotation score (pp)']>2,frame['Rotation score (pp)']< -2],['Leading','Lagging'],default='Neutral')
    return frame

apply_theme()
hero()
market_strip()
st.caption('Daily price charts · Weekly rotation signals · US / Europe / Mainland China · Region-local ETF pricing')
with st.sidebar:
    st.markdown('<div class="brand-sidebar">◈ GLOBAL <span>MARKETS</span></div>',unsafe_allow_html=True)
    st.header('Data & settings')
    region=st.selectbox('Market',list(REGIONS),index=0)
    cfg=REGIONS[region]
    sector_map=cfg['sectors']; benchmark=cfg['benchmark']; currency=cfg['currency']; sub_map=cfg['subsectors']
    eu_mode = st.radio('European data method', ['Official STOXX industry indices (CSV)', 'Legacy European ETF proxies (online)'], index=0) if region == 'Europe' else 'Official STOXX industry indices (CSV)'
    if region == 'Europe' and eu_mode.startswith('Legacy'):
        extension.REGION_BENCHMARK['Europe'] = 'EXSA.DE'
        active_europe = EUROPE_SECTORS
        cfg = {**cfg, 'benchmark':'EXSA.DE', 'label':'STOXX Europe 600 ETF proxy (EXSA.DE)', 'sectors':active_europe}
    else:
        extension.REGION_BENCHMARK['Europe'] = 'EU_STOXX600'
        active_europe = REGION_SECTORS['Europe']
    cn_mode = st.radio('China data method', ['CSI 300 GICS-style 11-sector history (CSV)', 'CSI 300 ETF benchmark and selected proxies (online)'], index=0) if region.startswith('China') else ''
    if region.startswith('China') and cn_mode.startswith('CSI 300 ETF'):
        extension.REGION_BENCHMARK[region] = '510300.SS'
        cfg = {**cfg, 'benchmark':'510300.SS', 'label':'CSI 300 ETF proxy (510300.SS)', 'sectors':CHINA_SECTORS}
    elif region.startswith('China'):
        extension.REGION_BENCHMARK[region] = 'CN_CSI300'
    benchmark=cfg['benchmark']
    source=st.radio('Source',['Yahoo Finance (online)','Upload daily CSV (offline)'],index=1 if (region=='Europe' and eu_mode.startswith('Official')) or (region.startswith('China') and cn_mode.startswith('CSI 300 GICS')) else 0)
    upload=st.file_uploader('CSV: Date,Ticker,Close',type='csv') if source.startswith('Upload') else None
    page=st.radio('Page',['Global heatmap','Market overview','Sector history','Weekly rotation','Subsector explorer','Company Explorer','Ascending Triangle Scanner','Sector data catalog','Methodology'])
    mapping_file=st.file_uploader('Optional: sector mapping CSV',type='csv',key='mapping')
    try:
        catalog=read_catalog(mapping_file)
    except ValueError as e:
        st.error(f'Invalid mapping file: {e}')
        catalog=make_catalog()
    if region=='Europe' and eu_mode.startswith('Legacy'):
        catalog.loc[catalog.Region=='Europe','Ticker']=catalog.loc[catalog.Region=='Europe','Sector'].map(EUROPE_SECTORS).fillna('')
    if region.startswith('China') and cn_mode.startswith('CSI 300 ETF'):
        catalog.loc[catalog.Region==region,'Ticker']=catalog.loc[catalog.Region==region,'Sector'].map(CHINA_SECTORS).fillna('')
    region_map=catalog[catalog.Region==region].set_index('Sector')['Ticker'].to_dict()
    sector_map={sector:(region_map.get(sector) or None) for sector in GICS_11}
    st.caption('China official-style mode requires licensed or reconstructed CSI 300 GICS-classified sector histories as CSV. CN_CSI300_* are local placeholders, not real market tickers. European official mode uses imported STOXX ICB industry index levels. EU_S600_* are CSV identifiers, not Yahoo tickers. Legacy ETF mode retains the previous proxy method. Never mix price-only index levels with dividend-adjusted ETF returns.')

if page=='Ascending Triangle Scanner':
    pattern_scanner_page()
    st.stop()

requested=list(dict.fromkeys([v for v in REGION_BENCHMARK.values() if not v.startswith(('EU_','CN_'))]+[t for t in catalog.Ticker.tolist() if t and not t.startswith(('EU_','CN_'))]+cfg['extra']+[t for t in sub_map.values() if t]))
prices=pd.DataFrame()
try:
    if source.startswith('Yahoo'):
        prices=yahoo_prices(tuple(requested))
    elif upload is not None:
        prices=import_csv(upload)
except Exception as e:
    st.error(f'Data unavailable: {e}. Switch to CSV mode or verify network permission.')

if page=='Company Explorer':
    company_page()
    st.stop()

if page=='Sector data catalog':
    mapping_page(catalog)
    st.stop()

if page=='Methodology':
    st.subheader('Calculation methodology')
    st.markdown('''- **Market selector:** US uses SPY, Europe uses officially classified STOXX Europe 600 ICB industry indices in CSV mode, China supports CSI 300 GICS-style sector CSV imports (and an optional 510300.SS ETF proxy mode). European and Chinese sector coverage requires correctly mapped series; do not interpret absent rows as zero. Unmapped sectors remain unscored.\n- **Daily charts:** one observation per trading day, using daily closing prices. With `auto_adjust=True`, the online provider adjusts historical prices for distributions and splits where data permit.
- **Weekly rotation:** daily prices are sampled to **the last available trading close in each Friday-ending week**, avoiding fixed calendar-day assumptions around market holidays.
- **4W / 13W:** weekly close divided by the close 4 or 13 completed weekly observations earlier, minus one.
- **Relative return:** sector return minus SPY return in percentage points. **Rotation score:** 60% × 4-week relative return + 40% × 13-week relative return.
- **Signals:** Leading above +2 percentage points, Lagging below −2, otherwise Neutral. These thresholds are illustrative analytical rules, not investment advice.
- **Flows:** relative price performance is **not** evidence of net fund inflows. ETF flow data and index weights require separate licensed sources.
- **Equal weight (US only):** RSP is an ETF proxy for equal-weight S&P 500; an ex-top-10 index needs independently calculated historical constituents and weights.
- **Subsectors:** US offers the original 45 analytical groups; Europe and China show the few explicitly configured proxies and allow CSV extensions. Industry ETF proxies are not exact GICS S&P 500 subsector indices and can overlap sectors or contain non-index constituents.
- **Incomplete weeks:** the current week is always excluded from weekly analysis, including on Friday before the close.
- **Offline:** upload a long-format CSV containing `Date,Ticker,Close`, for example `2026-10-29,XLK,250.5`; add all tickers to be compared. No sample returns are fabricated.''')
    st.download_button('Download CSV template',f'Date,Ticker,Close\n2026-01-02,{benchmark},\n','daily_prices_template.csv')
    st.dataframe(pd.DataFrame([{'Sector':k,'ETF proxy':v or 'Not mapped'} for k,v in sector_map.items()]),hide_index=True)
    st.stop()

if prices.empty:
    st.info('No market-data series loaded. Use a permitted external data connection or upload a CSV with actual daily ETF closes. Historical returns will appear after loading data.')
    st.stop()
prices=prices.apply(pd.to_numeric,errors='coerce').sort_index()
prices=prices.loc[:,prices.notna().any()]
if len(prices): st.caption(f'Data availability: {prices.index.min():%d %b %Y} – {prices.index.max():%d %b %Y} · {len(prices)} daily rows · {len(prices.columns)} tickers')

if page=='Global heatmap':
    global_rotation_page(prices, catalog)

elif page=='Market overview':
    st.subheader(f'{region} | Sector overview')
    st.caption('Only sectors with configured and downloaded price series are ranked; missing categories are explicitly not inferred.')
    window=st.selectbox('Performance window',['1M','3M','6M','1Y'],index=1)
    cutoff=prices.index.max()-pd.Timedelta(days=PERIODS[window])
    base=prices.loc[prices.index<=cutoff].tail(1)
    if base.empty: st.warning('Not enough daily history for the selected period'); st.stop()
    rets=((prices.iloc[-1]/base.iloc[0])-1)*100
    bench=rets.get(benchmark,np.nan)
    rows=[]
    for name,tkr in sector_map.items():
        if tkr and tkr in rets and pd.notna(rets[tkr]):
            rows.append({'Sector':name,'ETF':tkr,'Return %':rets[tkr],'vs benchmark (pp)':rets[tkr]-bench})
    summary=pd.DataFrame(rows).sort_values('vs benchmark (pp)',ascending=False)
    if summary.empty: st.warning('No configured sector prices available. Upload region-specific ETF prices or try the online provider.'); st.stop()
    m1,m2,m3=st.columns(3)
    m1.metric('Tracked sectors',f'{len(summary)} / 11')
    m2.metric('Local benchmark',f'{bench:+.2f}%' if pd.notna(bench) else 'N/A',help=f'{cfg["label"]} over the selected window')
    m3.metric('Leading sectors',str(int((summary['vs benchmark (pp)']>0).sum())) if pd.notna(bench) else 'N/A')
    c1,c2=st.columns(2)
    with c1:
        fig=px.bar(summary,x='vs benchmark (pp)',y='Sector',orientation='h',color='vs benchmark (pp)',color_continuous_scale='RdBu',color_continuous_midpoint=0,title='Relative returns vs local market benchmark')
        fig.update_layout(yaxis={'categoryorder':'total ascending'},coloraxis_showscale=False)
        plot(fig,use_container_width=True)
    with c2:
        st.dataframe(summary.style.format({'Return %':'{:+.2f}','vs benchmark (pp)':'{:+.2f}'}),hide_index=True,use_container_width=True)
    st.caption('Performance uses adjusted prices where provided. This view is daily-price-based, while the separate rotation view uses weekly observations.')

elif page=='Sector history':
    st.subheader(f'{region} | Daily historical sector charts')
    c1,c2,c3=st.columns(3)
    with c1: sector=st.selectbox('Sector',[k for k,v in sector_map.items() if v])
    with c2: years=st.selectbox('History',['1M','3M','6M','1Y','2Y','3Y','4Y','5Y'],index=3)
    with c3: compare=st.multiselect('Compare with',list(dict.fromkeys([benchmark]+cfg['extra']+[v for v in sector_map.values() if v])),default=[benchmark])
    ticker=sector_map[sector]
    cols=[x for x in dict.fromkeys([ticker]+compare) if x in prices]
    if ticker not in prices: st.warning(f'No daily data for {ticker}'); st.stop()
    chart=prices[cols].loc[prices.index>=prices.index.max()-pd.Timedelta(days=PERIODS[years])].copy()
    chart=chart.dropna(how='all')
    if chart.empty: st.warning('Insufficient data'); st.stop()
    first=chart.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)
    indexed=100*chart.divide(first)
    fig=go.Figure()
    for t in cols: fig.add_trace(go.Scatter(x=indexed.index,y=indexed[t],name=t,mode='lines'))
    fig.update_layout(title=f'{region}: {sector} | Daily indexed performance (start=100)',xaxis_title='Trading date',yaxis_title='Indexed adjusted close',hovermode='x unified',height=520)
    plot(fig,use_container_width=True)
    st.download_button('Export selected daily chart data',chart.to_csv().encode(),'daily_sector_prices.csv','text/csv')

elif page=='Weekly rotation':
    st.subheader(f'{region} | Weekly sector rotation analysis')
    w=weekly(prices)
    choices=w.index
    only_completed=st.checkbox('Exclude current incomplete week',value=True)
    # Completed Friday-ending weeks are enforced in weekly() for reproducibility.
    score=signals(w, benchmark)
    if score.empty: st.warning('At least 14 weekly observations for SPY and sector prices are required.'); st.stop()
    out=[]
    for sector,tkr in sector_map.items():
        if tkr and tkr in score.index:
            out.append({'Sector':sector,'Ticker':tkr,**score.loc[tkr].to_dict()})
    if not out: st.warning('No mapped sector has sufficient weekly history.'); st.stop()
    df=pd.DataFrame(out).sort_values('Rotation score (pp)',ascending=False)
    st.caption(f'Last completed weekly observation: {w.index[-1]:%d %b %Y}. Positive relative returns = outperformance, not proven fund inflows.')
    fig=px.bar(df,y='Sector',x='Rotation score (pp)',orientation='h',color='Rotation score (pp)',color_continuous_scale='RdBu',color_continuous_midpoint=0)
    fig.update_layout(yaxis={'categoryorder':'total ascending'},coloraxis_showscale=False,height=530)
    plot(fig,use_container_width=True)
    fmt={c:'{:+.2f}' for c in ['4W relative (pp)','13W relative (pp)','Rotation score (pp)']}
    fmt.update({'4W return':'{:.2%}','13W return':'{:.2%}','Weekly change':'{:.2%}'})
    st.dataframe(df.style.format(fmt),hide_index=True,use_container_width=True)
    st.download_button('Export weekly rotation results',df.to_csv(index=False).encode(),'weekly_sector_rotation.csv','text/csv')

elif page=='Subsector explorer':
    st.subheader(f'{region} | Subsector ETF proxy explorer')
    if region=='United States':
        sector=st.selectbox('Parent sector',list(MAP))
        choices=MAP[sector]
    else:
        choices=list(sub_map)
        st.info('Limited verified subsector coverage in this region. Missing categories are not fabricated; upload custom data to extend coverage.')
        if not choices: st.stop()
    selected=st.selectbox('Subsector',choices)
    proxy=sub_map[selected]
    if proxy is None:
        st.info('No satisfactory single-ETF proxy assigned. Use a licensed custom series or a constituent-based sector index.'); st.stop()
    st.caption(f'{selected} · ETF proxy: {proxy} (may not match the benchmark’s constituent universe)')
    if proxy not in prices: st.warning(f'No data loaded for {proxy}'); st.stop()
    period=st.selectbox('Period',['1M','3M','6M','1Y','2Y','3Y','4Y','5Y'],index=3)
    subset=prices.loc[prices.index>=prices.index.max()-pd.Timedelta(days=PERIODS[period])]
    series=subset[proxy].dropna()
    if series.empty: st.warning('No prices in selected window'); st.stop()
    fig=px.line(x=series.index,y=series/series.iloc[0]*100,labels={'x':'Trading date','y':'Indexed adjusted close'},title=f'{selected} · daily data')
    plot(fig,use_container_width=True)
