"""Conservative Europe exchange-symbol mapping for public STOXX tables.

Country indicates a *candidate* primary venue, not proof of listing. All candidates
are clearly marked unverified. Exchange-specific official identifiers are preferred.
"""
import re
import pandas as pd

# Yahoo Finance exchange suffix conventions. These are inferred primary listings,
# never guaranteed identification of a particular security/share class.
PRIMARY_SUFFIX = {
    'United Kingdom':'.L', 'UK':'.L', 'Great Britain':'.L',
    'France':'.PA','Germany':'.DE','Switzerland':'.SW','Netherlands':'.AS',
    'Italy':'.MI','Spain':'.MC','Sweden':'.ST','Denmark':'.CO',
    'Norway':'.OL','Finland':'.HE','Belgium':'.BR','Austria':'.VI',
    'Portugal':'.LS','Ireland':'.IR','Poland':'.WA','Greece':'.AT',
}
# These require special handling or manual exchange verification.
AMBIGUOUS_COUNTRIES={'Luxembourg','Jersey','Guernsey','Isle of Man','Cyprus','Bermuda'}

# Source-native ticker may include share-class punctuation; preserve the left hand
# symbol, do not guess a replacement if it is already a recognized Yahoo code.
KNOWN_SUFFIXES=set(PRIMARY_SUFFIX.values())|{'.LS','.IC','.PR','.BD','.TL','.RG','.VS'}

def candidate_symbol(native, country):
    sym=str(native or '').strip()
    country=str(country or '').strip()
    if not sym or sym.lower()=='nan':return '', 'missing native ticker'
    if any(sym.upper().endswith(ext.upper()) for ext in KNOWN_SUFFIXES):
        return sym, 'source symbol contains exchange suffix; verify listing'
    if not re.fullmatch(r'[A-Za-z0-9_.\-]+',sym):
        return '', 'unrecognized native symbol format; manual mapping required'
    suffix=PRIMARY_SUFFIX.get(country)
    if not suffix:
        return '', 'exchange unavailable or ambiguous; manual mapping required'
    # Avoid accepting arbitrary embedded punctuation not proven safe.
    return sym+suffix, 'country-inferred candidate; unverified'

def enrich_european_roster(data):
    data=data.copy()
    if 'Country' not in data.columns:
        data['Country']=''
    data['NativeTicker']=data['Ticker'].fillna('').astype(str)
    resolved=[candidate_symbol(t,c) for t,c in zip(data.NativeTicker,data.Country)]
    data['Ticker']=[r[0] for r in resolved]
    data['MappingStatus']=[r[1] for r in resolved]
    return data

def apply_verified_overrides(data, overrides):
    """Use user-verified mapping keyed by native symbol and country."""
    expected={'NativeTicker','Country','YahooTicker'}
    if not expected.issubset(overrides.columns):
        raise ValueError('Mappings require NativeTicker,Country,YahooTicker')
    mapping=overrides.copy().fillna('')
    mapping['YahooTicker']=mapping.YahooTicker.astype(str).str.strip()
    mapping=mapping[mapping.YahooTicker.ne('')]
    if mapping.duplicated(['NativeTicker','Country']).any():
        raise ValueError('Duplicate native ticker and country in override mapping')
    if not mapping.YahooTicker.str.match(r'^[A-Za-z0-9^=_.\-]+$').all():
        raise ValueError('Invalid Yahoo ticker in mapping CSV')
    lookup={(str(r.NativeTicker),str(r.Country)):str(r.YahooTicker) for r in mapping.itertuples()}
    out=data.copy()
    for idx,row in out.iterrows():
        chosen=lookup.get((str(row.NativeTicker),str(row.Country)))
        if chosen:
            out.at[idx,'Ticker']=chosen
            out.at[idx,'MappingStatus']='user-supplied mapping (not independently verified)'
    return out

# ISO 10383 exchange MIC to Yahoo Finance suffix. These are venue hints,
# NOT proof of a particular security's quotation or symbol.
MIC_SUFFIX = {
 'XLON':'.L','XPAR':'.PA','XETR':'.DE','XAMS':'.AS','XSWX':'.SW',
 'XMIL':'.MI','XMAD':'.MC','XSTO':'.ST','XCSE':'.CO','XOSL':'.OL',
 'XHEL':'.HE','XBRU':'.BR','XWBO':'.VI','XLIS':'.LS','XDUB':'.IR',
 'XWAR':'.WA','XATH':'.AT'
}
ISIN_PATTERN = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')

def valid_isin(isin):
    """Validate ISO 6166 ISIN format and Luhn check digit."""
    v = str(isin or '').strip().upper()
    if not ISIN_PATTERN.fullmatch(v): return False
    expanded = ''.join(str(ord(ch)-55) if ch.isalpha() else ch for ch in v)
    return sum((int(ch)*2//10 + int(ch)*2%10) if index%2 else int(ch)
               for index,ch in enumerate(reversed(expanded))) % 10 == 0

def apply_isin_exchange_mapping(data, mapping):
    """Validate a provider-supplied mapping, keyed by ISIN and exchange MIC.

    A valid ISIN check digit confirms formatting, *not* that an ISIN is genuine,
    or that the Yahoo ticker resolves to that same traded share class.
    """
    required={'NativeTicker','ISIN','ExchangeMIC','YahooTicker','EvidenceURL','VerifiedAsOf'}
    if not required.issubset(mapping.columns):
        raise ValueError('ISIN mapping needs: '+', '.join(sorted(required)))
    m=mapping.copy().fillna('')
    for c in required:m[c]=m[c].astype(str).str.strip()
    m['ISIN']=m.ISIN.str.upper();m['ExchangeMIC']=m.ExchangeMIC.str.upper()
    if m.duplicated(['NativeTicker']).any():
        raise ValueError('Duplicate NativeTicker: identify individual listings before importing')
    if not m.ISIN.map(valid_isin).all():
        raise ValueError('Invalid ISIN format/check digit in mapping')
    if not m.ExchangeMIC.isin(MIC_SUFFIX).all():
        raise ValueError('Unrecognized ExchangeMIC; add a reviewed venue mapping first')
    if not m.YahooTicker.str.fullmatch(r'[A-Za-z0-9^=_.\-]+').all():
        raise ValueError('Invalid Yahoo ticker')
    if not m.apply(lambda r:r.YahooTicker.upper().endswith(MIC_SUFFIX[r.ExchangeMIC].upper()),axis=1).all():
        raise ValueError('Yahoo ticker suffix conflicts with ExchangeMIC')
    if not m.EvidenceURL.str.match(r'^https://[^\s]+$').all():
        raise ValueError('Each mapping needs an HTTPS evidence URL to the listing/security record')
    if pd.to_datetime(m.VerifiedAsOf,errors='coerce').isna().any():
        raise ValueError('VerifiedAsOf must be a valid date')
    idx=m.set_index('NativeTicker')
    out=data.copy()
    if 'NativeTicker' not in out.columns:raise ValueError('Roster must contain NativeTicker')
    for c in ('ISIN','ExchangeMIC','EvidenceURL','VerifiedAsOf'):
        if c not in out:out[c]=''
    if 'MappingStatus' not in out:out['MappingStatus']='unmapped'
    for i,r in out.iterrows():
        key=str(r.NativeTicker)
        if key not in idx.index:continue
        val=idx.loc[key]
        out.at[i,'Ticker']=val.YahooTicker
        for c in ('ISIN','ExchangeMIC','EvidenceURL','VerifiedAsOf'):out.at[i,c]=val[c]
        out.at[i,'MappingStatus']='documented ISIN + MIC mapping (identity not independently verified)'
    return out
