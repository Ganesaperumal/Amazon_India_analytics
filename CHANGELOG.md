# 🔄 Changelog
### Amazon India Analytics Platform — Version History

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [2.0.0] — 2025-03-16 🚀 Major Release
*Complete platform overhaul — from basic dashboard to enterprise-grade BI platform*

### ✨ Added — New Pages
- `0_Data_Quality.py` — Full data cleaning showcase with before/after stats,
  quality score gauge, column health heatmap, and pipeline flow diagram
- `9_Simulator.py` — What-If Business Simulator with 6 adjustable levers,
  4 scenario presets, impact breakdown chart, and 2026 revenue projection
- `10_AI_Insights.py` — Groq AI powered chatbot with live DB context,
  8 suggested questions, multi-turn conversation, and data snapshot viewer

### ✨ Added — New Features to Existing Pages
- **Executive Page** — Business Health Score composite gauge (0-100)
  with 4-component progress bars (growth, delivery, returns, retention)
- **Revenue Page** — Year Comparison Mode toggle with side-by-side
  monthly revenue, AOV, orders, and category comparison + scorecard
- **Revenue Page** — Animated Revenue Replay (2015→2025) with Play/Pause
  buttons, year slider, and category color-coded bars
- **Customer Page** — Customer Persona Cards (4 per row) for each RFM
  segment with avatar, stats grid, and behavioral description
- **Festival Page** — GitHub-style Revenue Calendar Heatmap (12×11 grid)
  with festival labels, color intensity scale, and hover tooltips
- **Sidebar** — Top 5 Quick Findings expander with live DB-powered
  insights on every page

### 🔧 Changed
- Merged `assets/style.css` into `utils/sidebar.py` `_load_css()` function
  for single-file CSS management
- Fixed home page navigation cards — replaced broken HTML anchors with
  proper Streamlit `st.switch_page()` overlay approach
- Removed duplicate `stSidebarNav` CSS rules from both files
- Updated home page stats from "8 Pages · 90+ Charts" to
  "11 Pages · 100+ Charts · AI Powered"
- Updated `pages_info` and `NAV_ITEMS` to include all 11 pages

### 🔒 Security
- Removed hardcoded local DB path from `utils/db.py`
- Moved API key to `.streamlit/secrets.toml`
- Added `.gitignore` to prevent secrets, DB, and raw data from being committed

### 📁 Added — Project Files
- `requirements.txt` — pinned dependency versions
- `.streamlit/config.toml` — dark theme + server configuration
- `.streamlit/secrets.toml` — API key storage (not committed)
- `.gitignore` — GitHub safety rules
- `README.md` — comprehensive GitHub documentation
- `INSIGHTS.md` — 25 data-driven business findings
- `data_dictionary.md` — complete column reference guide
- `CHANGELOG.md` — this file

---

## [1.0.0] — 2025-03-01 🎯 Initial Release
*First working version submitted as GUVI × HCL capstone project*

### ✨ Added — Core Dashboard
- `app.py` — Home page with Amazon branding, KPI cards, navigation cards
- `1_Executive_Financial.py` — KPIs, yearly revenue, waterfall chart,
  cost vs revenue, financial forecasting
- `2_Revenue_Analytics.py` — Monthly heatmap, seasonal patterns,
  subcategory trends, avg monthly revenue
- `3_Customer_Analytics.py` — RFM segmentation, cohort heatmap,
  Prime analysis, age group patterns, funnel
- `4_Product_Brand.py` — Treemap, brand bubble chart, product lifecycle,
  competitive pricing analysis
- `5_Geographic.py` — City bubble map, state revenue, tier analysis
- `6_Payment_Operations.py` — Payment evolution, delivery gauges,
  return analysis, UPI growth
- `7_Festival_Seasonal.py` — Festival vs normal, per-festival revenue,
  monthly spike overlay, seasonal planning
- `8_Predictive_Advanced.py` — Prophet forecasting, churn prediction,
  cross-sell analysis, BI command center

### ✨ Added — Data Pipeline
- `notebook/01_data_cleaning.ipynb` — 10 cleaning operations
- `notebook/02_exploratory_data_analysis.ipynb` — 20 EDA visualizations
- `notebook/03_sql_integration.ipynb` — SQL schema + data loading
- 75+ EDA output charts saved to `outputs/`

### ✨ Added — Utilities
- `utils/db.py` — SQLite connection with caching
- `utils/sidebar.py` — Shared sidebar with 12 filters + navigation
- `assets/style.css` — Dark theme CSS (merged into sidebar in v2.0)

### 📊 Data
- Cleaned ~1M transactions across 2015–2025
- 4 normalized SQL tables with indexes
- 8 product categories, 30+ cities, 100+ brands

---

## 🗺️ Roadmap — Future Versions

### [2.1.0] — Planned
- [ ] Christmas festival fix in calendar heatmap
- [ ] Export to PDF button on Executive page
- [ ] Email alert system for KPI thresholds
- [ ] Mobile responsive layout improvements

### [2.2.0] — Planned  
- [ ] Streamlit Cloud deployment
- [ ] Multi-user authentication
- [ ] Scheduled data refresh pipeline
- [ ] Power BI version of dashboard

### [3.0.0] — Future Vision
- [ ] Real-time data streaming integration
- [ ] Advanced ML models (demand forecasting, price optimization)
- [ ] Natural language SQL query generation
- [ ] API endpoint for external dashboard consumption

---

*Amazon India Analytics Platform · GUVI × HCL Capstone Project*
*Maintained by Ganesaperumal*
```

---

## 🎉 All Documents Complete!

Here's everything that's been done:

**Documents ✅**
- `README.md`
- `INSIGHTS.md`
- `data_dictionary.md`
- `CHANGELOG.md`
- `.gitignore`

---

## Final Checklist Before GitHub Upload

**Rename your folder:**
`amazon_in_analyticsV2 (Copy)` → `amazon_india_analytics`

**Verify these files exist:**
```
amazon_india_analytics/
├── .streamlit/
│   ├── config.toml       ✅
│   └── secrets.toml      ✅ (NOT uploaded to GitHub)
├── pages/                ✅ 11 pages
├── utils/                ✅
├── notebook/             ✅
├── data/                 ✅
├── outputs/              ✅
├── app.py                ✅
├── requirements.txt      ✅
├── .gitignore            ✅
├── README.md             ✅
├── INSIGHTS.md           ✅
├── data_dictionary.md    ✅
└── CHANGELOG.md          ✅