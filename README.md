# Tata Steel IT Asset Dashboard

A production-ready, fully interactive IT Asset Management dashboard built with **Streamlit**, **Plotly**, **Pandas**, and **SQLAlchemy**.

---

## 📁 Project Structure

```
dashboard_tatasteel/
├── app.py              ← Main Streamlit entry point (10 pages)
├── database.py         ← Data loading (Excel, CSV, SQLite/SQLAlchemy)
├── analytics.py        ← KPI engine, breakdowns, AI insights
├── charts.py           ← Plotly chart library (14 chart types)
├── utils.py            ← UI components, filters, export, formatting
├── config.py           ← All configuration (colors, columns, paths)
├── requirements.txt    ← Python dependencies
└── assets/
    ├── style.css       ← Supplementary CSS
    └── it_assets.xlsx  ← ← Place YOUR Excel file here
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd dashboard_tatasteel
pip install -r requirements.txt
```

### 2. Add Your Data *(optional)*

Copy your Excel file to `assets/it_assets.xlsx`  
**OR** upload it directly from the sidebar at runtime.

### 3. Run the Dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Executive Summary | Total assets, active rate, KPI cards, yearly trend |
| 📦 Asset Analytics | CI Type, Class, Manufacturer, Treemap |
| 📍 Location Analytics | Location/Region bars, Heatmap, Sunburst |
| 🏢 Department Analytics | Department breakdown, stacked bar, heatmap |
| 👤 Custodian Analytics | Workload distribution, top 20, histogram |
| 🔧 Hardware Status | Status donut, stacked location bars |
| 📅 Installation Trends | Monthly/Yearly/Quarterly trends, age buckets |
| 🔬 Advanced Analytics | Top/Bottom N, Outlier detection, Correlation |
| 🤖 AI Insights | Rule-based automated findings & recommendations |
| 📤 Export | CSV & Excel export for all views |

---

## 🎛️ Interactive Filters (Sidebar)

- 🔍 **Search** – Full-text across all columns  
- 📅 **Date Range** – Filter by Installation Date  
- 🏷️ **Class** – Multi-select  
- 📍 **Location** – Multi-select  
- 🌐 **Region** – Multi-select  
- 🏢 **Department** – Multi-select  
- 🔧 **CI Type** – Multi-select  
- 💡 **Hardware Status** – Multi-select  
- 🏭 **Manufacturer** – Multi-select  
- 📊 **Asset Criteria** – Multi-select  
- 👥 **Team** – Multi-select  

All charts, tables, and KPIs update instantly when filters change.

---

## 📋 Expected Column Names

Your Excel file should contain these columns (case-insensitive matching):

| Column | Description |
|--------|-------------|
| Asset ID | Unique identifier |
| Name | Asset name/label |
| Class | Asset class (Hardware, Network…) |
| Location | Physical site |
| Sublocation | Specific room/area |
| Region | Geographic region |
| Custodian | Owner/responsible person |
| Team | IT team |
| Support Group | Support tier |
| Department | Business unit |
| CI Type | Configuration item type |
| Hardware Status | Active / Maintenance / Retired… |
| Manufacturer | Vendor/brand |
| Company | Owning company |
| Installed On | Installation date (any parseable format) |
| Asset Criteria | Critical / Important / Standard |

---

## 🔌 Database Connection (SQLAlchemy)

The dashboard auto-saves loaded data to a local SQLite DB (`assets/it_assets.db`).

To connect to a different database, edit `config.py`:

```python
# Example: PostgreSQL
SQLALCHEMY_URL = "postgresql://user:password@host:5432/dbname"

# Example: MS SQL Server
SQLALCHEMY_URL = "mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server"
```

Then call `db.load_from_db(SQLALCHEMY_URL, "table_name")` in `app.py`.

---

## 📤 Exports

Every page that shows data includes **Export CSV** and **Export Excel** buttons.  
All Plotly charts have a built-in **Download as PNG** button (camera icon in the top-right of each chart).

---

## 🎨 Theming

Colors, fonts, and branding are centralised in `config.py` → `COLORS` dict.  
Dark mode is enabled by default via Plotly's `plotly_dark` template and custom CSS.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Excel not loading | Ensure file is `.xlsx` not `.xls` or re-save in Excel |
| Blank charts | Check that column names match `config.py → COLUMNS` |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
