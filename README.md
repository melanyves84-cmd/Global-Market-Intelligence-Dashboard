# Global Market Intelligence — three-region sector rotation

Streamlit website for **United States, Europe and mainland China**, expanded from the previous dashboard.

## Launch

```bash
pip install -r requirements.txt
streamlit run app.py
```

Deploy on Streamlit Community Cloud from a GitHub repository, selecting `app.py` as the entry point. Keep `extension.py` and `requirements.txt` beside it.

## New global features

- **Global heatmap**: 11 aligned sector labels × 3 markets; data deliberately marked N/A when unavailable.
- **Weekly signals**: 1, 4, 8, 13, 26 or 52 completed weeks. Relative returns are percentage-point differences against each region's own benchmark.
- **Coverage diagnostics**: shows which of the 33 cells have a valid data series.
- **Sector data catalog**: download a 33-row mapping CSV, add approved ticker symbols and upload it back to the site.
- **Existing pages remain**: market overview, daily sector charts (1 month–5 years), weekly ranking, US subsectors and methodology.

## Benchmarks and sector classifications

- **US:** SPY and the 11 standard US sector ETFs (complete proxy ticker mapping).
- **Europe:** EXSA.DE as the STOXX Europe 600 proxy. Sector membership in STOXX's official family uses **ICB**, not GICS, and the website does not automatically pretend those are equivalent. Two documented European ETF proxies are included as starters; others need a verified mapping.
- **China:** 510300.SS as the CSI 300 proxy. The original CSI 300 ten-industry classification historically grouped **financials and real estate**. The site does not silently assign those old series to both GICS sectors. Other 11-sector series must be licensed, acquired or loaded by CSV.

Official references:
- https://stoxx.com/index/SXXP/
- https://www.stoxx.com/download/indices/factsheets/SXFGR.pdf
- https://www.szse.cn/disclosure/notice/general/t20070611_499843.html
- https://www.msci.com/indexes/group/sector-indexes

## Data input

Choose **Upload daily CSV (offline)** in the sidebar. The input must contain three columns:

```csv
Date,Ticker,Close
2026-01-02,SPY,600.00
2026-01-02,XLK,240.00
2026-01-02,EXSA.DE,50.00
2026-01-02,510300.SS,4.00
```

These rows illustrate **CSV structure only**, not actual historical market prices. Use genuine sourced prices; use consistent adjusted-close conventions within each region, and respect provider licensing.

You can also upload a separate `sector_mapping.csv` produced by the sector-data catalog page. It has `Region,Sector,Ticker` fields and overrides the app's default map. For Europe and China, a **full 11-sector price series for each region** is needed for a fully populated and consistent global heatmap.

The online Yahoo Finance interface (`yfinance`) is **best effort**, may be blocked and does not supply every official sector index. Provider ticker availability and distribution licensing are not guaranteed.

## Calculations

Each Friday-ending week uses that week's last trading price. An incomplete week is excluded. Sector weekly percentage return minus *the same region's* benchmark weekly percentage return = relative performance in percentage points. Heatmap is not proof of capital inflows.

**Note:** the 11 displayed labels are a common comparison scheme, not evidence of unified index methodology. Don't draw strict cross-market conclusions until all source series have matching classifications and adjustment rules. No invented prices are bundled.

## Sector index data: Europe and China

The 33-slot GICS-style heatmap is ready for licensed histories but is **not a completed, fully sourced 33-index dataset**. Do not treat ETF proxies or the 10 older CSI 300 industry indices as directly equivalent to 11 constituent-matched GICS sectors.

To import approved data:
1. Export **daily closing index levels** (ideally dividend-adjusted / net total-return consistently) from your licensed STOXX/CSI or approved data vendor into `Date,Ticker,Close` CSV. One row per date and index symbol. No duplicate date-symbol observations.
2. Open **Sector data catalog**, download the mapping CSV, add each provider symbol to the desired region/sector row. The benchmark symbol is SPY (US), EXSA.DE (Europe), or 510300.SS (China) unless you change the code to match your licensed index benchmark.
3. In the sidebar upload the mapping CSV and your price CSV. Select **Global heatmap**. The application calculates weekly sector-minus-benchmark percentage-point returns only where data exist.
4. The current Friday-ending week is excluded until the following Saturday, preventing partially completed weekly comparisons.

Important: STOXX sector indices use ICB classification and official CSI 300 legacy industries use 10 buckets, including combined financials/real estate. Full 11-sector harmonization requires licensed GICS-aligned provider series or a transparently specified constituent-and-weight methodology. **No fabricated missing-sector data is included.**

Official references: https://www.stoxx.com/help ; https://stoxx.com/index/s600csv/ ; https://www.szse.cn/disclosure/notice/general/t20070611_499843.html ; https://www.ciis.com.hk/hongkong/en/uploadfiles/202507/21/2025072109322370585011.pdf

## Design B — modern light dashboard

This edition retains all existing market-data, import, heatmap, weekly rotation, and sector-history calculations while adding a consistent light design.

- Theme: `.streamlit/config.toml` (light background, navy text, #215F9A blue accent).
- Presentation components: `ui_theme.py` (header, sidebar, panels, chart styling).
- Replace all repository files, including the hidden `.streamlit` directory, when updating the hosted app.
- If GitHub's web uploader does not expose hidden folders easily, create `.streamlit/config.toml` through GitHub's **Add file → Create new file** path.
- No market observations are bundled; the application requires Yahoo Finance retrieval or a user-supplied CSV.
- The price data feed, data quality and licensed-coverage limitations of the prior edition still apply.
