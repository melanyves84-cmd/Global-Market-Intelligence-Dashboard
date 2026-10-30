"""Standalone company research page; never fabricates index membership or weight data."""
from datetime import date, timedelta
import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

SECTORS = ['Information Technology','Financials','Healthcare','Consumer Discretionary','Communication Services','Industrials','Consumer Staples','Energy','Utilities','Real Estate','Materials']
# Curated examples, not exhaustive or point-in-time constituent records.
EXAMPLES = [
 ('United States','Information Technology','Microsoft','MSFT'),('United States','Information Technology','Nvidia','NVDA'),('United States','Information Technology','Apple','AAPL'),('United States','Financials','JPMorgan Chase','JPM'),('United States','Healthcare','Johnson & Johnson','JNJ'),('United States','Consumer Discretionary','Amazon','AMZN'),('United States','Communication Services','Alphabet (Class A)','GOOGL'),('United States','Industrials','Caterpillar','CAT'),('United States','Consumer Staples','Procter & Gamble','PG'),('United States','Energy','ExxonMobil','XOM'),('United States','Utilities','NextEra Energy','NEE'),('United States','Real Estate','Prologis','PLD'),('United States','Materials','Linde','LIN'),
 ('Europe','Information Technology','ASML','ASML.AS'),('Europe','Information Technology','SAP','SAP.DE'),('Europe','Healthcare','Novartis','NOVN.SW'),('Europe','Healthcare','Roche','ROG.SW'),('Europe','Financials','HSBC','HSBA.L'),('Europe','Consumer Discretionary','LVMH','MC.PA'),('Europe','Consumer Staples','Nestlé','NESN.SW'),('Europe','Energy','Shell','SHEL.L'),('Europe','Industrials','Siemens','SIE.DE'),('Europe','Utilities','Iberdrola','IBE.MC'),('Europe','Materials','BASF','BAS.DE'),('Europe','Communication Services','Deutsche Telekom','DTE.DE'),('Europe','Real Estate','Vonovia','VNA.DE'),
 ('China (mainland A-shares)','Information Technology','Luxshare Precision','002475.SZ'),('China (mainland A-shares)','Financials','China Merchants Bank','600036.SS'),('China (mainland A-shares)','Healthcare','Jiangsu Hengrui Pharmaceuticals','600276.SS'),('China (mainland A-shares)','Consumer Staples','Kweichow Moutai','600519.SS'),('China (mainland A-shares)','Consumer Discretionary','BYD','002594.SZ'),('China (mainland A-shares)','Utilities','China Yangtze Power','600900.SS'),('China (mainland A-shares)','Energy','PetroChina A','601857.SS')]
COLUMNS=['Market','Sector','Company','Ticker','WeightPct','Subsector','Source','AsOf']
PERIODS={'1M':32,'3M':96,'6M':190,'1Y':365,'2Y':730,'3Y':1095,'4Y':1461,'5Y':1827}
BENCHMARK={'United States':'SPY','Europe':'EXSA.DE','China (mainland A-shares)':'510300.SS'}

def starter():
    x=pd.DataFrame(EXAMPLES,columns=COLUMNS[:4])
    for c in COLUMNS[4:]:x[c]=''
    return x

def validate_roster(df):
    mandatory=['Market','Sector','Company','Ticker']
    if any(c not in df.columns for c in mandatory):raise ValueError('Constituent CSV requires Market, Sector, Company, Ticker columns.')
    df=df.copy()
    for c in COLUMNS:
        if c not in df:df[c]=''
    df=df[COLUMNS]
    for c in mandatory:df[c]=df[c].fillna('').astype(str).str.strip()
    if (df[mandatory]=='').any().any():raise ValueError('Market, Sector, Company and Ticker cannot be empty.')
    if not df['Market'].isin(BENCHMARK).all():raise ValueError('Unknown Market label. Use values in the downloadable template.')
    if not df['Sector'].isin(SECTORS).all():raise ValueError('Unknown Sector name. Use the 11 categories in the downloadable template.')
    if df.duplicated(['Market','Ticker']).any():raise ValueError('Duplicate Market + Ticker rows.')
    w=pd.to_numeric(df.WeightPct.replace('',pd.NA),errors='coerce')
    bad=df.WeightPct.astype(str).str.strip().ne('') & w.isna()
    if bad.any() or ((w<0)|(w>100)).any():raise ValueError('WeightPct must be blank or a number between 0 and 100.')
    df['WeightPct']=w
    return df

