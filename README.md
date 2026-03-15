<div align="center">

# 🛒 Amazon India: A Decade of Sales Analytics

### *From Raw Messy Data → Production-Ready Business Intelligence Dashboard*

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI_Powered-F55036?style=for-the-badge&logoColor=white)

**2015 – 2025 · ~1 Million Transactions · 11 Pages · 100+ Charts · 12 Filters · AI Powered**

*A GUVI × HCL Capstone Project*

</div>

---

## 📌 Project Overview

This is a comprehensive end-to-end **e-commerce analytics platform** built on Amazon India's simulated 10-year transactional dataset (2015–2025). The project covers the complete data science pipeline — from raw messy data with 25% quality issues, through advanced cleaning, SQL database integration, exploratory data analysis, and finally an interactive multi-page Streamlit dashboard with AI-powered business insights.

The platform is designed for **C-level executive decision making**, **marketing strategy**, **operational excellence**, and **business forecasting** — all powered by ~1 million real-world style transactions across 8 product categories, 30+ Indian cities, and 10 years of market evolution.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧹 **Advanced Data Cleaning** | 10 cleaning operations fixing 25% data quality issues |
| 📊 **11 Dashboard Pages** | Executive, Revenue, Customer, Product, Geographic, Payment, Festival, Predictive, Simulator, AI |
| 🤖 **AI Business Analyst** | Groq-powered chatbot answering live questions from your data |
| 🎮 **What-If Simulator** | Adjust business levers and project 2026 revenue outcomes |
| 📅 **Festival Calendar** | GitHub-style heatmap showing revenue hotspots across 10 years |
| 👥 **Customer Persona Cards** | RFM-based segmentation with live behavioral profiles |
| 🏥 **Business Health Score** | Composite 0-100 score from delivery, returns, growth, retention |
| 🔀 **Year Comparison Mode** | Side-by-side analysis of any two years |
| ▶️ **Animated Revenue Replay** | Watch revenue grow from 2015→2025 with Play button |
| 🎛️ **12 Interactive Filters** | Time, Location, Customer, Payment, Festival filters |
| 🗄️ **SQL Integration** | Normalized SQLite database with 4 tables and optimized indexes |

---

## 🗂️ Dashboard Pages

| # | Page | Key Contents |
|---|---|---|
| 0 | 🧹 Data Quality | Cleaning pipeline, before/after stats, column health heatmap |
| 1 | 📊 Executive & Financial | KPIs, health score, YoY waterfall, forecasting |
| 2 | 📈 Revenue Analytics | Monthly heatmap, year comparison, animated replay |
| 3 | 👥 Customer Analytics | RFM scatter, persona cards, cohort retention, funnel |
| 4 | 🛍️ Product & Brand | Treemap, brand bubble chart, lifecycle, pricing |
| 5 | 🗺️ Geographic | City bubble map, state ranking, tier analysis |
| 6 | 💳 Payment & Operations | UPI trends, delivery gauges, return analysis |
| 7 | 🎉 Festival & Seasonal | Festival calendar heatmap, spike overlay, ROI |
| 8 | 🔮 Predictive & Advanced | Prophet forecasting, churn, cross-sell, BI command center |
| 9 | 🎮 Business Simulator | What-if levers, scenario presets, 2026 projection |
| 10 | 🤖 AI Insights | Groq AI chatbot, suggested questions, live data context |

---

## 🛠️ Tech Stack

| Tool | Purpose | Version |
|---|---|---|
| Python | Core language | 3.11 |
| Streamlit | Dashboard framework | 1.45.0 |
| SQLite + SQLAlchemy | Database storage | 2.0.30 |
| Pandas | Data manipulation | 2.2.2 |
| NumPy | Numerical operations | 1.26.4 |
| Plotly | Interactive charts | 5.22.0 |
| Matplotlib + Seaborn | Static visualizations | 3.9.0 / 0.13.2 |
| Prophet | Time series forecasting | 1.1.5 |
| Scikit-learn | ML models | 1.5.0 |
| Groq API | AI business analyst | llama-3.1-8b-instant |

---

