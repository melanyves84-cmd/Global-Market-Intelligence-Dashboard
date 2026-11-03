import numpy as np
import pandas as pd
import sys, types
st=types.ModuleType("streamlit")
st.cache_data=lambda *a,**k: (lambda f:f)
sys.modules.setdefault("streamlit",st)
from pattern_scanner import detect

def fixture(breakout=False, fail=False):
    n=95; x=np.arange(n); close=88+0.06*x+np.sin(x*2*np.pi/12)*(7-0.048*x)
    high=close+0.5; low=close-0.5
    for j in [30,44,58,72,84]:high[j]=101.0
    # ordered higher swing lows, near resistance plateau
    for j,v in [(34,89),(48,91),(62,93),(76,95)]: low[j]=v
    # price must stay lower than resistance until breakout; ignore other swing peaks
    close=np.minimum(close,99.4)
    vol=np.full(n,1000.)
    if breakout:
        close[-3:]=[102,103,104];high[-3:]=[103,104,105];low[-3:]=[100,101,102];vol[-3]=11000
        if fail:close[-1]=99
    return pd.DataFrame({'High':high,'Low':low,'Close':close,'Volume':vol},index=pd.bdate_range('2026-01-01',periods=n))

def test_safe_missing():
    assert detect(fixture().head(10)) is None

def test_generated_values():
    x=detect(fixture())
    assert x is None or x['score']<=100

def test_volume_reference():
    from pattern_scanner import DEFAULTS
    assert DEFAULTS['volume_multiple']==10