@st.cache_data(ttl=3600,show_spinner=False)
def fetch_daily(tickers):
    import yfinance as yf
    x=yf.download(list(tickers),start=(date.today()-timedelta(days=1900)).isoformat(),auto_adjust=True,progress=False,threads=True)
    if x is None or x.empty:return pd.DataFrame()
    if isinstance(x.columns,pd.MultiIndex):p=x['Close']
    else:p=x[['Close']].rename(columns={'Close':tickers[0]})
    p.index=pd.to_datetime(p.index).tz_localize(None).normalize()
    return p.sort_index()

def parse_prices(upload):
    x=pd.read_csv(upload)
    if not {'Date','Ticker','Close'}.issubset(x.columns):raise ValueError('Price CSV requires Date,Ticker,Close.')
    x['Date']=pd.to_datetime(x.Date,errors='coerce')
    x['Close']=pd.to_numeric(x.Close,errors='coerce')
    x=x.dropna(subset=['Date','Ticker','Close'])
    if (x.Close<=0).any():raise ValueError('Close prices must be positive.')
    if x.duplicated(['Date','Ticker']).any():raise ValueError('Duplicate Date/Ticker entries found.')
    return x.pivot(index='Date',columns='Ticker',values='Close').sort_index()

from constituent_sources import download_constituents
from europe_tickers import apply_verified_overrides, apply_isin_exchange_mapping

