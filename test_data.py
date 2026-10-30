import io, unittest
import pandas as pd
from sector_data import read_prices, weekly_completed, last_completed_friday
class Check(unittest.TestCase):
 def test_csv(self):
  p=read_prices(io.StringIO('Date,Ticker,Close\n2026-01-02,SPY,600\n2026-01-05,SPY,605\n'))
  self.assertEqual(len(p),2)
 def test_duplicates(self):
  with self.assertRaises(ValueError):read_prices(io.StringIO('Date,Ticker,Close\n2026-01-02,SPY,600\n2026-01-02,SPY,605\n'))
 def test_friday_exclusion(self):
  self.assertEqual(str(last_completed_friday('2026-10-30').date()),'2026-10-23')
  self.assertEqual(str(last_completed_friday('2026-10-31').date()),'2026-10-30')
 def test_week_end(self):
  x=pd.DataFrame({'SPY':[100,102,103]},index=pd.to_datetime(['2026-10-22','2026-10-23','2026-10-29']))
  w=weekly_completed(x,today='2026-10-30')
  self.assertEqual(len(w),1)
  self.assertEqual(w.iloc[-1,0],102)
if __name__=='__main__':unittest.main()
