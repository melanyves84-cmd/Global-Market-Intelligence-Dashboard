"""Regional sector catalog and global, weekly rotation visualizations.

All dates are market-local, sector returns are relative to market-local benchmarks.
'Auto' sources are explicitly ETF/index price proxies, not exact GICS indices.
"""
import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sector_data import weekly_completed, series_quality
from ui_theme import plot

GICS_11=["Information Technology","Financials","Healthcare","Consumer Discretionary",
"Communication Services","Industrials","Consumer Staples","Energy","Utilities","Real Estate","Materials"]
REGION_BENCHMARK={"United States":"SPY", "Europe":"EXSA.DE", "China (mainland A-shares)":"510300.SS"}
# Conservative default coverage: source-aligned public ETFs, chosen from published Europe ETF mapping.
# Unverified series stay absent. Official China codes are shown as *candidate* index references only.
# Provider ticker support not guaranteed; users may map a licensed index series using CSV.
REGION_SECTORS={
 "United States":dict(zip(GICS_11,["XLK","XLF","XLV","XLY","XLC","XLI","XLP","XLE","XLU","XLRE","XLB"])),
 "Europe":{"Information Technology":"EXH1.DE","Financials":None,"Healthcare":None,
           "Consumer Discretionary":None,"Communication Services":None,"Industrials":"EXH4.DE",
           "Consumer Staples":None,"Energy":None,"Utilities":None,"Real Estate":None,"Materials":None},
 "China (mainland A-shares)":dict.fromkeys(GICS_11,None)
}
# 2007 official 10 CSI300 industry codes. Financials + real estate were grouped.
# NOT inserted into the GICS 11 heatmap automatically; codes provided for research/import.
CHINA_LEGACY={"Energy":"000908.SS","Materials":"000909.SS","Industrials":"000910.SS",
"Consumer Discretionary":"000911.SS","Consumer Staples":"000912.SS","Healthcare":"000913.SS",
"Financials + Real Estate (combined)":"000914.SS","Information Technology":"000915.SS",
"Communication Services":"000916.SS","Utilities":"000917.SS"}

def make_catalog():
    rows=[]
    for region in REGION_SECTORS:
        for sector in GICS_11:
            ticker=REGION_SECTORS[region].get(sector)
            rows.append({"Region":region,"Sector":sector,"Ticker":ticker or "",
                         "Coverage": "ETF price proxy" if ticker else "Needs approved sector series",
                         "Notes": "Specify exact index/ETF and price basis; benchmark must be consistent"})
    return pd.DataFrame(rows)

def read_catalog(upload):
    if upload is None:return make_catalog()
    df=pd.read_csv(upload,dtype=str).fillna("")
    required={"Region","Sector","Ticker"}
    if not required.issubset(df.columns):
        raise ValueError("Mapping CSV requires Region, Sector, Ticker columns")
    valid_regions=set(REGION_BENCHMARK)
    if not set(df.Region).issubset(valid_regions) or not set(df.Sector).issubset(GICS_11):
        raise ValueError("Mapping contains unknown regions or sectors")
    if df.duplicated(['Region','Sector']).any():raise ValueError('Region + Sector must be unique')
    return make_catalog().drop(columns=['Ticker','Coverage','Notes']).merge(
        df[['Region','Sector','Ticker']],on=['Region','Sector'],how='left').fillna('')

def regional_weekly_scores(daily, catalog, period=4, exclude_unfinished=True, today=None):
    """Return long rows with coverage info. Use only completed week-end observations; no forward fill across gaps."""
    if today is None: today=pd.Timestamp.today().normalize()
    today=pd.Timestamp(today).normalize()
    if not isinstance(daily.index,pd.DatetimeIndex) or daily.empty:
        return pd.DataFrame()
    p=daily.sort_index().copy()
    p.index=pd.to_datetime(p.index).tz_localize(None).normalize()
    p=p[p.index<=today]
    w=weekly_completed(p,today=today) if exclude_unfinished else p.resample('W-FRI').last()
    if len(w)<period+1:return pd.DataFrame()
    latest=w.iloc[-1]; past=w.iloc[-period-1]
    rows=[]
    for region in REGION_BENCHMARK:
        bench=REGION_BENCHMARK[region]
        b=np.nan
        if bench in w and pd.notna(latest.get(bench)) and pd.notna(past.get(bench)) and past[bench]>0:
            b=(latest[bench]/past[bench]-1)*100
        for sector in GICS_11:
            found=catalog[(catalog.Region==region)&(catalog.Sector==sector)]
            ticker=str(found.iloc[0]['Ticker']).strip() if not found.empty else ''
            rr=np.nan
            if ticker and ticker in w and pd.notna(latest.get(ticker)) and pd.notna(past.get(ticker)) and past[ticker]>0:
                rr=(latest[ticker]/past[ticker]-1)*100
            score=rr-b if pd.notna(rr) and pd.notna(b) else np.nan
            reason=('Missing mapping' if not ticker else ('Missing benchmark' if pd.isna(b) else ('Missing price history' if pd.isna(rr) else 'Available')))
            rows.append({'Region':region,'Sector':sector,'Ticker':ticker or '—',
                         'Sector return (%)':rr,'Benchmark return (%)':b,'Relative (pp)':score,
                         'Coverage':reason, 'Week ending':w.index[-1]})
    return pd.DataFrame(rows)

