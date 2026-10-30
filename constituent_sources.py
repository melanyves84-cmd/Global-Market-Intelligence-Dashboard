"""Public current constituent catalogs; independently check official index data before trading."""
from datetime import datetime, timezone
import io
import pandas as pd
import streamlit as st
from europe_tickers import enrich_european_roster

US_URL = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv'
EU_URL = 'https://en.wikipedia.org/wiki/STOXX_Europe_600'
CN_URL = 'https://yfiua.github.io/index-constituents/constituents-csi300.csv'
SECTOR_MAP = {'Health Care':'Healthcare','Basic Materials':'Materials','Technology':'Information Technology',
    'Telecommunications':'Communication Services','Financial Services':'Financials',
    'Consumer Products and Services':'Consumer Discretionary','Automobiles and Parts':'Consumer Discretionary',
    'Travel and Leisure':'Consumer Discretionary','Retail':'Consumer Discretionary','Media':'Communication Services',
    'Food, Beverage and Tobacco':'Consumer Staples','Personal Care, Drug and Grocery Stores':'Consumer Staples',
    'Industrial Goods and Services':'Industrials','Construction and Materials':'Industrials',
    'Chemicals':'Materials','Basic Resources':'Materials','Banks':'Financials','Insurance':'Financials',
    'Oil, Gas and Coal':'Energy','Utilities':'Utilities','Real Estate':'Real Estate',
    'Energy':'Energy','Financials':'Financials','Industrials':'Industrials','Consumer Staples':'Consumer Staples',
    'Consumer Discretionary':'Consumer Discretionary','Information Technology':'Information Technology',
    'Communication Services':'Communication Services','Materials':'Materials','Healthcare':'Healthcare'}
# Exchange suffix cannot be inferred reliably from country for multi-listed securities; keep native ticker unless verified.

def _standard(market, frame, name, ticker, sector=None, subsector=None, source='', asof=''):
    x=pd.DataFrame({'Market':market,'Company':frame[name].astype(str).str.strip(),
                    'Ticker':frame[ticker].astype(str).str.strip(),
                    'Sector':frame[sector].astype(str).str.strip().map(lambda v:SECTOR_MAP.get(v,'')) if sector else '',
                    'Subsector':frame[subsector].astype(str).str.strip() if subsector else '',
                    'WeightPct':pd.NA,'Source':source,'AsOf':asof})
    x=x[(x.Ticker!='')&(x.Ticker!='nan')&(x.Company!='nan')].drop_duplicates(['Market','Ticker'])
    return x[['Market','Sector','Company','Ticker','WeightPct','Subsector','Source','AsOf']]

@st.cache_data(ttl=86400,show_spinner=False)
def download_constituents(market):
    ts=datetime.now(timezone.utc).strftime('%Y-%m-%d UTC')
    if market=='United States':
        d=pd.read_csv(US_URL, dtype=str)
        needed={'Symbol','Security','GICS Sector'}
        if not needed.issubset(d):raise ValueError(f'US source format changed: {list(d.columns)}')
        d['Symbol']=d['Symbol'].str.replace('.','-',regex=False)
        out=_standard(market,d,'Security','Symbol','GICS Sector','GICS Sub-Industry',US_URL,ts)
        if not 450<=len(out)<=550:raise ValueError('US constituent count outside expected bounds')
    elif market=='Europe':
        tables=pd.read_html(EU_URL)
        d=next((t for t in tables if {'Ticker','Company','ICB Sector'}.issubset(t.columns)),None)
        if d is None:raise ValueError('No recognized STOXX Europe 600 constituent table found')
        out=_standard(market,d,'Company','Ticker','ICB Sector',None,EU_URL,ts)
        out['Country']=d['Country'].astype(str).str.strip().values if 'Country' in d else ''
        out=enrich_european_roster(out)
        if not 450<=len(out)<=700:raise ValueError('Europe constituent count outside expected bounds')
    elif market=='China (mainland A-shares)':
        d=pd.read_csv(CN_URL,dtype=str)
        if not {'Symbol','Name'}.issubset(d):raise ValueError('CSI 300 source columns changed')
        out=_standard(market,d,'Name','Symbol',source=CN_URL,asof=ts)
        # Source contains membership only: do NOT claim sectors or weights.
        if not 280<=len(out)<=320:raise ValueError('China constituent count outside expected bounds')
    else:raise ValueError('Unknown market')
    return out.reset_index(drop=True)
