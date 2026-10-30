import unittest
import pandas as pd
from europe_tickers import candidate_symbol, enrich_european_roster, apply_verified_overrides
class MappingTests(unittest.TestCase):
    def test_countries(self):
        self.assertEqual(candidate_symbol('ASML','Netherlands')[0], 'ASML.AS')
        self.assertEqual(candidate_symbol('SAP','Germany')[0], 'SAP.DE')
        self.assertEqual(candidate_symbol('MC','France')[0], 'MC.PA')
        self.assertEqual(candidate_symbol('NOVN','Switzerland')[0], 'NOVN.SW')
    def test_unknown(self):
        self.assertEqual(candidate_symbol('TEST','Luxembourg')[0], '')
    def test_override(self):
        d=enrich_european_roster(pd.DataFrame([{'Ticker':'A','Country':'Luxembourg','Market':'Europe'}]))
        self.assertEqual(d.iloc[0].Ticker,'')
        o=apply_verified_overrides(d,pd.DataFrame([{'NativeTicker':'A','Country':'Luxembourg','YahooTicker':'A.PA'}]))
        self.assertEqual(o.iloc[0].Ticker,'A.PA')
if __name__=='__main__':unittest.main()
