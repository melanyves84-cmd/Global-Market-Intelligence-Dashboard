# Global Market Intelligence — US / Europe / China

Expanded version of the previous US sector rotation Streamlit website.

## Install and launch

```bash
pip install -r requirements.txt
streamlit run app.py
```

Select **Market** in the sidebar to switch between US (S&P 500/SPY), Europe (STOXX Europe 600/EXSA.DE), and mainland China (CSI 300/510300.SS).

Daily ETF adjusted closing prices are used for the charts; weekly Friday-ending close observations are used for 4-week and 13-week relative rotation scores. Missing series remain missing. CSV files with `Date,Ticker,Close` are supported for offline operation, including additional tickers matching configured mappings.

## Important coverage limitations

US: Original 11 sector ETFs, RSP equal-weight ETF and 45 named analytical subsectors (some without valid proxies).

Europe: 10 selected STOXX Europe 600 ETF proxies; financials proxy is **banks only**, discretionary is **automobiles only**, communication is **telecom only**, staples is **food and beverages only**. Materials is unassigned. These are not entire-sector representations. The underlying Europe ETF benchmark tracks STOXX Europe 600, not S&P Europe.

Mainland China: CSI 300 ETF baseline in CNY; verified semiconductor and pharmaceuticals ETF proxies available. The other sectors are left unassigned, as available ETFs require verification. China offshore equities in Hong Kong/US are not represented by the onshore CSI 300. In particular, discontinued Global X CHI* China sector ETFs are not used.

The website does not claim to track actual sector fund inflows. ETF price appreciation is not a fund flow measurement. Online yfinance data retrieval needs network access and may fail or be delayed. Public-market-data research prototype, not licensed commercial redistribution.