## 📁 Project Structure
```
amazon_india_analytics/
│
├── app.py                          # Home page — landing + navigation
│
├── pages/
│   ├── 0_Data_Quality.py           # Data cleaning showcase
│   ├── 1_Executive_Financial.py    # Executive dashboard
│   ├── 2_Revenue_Analytics.py      # Revenue analysis
│   ├── 3_Customer_Analytics.py     # Customer segmentation
│   ├── 4_Product_Brand.py          # Product & brand analysis
│   ├── 5_Geographic.py             # Geographic analysis
│   ├── 6_Payment_Operations.py     # Payment & operations
│   ├── 7_Festival_Seasonal.py      # Festival analytics
│   ├── 8_Predictive_Advanced.py    # Predictive analytics
│   ├── 9_Simulator.py              # Business simulator
│   └── 10_AI_Insights.py           # AI chatbot
│
├── utils/
│   ├── __init__.py
│   ├── db.py                       # SQLite connection + query runner
│   └── sidebar.py                  # Shared sidebar + filters + CSS
│
├── notebook/
│   ├── 01_data_cleaning.ipynb      # 10 cleaning operations
│   ├── 02_exploratory_data_analysis.ipynb  # 20 EDA visualizations
│   └── 03_sql_integration.ipynb    # SQL schema + data loading
│
├── data/
│   ├── amazon_india.db             # SQLite database (generated)
│   ├── amazon_india_products_catalog.csv
│   └── cleaned/
│       └── amazon_india_master_cleaned.csv
│
├── outputs/                        # EDA chart outputs (PNG)
│
├── .streamlit/
│   ├── config.toml                 # Theme + server config
│   └── secrets.toml                # API keys (NOT committed to Git)
│
├── requirements.txt                # Python dependencies
├── .gitignore                      # Excludes secrets, DB, raw data
├── README.md                       # This file
├── INSIGHTS.md                     # Business insights report
├── data_dictionary.md              # Column descriptions
└── CHANGELOG.md                    # Version history
```

---

## ⚙️ How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/amazon-india-analytics.git
cd amazon-india-analytics
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the Dataset
Download the raw data files from Google Drive:
👉 [Dataset Link](https://drive.google.com/drive/folders/1ZHB4x8nZHuXmyDlwujWtbOaxiMHWf-3-?usp=drive_link)

Place downloaded CSV files in:
```
data/raw/
```

### 4. Run Data Cleaning + SQL Setup
Open and run notebooks in order:
```
notebook/01_data_cleaning.ipynb
notebook/02_exploratory_data_analysis.ipynb  
notebook/03_sql_integration.ipynb
```
This generates `data/amazon_india.db`

### 5. Configure API Key
Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your-groq-api-key-here"
```
Get your free key at: https://console.groq.com

### 6. Run the Dashboard
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📊 Dataset

| Property | Details |
|---|---|
| Source | Simulated Amazon India transactional data |
| Period | 2015 – 2025 |
| Records | ~1,000,000 transactions |
| Tables | transactions, products, customers, time_dimension |
| Columns | 45+ transaction columns, 12+ product columns |
| Cities | 30+ Indian cities (Metro to Rural) |
| Categories | 8 major product categories, 25+ subcategories |
| Brands | 100+ Indian and global brands |
| Download | [Google Drive](https://drive.google.com/drive/folders/1ZHB4x8nZHuXmyDlwujWtbOaxiMHWf-3-?usp=drive_link) |

---

## 📸 Screenshots

> Add screenshots of your dashboard pages here after deployment.

| Home Page | Executive Dashboard |
|---|---|
| *screenshot* | *screenshot* |

| Customer Persona Cards | AI Insights |
|---|---|
| *screenshot* | *screenshot* |

---

## 🔒 Security Notes

- **Never commit** `.streamlit/secrets.toml` to GitHub
- **Never commit** `data/amazon_india.db` (large file)
- **Never commit** raw CSV files (large files)
- All sensitive files are excluded via `.gitignore`

---

## 📝 Related Documents

- 📊 [Business Insights Report](INSIGHTS.md)
- 📖 [Data Dictionary](data_dictionary.md)
- 🔄 [Changelog](CHANGELOG.md)

---

## 🙏 Acknowledgements

- **GUVI × HCL** — Project brief and dataset design
- **Streamlit** — Dashboard framework
- **Groq** — Free AI API powering the chatbot
- **Prophet (Meta)** — Time series forecasting

---

## 👤 Author

**Ganesaperumal**
- 📧 GUVI × HCL Data Science Program
- 🔗 GitHub: [@ganesaperumal](https://github.com/ganesaperumal)

---

<div align="center">
<i>Built with ❤️ using Python · Streamlit · Plotly · SQLite · Groq AI</i>
</div>