def global_rotation_page(prices, catalog):
    st.subheader('Global sector rotation heatmap')
    st.caption('Weekly returns versus **each region’s own benchmark** (US: SPY · Europe: STOXX Europe 600 ETF · China: CSI 300 ETF). '
               'Missing cells mean no valid comparable series was loaded, not a zero return.')
    c1,c2=st.columns([1,2])
    with c1: weeks=st.selectbox('Weekly lookback',[1,4,8,13,26,52],index=1,format_func=lambda n:f'{n} weeks')
    with c2: show=st.radio('Heatmap values',['Relative return (pp)','Absolute sector return (%)'],horizontal=True)
    results=regional_weekly_scores(prices,catalog,period=weeks)
    if results.empty:
        st.warning('Need at least '+str(weeks+1)+' completed weekly price observations. Import daily CSV or retrieve permitted prices.')
        return
    field='Relative (pp)' if show.startswith('Relative') else 'Sector return (%)'
    heat=results.pivot(index='Sector',columns='Region',values=field).reindex(GICS_11)
    labels=heat.copy().apply(lambda c:c.map(lambda v:'N/A' if pd.isna(v) else f'{v:+.1f}'))
    arr=heat.to_numpy(dtype=float)
    lim=max(2.0, np.nanpercentile(np.abs(arr[np.isfinite(arr)]),90)) if np.isfinite(arr).any() else 2.0
    fig=px.imshow(heat, color_continuous_scale='RdBu',color_continuous_midpoint=0,
                  zmin=-lim,zmax=lim,aspect='auto',text_auto=False)
    fig.update_traces(text=labels.to_numpy(),texttemplate='%{text}',hovertemplate='Sector: %{y}<br>Market: %{x}<br>Value: %{z:.2f}<extra></extra>')
    fig.update_layout(height=600,coloraxis_colorbar_title='pp' if show.startswith('Relative') else '%',xaxis_title='',yaxis_title='')
    plot(fig,use_container_width=True)
    st.caption('A sector proxy is not necessarily a constituent-matched sector index. Comparing relative returns across currencies avoids direct FX conversion of percentage returns, but not methodology differences.')
    covered=results[results.Coverage=='Available']
    st.metric('Covered sector cells',f'{len(covered)} / 33')
    with st.expander('Coverage and mapping diagnostics',expanded=len(covered)<33):
        st.dataframe(results[['Region','Sector','Ticker','Coverage','Week ending']],hide_index=True,use_container_width=True)
    st.download_button('Download weekly global results',results.to_csv(index=False).encode(), 'global_weekly_rotation.csv','text/csv')

def mapping_page(catalog):
    st.subheader('Sector-series mapping & coverage')
    st.warning('For a genuinely harmonized 11-sector comparison, provide **one licensed GICS-classified sector index per region and sector**, plus a matching benchmark. Public ETFs are only practical proxies.')
    st.dataframe(catalog,use_container_width=True,hide_index=True)
    st.download_button('Download editable 33-sector mapping CSV',catalog.to_csv(index=False).encode(),'sector_mapping.csv','text/csv')
    st.markdown('**China legacy CSI 300 index references** (official historical ten-sector scheme; combined Financials + Real Estate):')
    st.dataframe(pd.DataFrame([{'Index':k,'Candidate Yahoo symbol (verify)':v} for k,v in CHINA_LEGACY.items()]),hide_index=True)
    st.markdown('**Historical data licensing:** STOXX ordinarily provides only a short free history; longer STOXX sector index histories require a license. CSI index histories likewise may require a CSI / authorised-vendor agreement. The app does not redistribute licensed values.')
    st.markdown('**Official source references:** [STOXX download policies](https://www.stoxx.com/help) · [STOXX sector structure](https://stoxx.com/index/s600csv/) · [CSI 300 legacy index announcement](https://www.szse.cn/disclosure/notice/general/t20070611_499843.html) · [CSI data licensing overview](https://www.ciis.com.hk/hongkong/en/uploadfiles/202507/21/2025072109322370585011.pdf)')
    st.download_button('Download empty sector-index price template', 'Date,Ticker,Close\n'.encode(), 'sector_index_prices_template.csv','text/csv')
    st.info('To complete coverage, download the mapping CSV, fill its empty Ticker fields with correctly classified provider symbols, '
            'upload that file in the sidebar, and include the corresponding daily prices in the CSV data upload or configure a licensed feed.')
