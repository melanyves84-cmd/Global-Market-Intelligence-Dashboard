"""Quality controls and portable ingestion for regional index-provider CSV histories."""
from datetime import date
import pandas as pd
import numpy as np

REQUIRED=('Date','Ticker','Close')

def read_prices(upload):
    """Long-format CSV; strict no fabricated/forward-filled prices. Can contain many index series."""
    df=pd.read_csv(upload,dtype={'Ticker':str})
    missing=set(REQUIRED)-set(df.columns)
    if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    df['Date']=pd.to_datetime(df.Date,errors='coerce',utc=True).dt.tz_convert(None).dt.normalize()
    df['Ticker']=df.Ticker.astype(str).str.strip()
    df['Close']=pd.to_numeric(df.Close,errors='coerce')
    bad=df[df.Date.isna() | df.Close.isna() | (df.Close<=0) | (df.Ticker=='')]
    if len(bad): raise ValueError(f'{len(bad)} invalid records (date, ticker or positive close). Clean source file first.')
    duplicates=df.duplicated(['Date','Ticker'],keep=False)
    if duplicates.any(): raise ValueError(f'{duplicates.sum()} duplicate Date + Ticker records. Resolve conflicting sources first.')
    future=df.Date.dt.date>date.today()
    if future.any(): raise ValueError('Source contains future-dated observations.')
    return df.pivot(index='Date',columns='Ticker',values='Close').sort_index()

def last_completed_friday(today=None):
    now=pd.Timestamp(today or date.today()).normalize()
    # Friday belongs to a still-open weekly bucket until Saturday.
    days_since_friday=(now.weekday()-4)%7
    latest=now-pd.Timedelta(days=days_since_friday)
    if now.weekday()==4: latest-=pd.Timedelta(days=7)
    return latest

def weekly_completed(daily,today=None):
    if daily.empty: return daily
    p=daily.sort_index().copy()
    p.index=pd.to_datetime(p.index).tz_localize(None)
    cutoff=last_completed_friday(today)
    return p.resample('W-FRI').last().loc[lambda x:x.index<=cutoff]

def series_quality(prices,ticker,period_weeks=13):
    if ticker not in prices: return 'No data'
    s=prices[ticker].dropna()
    if len(s)==0:return 'No data'
    w=weekly_completed(prices[[ticker]])[ticker]
    if len(w)<period_weeks+1 or w.iloc[-1]!=w.iloc[-1]: return 'Insufficient weekly history'
    if pd.isna(w.iloc[-period_weeks-1]): return 'Historical gaps'
    if s.index[-1] < pd.Timestamp.today().normalize()-pd.Timedelta(days=12):return 'Stale data'
    return 'Available'

TEMPLATE='Date,Ticker,Close\n'