def company_page():
    st.subheader('Company Explorer')
    st.caption('Market → sector → company · Daily share-price chart · Compare up to five securities. Example list is a starter universe, not a verified or complete live index membership list.')
    feed_mode=st.radio('Constituent list source',['Automatic public sources','Upload custom CSV','Starter examples'],horizontal=True)
    a,b=st.columns([1,1])
    with a: roster_file=st.file_uploader('Constituent list / weights CSV',type=['csv'],key='company_roster')
    with b: price_file=st.file_uploader('Optional daily prices CSV (Date,Ticker,Close)',type=['csv'],key='company_prices')
    try:
        if roster_file is not None:
            roster=validate_roster(pd.read_csv(roster_file))
            st.success('Using uploaded constituent list, overriding public source.')
        elif feed_mode=='Automatic public sources':
            datasets=[]; errors=[]
            for m in BENCHMARK:
                try:datasets.append(download_constituents(m))
                except Exception as e: errors.append(f'{m}: {e}')
            roster=pd.concat(datasets,ignore_index=True) if datasets else starter().iloc[:0]
            for err in errors:st.warning(f'Automatic source unavailable — {err}')
            st.caption('Membership is cached for 24 hours. Public snapshots are not guaranteed official. European Yahoo symbols are inferred from the country of listing and MUST be verified for company identity, share class and exchange. China list has no sector labels or weights.')
        elif feed_mode=='Starter examples':roster=validate_roster(starter())
        else:
            st.info('Upload a constituent CSV to begin.'); roster=starter().iloc[:0]
    except Exception as e:
        st.error(f'Constituent input error: {e}');return
    if not roster.empty and 'NativeTicker' in roster.columns:
        st.markdown('#### European exchange ticker mapping')
        eu=roster[roster.Market=='Europe'].copy()
        a,b=st.columns([2,1])
        with a:
            mapping_file=st.file_uploader('Optional European Yahoo-symbol corrections (CSV)',type=['csv'],key='eu_symbol_overrides',help='Columns: NativeTicker,Country,YahooTicker. Use exchange-verified symbols. Do not use this to change index membership.')
        with b:
            sample=eu[['NativeTicker','Country','Ticker']].rename(columns={'Ticker':'YahooTicker'}) if not eu.empty else pd.DataFrame(columns=['NativeTicker','Country','YahooTicker'])
            st.download_button('Download European mapping CSV',sample.to_csv(index=False).encode(),'europe_ticker_mapping.csv',mime='text/csv')
        if mapping_file is not None:
            try:
                roster_eu=apply_verified_overrides(eu,pd.read_csv(mapping_file,dtype=str))
                roster=pd.concat([roster[roster.Market!='Europe'],roster_eu],ignore_index=True)
                eu=roster_eu
                st.success('Ticker overrides applied. Identity and listing still need independent confirmation.')
            except Exception as e:st.error(f'European mapping error: {e}')
        st.markdown('##### ISIN + exchange validation (recommended)')
        st.caption('Provide a source-checked ISIN, ISO 10383 exchange MIC, and exact Yahoo ticker for each listing. Check digits and suffix agreement are validated; provider identity is not independently verified.')
        isin_template=eu[['NativeTicker']].copy()
        for col in ['ISIN','ExchangeMIC','YahooTicker','EvidenceURL','VerifiedAsOf']:
            isin_template[col]=''
        st.download_button('Download ISIN + MIC template',isin_template.to_csv(index=False).encode(),'europe_isin_exchange_mapping.csv',mime='text/csv')
        isin_file=st.file_uploader('Import ISIN + exchange mapping CSV',type=['csv'],key='europe_isin_mapping')
        if isin_file is not None:
            try:
                roster_eu=apply_isin_exchange_mapping(eu,pd.read_csv(isin_file,dtype=str))
                roster=pd.concat([roster[roster.Market!='Europe'],roster_eu],ignore_index=True)
                eu=roster_eu
                st.success('Documented mapping loaded and format-checked. Please independently confirm source identity and share class.')
            except Exception as e:st.error(f'ISIN / MIC mapping failed: {e}')
        missing=int(eu.Ticker.eq('').sum())
        st.caption(f'Europe mapping: {len(eu)-missing} candidate tickers; {missing} require manual exchange identification. Candidate ticker does not guarantee correct security.')
        if missing:
            with st.expander('Unresolved European symbols'):
                st.dataframe(eu[eu.Ticker.eq('')][['Company','NativeTicker','Country','MappingStatus']],hide_index=True,use_container_width=True)
    st.download_button('Download company / weight CSV template',starter().to_csv(index=False).encode(),'company_constituents_template.csv',mime='text/csv')
    if not roster.empty:
        st.download_button('Download current roster / enrich offline',roster.to_csv(index=False).encode(),'current_constituents.csv',mime='text/csv')
        counts=roster.groupby('Market').size()
        st.caption('Loaded: '+' · '.join(f'{m}: {counts.get(m,0)} securities' for m in BENCHMARK))
    a,b,c=st.columns([1,1,1])
    with a: market=st.selectbox('Market',list(BENCHMARK),key='company_market')
    with b: sector=st.selectbox('Sector',SECTORS,key='company_sector')
    subset=roster[(roster.Market==market)&(roster.Sector==sector)].copy()
    unresolved=subset[subset.Ticker.fillna('').eq('')].copy()
    subset=subset[subset.Ticker.fillna('').ne('')].copy()
    if not unresolved.empty:st.warning(f'{len(unresolved)} companies in this sector have no safely mapped exchange ticker; use the European mapping CSV to add them.')
    with c: period=st.selectbox('Chart history',list(PERIODS),index=3,key='company_period')
    if subset.empty:
        unclassified=roster[(roster.Market==market)&(roster.Sector=='')]
        if not unclassified.empty:
            st.warning(f'{len(unclassified)} constituents have no verified sector mapping. Showing full unclassified list below; use the roster download to add sourced sector values for filtering.')
            st.dataframe(unclassified[['Company','Ticker','Source','AsOf']],hide_index=True,use_container_width=True)
        else:st.info('No companies mapped to this market/sector yet. Choose another sector or upload a CSV with sector classifications.')
        return
    if market=='Europe' and 'MappingStatus' in subset.columns:
        verified=subset.MappingStatus.astype(str).str.startswith('documented ISIN + MIC')
        if not st.checkbox('Show country-inferred or unverified European symbols',value=False,help='By default only entries with documented ISIN and exchange MIC are eligible for price charts. Enable to explore speculative candidates with warnings.'):
            subset=subset[verified].copy()
        if subset.empty:
            st.warning('No ISIN + exchange mappings documented for this sector. Import the mapping CSV above, or explicitly enable unverified symbols.');return
    selected=st.selectbox('Company',subset.Ticker.tolist(),format_func=lambda t: f"{subset.loc[subset.Ticker==t,'Company'].iloc[0]}  ·  {t}")
    peers=st.multiselect('Compare companies (max 5, including selected)',[t for t in subset.Ticker if t!=selected],max_selections=4,key='company_peers')
    compare_benchmark=st.checkbox('Add regional benchmark ETF proxy',value=True,key='company_benchmark')
    tickers=list(dict.fromkeys([selected]+peers+([BENCHMARK[market]] if compare_benchmark else [])))
    if price_file:
        try: prices=parse_prices(price_file)
        except Exception as e:st.error(f'Price input error: {e}');return
        st.caption('Prices: uploaded CSV (verify currency, dividends and adjustment methodology).')
    else:
        try: prices=fetch_daily(tuple(tickers))
        except Exception as e:
            st.warning(f'Online price feed unavailable: {e}. Upload daily prices instead.');prices=pd.DataFrame()
        st.caption('Online historical prices: Yahoo Finance via yfinance, adjusted where available. Not a licensed production feed.')
    meta=subset.set_index('Ticker').loc[selected]
    if market=='Europe' and 'MappingStatus' in subset.columns:
        st.warning(f'European listing: {meta.get("MappingStatus","unverified")}. Check the exchange and share class before interpreting the chart.')
    x,y,z=st.columns(3)
    x.metric('Company',meta['Company']);y.metric('Ticker',selected)
    z.metric('Sector weight',f"{meta['WeightPct']:.2f}%" if pd.notna(meta['WeightPct']) else 'Not supplied')
    if prices.empty or selected not in prices or prices[selected].dropna().empty:
        st.info('No historical prices available for this selection. You can upload a daily prices CSV.');return
    recent=prices.loc[prices.index>=prices.index.max()-pd.Timedelta(days=PERIODS[period])]
    fig=go.Figure();lines=0
    for t in tickers:
        if t not in recent:continue
        series=recent[t].dropna()
        if len(series)<2:continue
        normalized=series/series.iloc[0]*100
        fig.add_trace(go.Scatter(x=normalized.index,y=normalized.values,mode='lines',name=t,line={'width':3 if t==selected else 2}));lines+=1
    if lines:
        fig.update_layout(template='plotly_white',height=435,margin=dict(l=15,r=15,t=35,b=20),title='Normalized daily price performance · starting value 100',xaxis_title='',yaxis_title='Indexed level (100 = start)',hovermode='x unified',legend=dict(orientation='h',y=1.12))
        st.plotly_chart(fig,use_container_width=True)
    st.caption('Prices can be in different currencies; normalization compares percentage price changes, not currency-adjusted investor returns. Benchmark ETFs are proxies. Historical company membership and weights are not inferred.')
    rows=[]
    for ticker in tickers:
        if ticker not in recent:continue
        series=recent[ticker].dropna()
        if len(series)>1:rows.append({'Ticker':ticker,'1M / selected-period return':100*(series.iloc[-1]/series.iloc[0]-1),'Observations':len(series)})
    if rows:st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.download_button('Export displayed price history',recent[[t for t in tickers if t in recent]].to_csv().encode(),'company_daily_prices.csv',mime='text/csv')
    st.markdown('#### Sector constituent table')
    st.dataframe(subset[['Company','Ticker','Subsector','WeightPct','Source','AsOf']],hide_index=True,use_container_width=True)
    if pd.to_numeric(subset.WeightPct,errors='coerce').notna().any():
        st.caption('Weights are supplied externally and may become stale; do not interpret them as current index weights unless their source and as-of date support that claim.')
    else:st.caption('No official sector weights are populated. Upload sourced weights for the allocation view.')
