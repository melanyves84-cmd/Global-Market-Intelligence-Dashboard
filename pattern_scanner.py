"""Causal ascending-triangle detection and volume-confirmed breakout scanner."""
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DEFAULTS = dict(window=90, pivot=3, tolerance=0.025, min_touches=3,
                volume_multiple=10.0, proximity=0.05, breakout_buffer=0.005,
                confirmation_days=2, false_days=5)

def detect(df, **options):
    cfg={**DEFAULTS,**options}
    d=df[['High','Low','Close','Volume']].copy().apply(pd.to_numeric,errors='coerce').dropna()
    d=d.sort_index()
    w=int(cfg['window']); k=int(cfg['pivot'])
    if len(d)<max(45,w//2):return None
    d=d.tail(max(w+int(cfg['false_days'])+2, w))
    highs=d.High.to_numpy(); lows=d.Low.to_numpy(); closes=d.Close.to_numpy(); vols=d.Volume.to_numpy()
    # Confirm swing highs/lows only after k later candles; exclude last k bars from pivot discovery.
    peaks=[i for i in range(k,len(d)-k) if highs[i] >= max(highs[i-k:i+k+1])]
    bottoms=[i for i in range(k,len(d)-k) if lows[i] <= min(lows[i-k:i+k+1])]
    if len(peaks)<2 or len(bottoms)<2:return None
    best=None
    # Anchor candidates using past pivot highs. Never use the current price to construct resistance.
    for seed in peaks:
        level=highs[seed]
        matching=[i for i in peaks if abs(highs[i]/level-1)<=cfg['tolerance']]
        if len(matching)<cfg['min_touches']:continue
        first=min(matching)
        matching=[i for i in matching if i>=first]
        if len(matching)<cfg['min_touches'] or max(matching)-first<12:continue
        relevant=[i for i in bottoms if first<=i<=max(matching)]
        if len(relevant)<2:continue
        vals=np.array([lows[i] for i in relevant]); rises=np.diff(vals)
        rising_fraction=float(np.mean(rises>0))
        if rising_fraction < .66 or vals[-1]<=vals[0]:continue
        resistance=float(np.median(highs[matching]))
        # Reject setups where a close already broke the resistance before the latest setup started.
        tolerance=float(cfg['tolerance'])
        if np.any(closes[first:max(matching)+1]>resistance*(1+tolerance)):continue
        span=max(matching)-first
        support_start=float(vals[0]); support_end=float(vals[-1]); height=resistance-min(lows[first:max(matching)+1])
        if height<=0:continue
        # Require the ascending base to remain below resistance.
        if support_end>=resistance:continue
        compression=max(0,min(1,(support_end-support_start)/max(1e-9,resistance-support_start)))
        touch_quality=max(0,1-np.std(highs[matching])/max(.00001,resistance)/cfg['tolerance'])
        duration=min(1,span/80)
        score=25*rising_fraction+25*touch_quality+15*compression+10*duration+15*min(len(matching)/5,1)
        candidate={'resistance':resistance,'support_start':support_start,'support_end':support_end,
                   'first':first,'last_touch':max(matching),'touches':len(matching),
                   'rising_lows':len(relevant),'higher_low_rate':rising_fraction,'score':round(score,1),
                   'height':height,'target':resistance+height,'peaks':matching,'bottoms':relevant,
                   'days_under_resistance':len(d)-first,'data':d}
        if best is None or (candidate['score'],candidate['last_touch'])>(best['score'],best['last_touch']):best=candidate
    if best is None:return None
    R=best['resistance']; buffer=float(cfg['breakout_buffer']); threshold=R*(1+buffer)
    # Only events after the most recent identified resistance touch count as a breakout.
    start=best['last_touch']+1
    triggers=[i for i in range(start,len(d)) if closes[i]>threshold and (i==0 or closes[i-1]<=threshold)]
    trigger=triggers[-1] if triggers else None
    # Relative volume uses the prior 20 sessions only, not breakout day's own volume.
    ratios=np.full(len(d),np.nan)
    for i in range(20,len(d)):
        avg=np.mean(vols[i-20:i]); ratios[i]=vols[i]/avg if avg>0 else np.nan
    best['volume_ratio']=float(ratios[trigger]) if trigger is not None else np.nan
    best['distance_pct']=100*(closes[-1]/R-1)
    best['breakout_date']=str(d.index[trigger].date()) if trigger is not None else ''
    best['breakout_i']=trigger
    best['volume_confirmed']=bool(trigger is not None and ratios[trigger]>=cfg['volume_multiple'])
    if trigger is None:
        best['status']='Forming' if closes[-1]>=R*(1-cfg['proximity']) and closes[-1]<=threshold else 'Watchlist'
    else:
        following=closes[trigger+1:min(len(d),trigger+1+int(cfg['false_days']))]
        failed=bool(len(following)>0 and np.any(following<R))
        since=len(d)-trigger-1
        if failed:best['status']='Failed breakout'
        elif since>=cfg['confirmation_days'] and np.all(closes[trigger:trigger+1+cfg['confirmation_days']]>R):
            best['status']='Confirmed high-volume breakout' if best['volume_confirmed'] else 'Price breakout (volume below threshold)'
        else:best['status']='Breakout pending confirmation'
    # Score is setup geometry, NOT predicted win probability.
    best['score']=round(min(100,best['score']),1)
    return best

@st.cache_data(ttl=3600,show_spinner=False)
def load_symbols():
    from constituent_sources import download_constituents
    roster=download_constituents('United States')
    return roster[['Ticker','Company','Sector']].drop_duplicates('Ticker')

@st.cache_data(ttl=3600,show_spinner=False)
def load_bars(tickers, days=340):
    import yfinance as yf
    raw=yf.download(list(tickers),start=(date.today()-timedelta(days=days)).isoformat(),
        interval='1d',auto_adjust=True,progress=False,threads=True,group_by='ticker')
    if raw is None or raw.empty:return {}
    out={}
    for sym in tickers:
        try:
            if isinstance(raw.columns,pd.MultiIndex):
                frame=raw[sym].copy()
            else:frame=raw.copy()
            if all(x in frame for x in ['High','Low','Close','Volume']):
                frame=frame[['High','Low','Close','Volume']].dropna()
                frame.index=pd.to_datetime(frame.index).tz_localize(None)
                # Exclude today's incomplete US session when scanning, including pre-market.
                ny=datetime.now(ZoneInfo('America/New_York'))
                if len(frame) and frame.index[-1].date()==ny.date() and (ny.hour,ny.minute)<(16,5):
                    frame=frame.iloc[:-1]
                if len(frame)>40:out[sym]=frame
        except (KeyError,TypeError,ValueError):continue
    return out

def scan(frames,cfg):
    results=[]; findings={}
    for sym,df in frames.items():
        try:found=detect(df,**cfg)
        except (ValueError,IndexError,TypeError):continue
        if found:
            findings[sym]=found
            results.append({'Ticker':sym,'Status':found['status'],'Quality score':found['score'],
                'Resistance':round(found['resistance'],2),'Distance (%)':round(found['distance_pct'],2),
                'Touches':found['touches'],'Higher lows':found['rising_lows'],
                'Days beneath resistance':found['days_under_resistance'],
                'Breakout volume / normal':round(found['volume_ratio'],2) if np.isfinite(found['volume_ratio']) else np.nan,
                'Volume ≥ 10×':found['volume_confirmed'],'Breakout date':found['breakout_date'],
                'Measured target':round(found['target'],2)})
    return pd.DataFrame(results),findings

def detail_chart(found,ticker):
    d=found['data']; fig=go.Figure()
    fig.add_trace(go.Candlestick(x=d.index,open=d.Close,high=d.High,low=d.Low,close=d.Close,
        name='Daily price (high-low-close)',increasing_line_color='#1c9c7d',decreasing_line_color='#d9566a'))
    fig.add_hline(y=found['resistance'],line_color='#d48a27',line_dash='dash',annotation_text='Resistance')
    p=found['peaks']; l=found['bottoms']
    fig.add_trace(go.Scatter(x=d.index[p],y=d.High.iloc[p],mode='markers',marker=dict(color='#d48a27',size=8),name='Resistance touches'))
    fig.add_trace(go.Scatter(x=d.index[l],y=d.Low.iloc[l],mode='markers',marker=dict(color='#215F9A',size=8),name='Swing lows'))
    if len(l)>=2:
        fig.add_trace(go.Scatter(x=[d.index[l[0]],d.index[l[-1]]],y=[d.Low.iloc[l[0]],d.Low.iloc[l[-1]]],mode='lines',line=dict(color='#215F9A',width=2),name='Rising support'))
    if found['breakout_i'] is not None:
        i=found['breakout_i'];fig.add_vline(x=d.index[i].timestamp()*1000,line_color='#26a37d',line_dash='dot')
    fig.update_layout(title=f'{ticker} — {found["status"]}',template='plotly_white',height=530,
        xaxis_rangeslider_visible=False,margin=dict(l=15,r=15,t=55,b=15),legend=dict(orientation='h'))
    return fig

def page():
    st.title('Ascending Triangle & Breakout Scanner')
    st.caption('US S&P 500 constituent universe · completed daily candles · geometry-based pattern matching; not investment advice')
    st.info('A confirmed high-volume breakout requires at least **10× the average daily volume of the preceding 20 sessions**. Ordinary breakouts are shown separately. Setup scores do not represent success probabilities.')
    c1,c2,c3,c4=st.columns(4)
    with c1: window=st.selectbox('Pattern lookback (sessions)',[60,90,120,180],index=1)
    with c2: tolerance=st.slider('Resistance tolerance (%)',1.0,5.0,2.5,.5)/100
    with c3: min_touches=st.slider('Minimum resistance touches',2,5,3)
    with c4: volume_multiple=st.number_input('Breakout volume threshold (×)',min_value=1.0,max_value=50.0,value=10.0,step=1.0)
    cfg=dict(window=window,tolerance=tolerance,min_touches=min_touches,volume_multiple=volume_multiple)
    try:roster=load_symbols()
    except Exception as exc:
        st.error(f'Could not load S&P 500 constituents: {exc}. Check data-source access.');return
    sectors=['All sectors']+sorted(roster.Sector.dropna().unique().tolist())
    sector=st.selectbox('Sector to scan',sectors)
    universe=roster if sector=='All sectors' else roster[roster.Sector==sector]
    limit=st.slider('Maximum stocks per scan (use batches to respect data-provider limits)',25,550,100,25)
    st.caption(f'{len(universe)} securities in selected universe. Scanning up to {limit}; large scans depend on provider rate limits.')
    if st.button('Run scanner',type='primary'):
        symbols=universe.Ticker.head(limit).tolist();frames={}
        bar=st.progress(0)
        for j in range(0,len(symbols),25):
            chunk=symbols[j:j+25]
            try:frames.update(load_bars(tuple(chunk)))
            except Exception as exc:st.warning(f'Batch {j//25+1} unavailable: {exc}')
            bar.progress(min(1,(j+len(chunk))/max(len(symbols),1)))
        report,found=scan(frames,cfg)
        st.session_state['pattern_scan']=(report,found,tuple(symbols),len(frames))
    if 'pattern_scan' not in st.session_state:
        st.caption('Select a universe and click Run scanner. No sample results are fabricated.');return
    report,found,requested,downloaded=st.session_state['pattern_scan']
    st.caption(f'Last scan: {downloaded}/{len(requested)} symbols with sufficient downloaded data. Results may be incomplete if feeds were unavailable.')
    if report.empty:st.warning('No matching patterns found in the successfully scanned prices.');return
    status=st.multiselect('Show pattern status',sorted(report.Status.unique()),default=sorted(report.Status.unique()))
    min_score=st.slider('Minimum pattern-quality score',0,100,60)
    filtered=report[(report.Status.isin(status))&(report['Quality score']>=min_score)].sort_values('Quality score',ascending=False)
    st.dataframe(filtered,hide_index=True,use_container_width=True)
    st.download_button('Export scan CSV',filtered.to_csv(index=False),file_name='ascending_triangle_scan.csv',mime='text/csv')
    if filtered.empty:return
    choice=st.selectbox('Inspect annotated chart',filtered.Ticker.tolist())
    st.plotly_chart(detail_chart(found[choice],choice),use_container_width=True)
    x=found[choice]
    st.caption(f'Resistance {x["resistance"]:.2f}; measured-move target {x["target"]:.2f} (illustrative, not a forecast); breakout {x["breakout_date"] or "not detected"}; volume ratio {x["volume_ratio"]:.2f}×' if np.isfinite(x['volume_ratio']) else f'Resistance {x["resistance"]:.2f}; breakout not detected; measured-move target {x["target"]:.2f}.')
    st.caption('This is an end-of-day on-demand scan, not background monitoring. The breakout volume test uses completed trading days; the scan does not issue push notifications.')
