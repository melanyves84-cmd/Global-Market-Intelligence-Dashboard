import unittest
import pandas as pd
from europe_tickers import valid_isin, apply_isin_exchange_mapping
class TestIsin(unittest.TestCase):
 def test_checkdigit(self):
  self.assertTrue(valid_isin('NL0010273215'))
  self.assertFalse(valid_isin('NL0010273214'))
 def test_mapping(self):
  row={'NativeTicker':'ASML','ISIN':'NL0010273215','ExchangeMIC':'XAMS','YahooTicker':'ASML.AS','EvidenceURL':'https://example.org/security','VerifiedAsOf':'2026-10-30'}
  frame=pd.DataFrame([{'NativeTicker':'ASML','Ticker':'ASML.AS','MappingStatus':'candidate'}])
  mapped=apply_isin_exchange_mapping(frame,pd.DataFrame([row]))
  self.assertEqual(mapped.iloc[0].ExchangeMIC,'XAMS')
  self.assertIn('documented',mapped.iloc[0].MappingStatus)
  row['YahooTicker']='ASML.L'
  with self.assertRaises(ValueError):apply_isin_exchange_mapping(frame,pd.DataFrame([row]))
if __name__=='__main__':unittest.main()
