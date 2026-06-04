# =============================================================================
# config.py - Configuration Settings for Tata Steel IT Asset Dashboard
# =============================================================================

import os

# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Default Excel data file – place your file here or change the path
DEFAULT_EXCEL_PATH = os.path.join(BASE_DIR, "assets", "it_assets.xlsx")

# SQLite fallback (created automatically when you load an Excel file)
SQLITE_DB_PATH = os.path.join(BASE_DIR, "assets", "it_assets.db")

# ---------------------------------------------------------------------------
# Dashboard Metadata
# ---------------------------------------------------------------------------
APP_TITLE    = "Tata Steel IT Asset Management Dashboard"
APP_ICON     = "🏭"
APP_VERSION  = "1.0.0"
COMPANY_NAME = "Tata Steel"
TAGLINE      = "Intelligent IT Asset Intelligence Platform"

# ---------------------------------------------------------------------------
# Tata Steel Brand Color Palette
# ---------------------------------------------------------------------------
COLORS = {
    "primary"      : "#1A3A5C",   # Deep Navy Blue  – Tata Steel brand
    "secondary"    : "#C0392B",   # Tata Red accent
    "accent"       : "#00B4D8",   # Cyan highlight
    "accent2"      : "#F39C12",   # Amber / gold
    "success"      : "#27AE60",   # Green
    "warning"      : "#E67E22",   # Orange
    "danger"       : "#E74C3C",   # Red
    "info"         : "#2E86C1",   # Blue info
    "bg_dark"      : "#0D1117",   # Page background
    "bg_card"      : "#161B22",   # Card background
    "bg_card2"     : "#1C2330",   # Alternate card
    "bg_sidebar"   : "#0A0F1A",   # Sidebar
    "text_primary" : "#E6EDF3",   # Primary text
    "text_secondary": "#8B949E",  # Muted text
    "border"       : "#30363D",   # Border / divider
    "gradient_start": "#1A3A5C",
    "gradient_end"  : "#0D1B2E",
}

# Plotly chart color sequences
CHART_COLORS = [
    "#00B4D8", "#1A3A5C", "#F39C12", "#C0392B", "#27AE60",
    "#8E44AD", "#E67E22", "#2ECC71", "#3498DB", "#E91E63",
    "#FF6F00", "#00BCD4", "#9C27B0", "#4CAF50", "#FF5722",
]

# ---------------------------------------------------------------------------
# Plotly Global Template (dark / branded)
# ---------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"

PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor = "rgba(22,27,34,0.0)",
    plot_bgcolor  = "rgba(22,27,34,0.0)",
    font          = dict(family="Inter, Segoe UI, sans-serif", color="#E6EDF3", size=12),
    margin        = dict(l=20, r=20, t=40, b=20),
    legend        = dict(
        bgcolor      = "rgba(22,27,34,0.7)",
        bordercolor  = "#30363D",
        borderwidth  = 1,
        font         = dict(color="#E6EDF3"),
    ),
    colorway = CHART_COLORS,
)

# ---------------------------------------------------------------------------
# Column Definitions  (matches the provided Excel schema)
# ---------------------------------------------------------------------------
COLUMNS = {
    "asset_id"      : "Asset ID",
    "name"          : "Name",
    "asset_class"   : "Class",
    "location"      : "Location",
    "sublocation"   : "Sublocation",
    "region"        : "Region",
    "custodian"     : "Custodian",
    "team"          : "Team",
    "support_group" : "Support Group",
    "department"    : "Department",
    "ci_type"       : "CI Type",
    "hw_status"     : "Hardware Status",
    "manufacturer"  : "Manufacturer",
    "company"       : "Company",
    "installed_on"  : "Installed On",
    "asset_criteria": "Asset Criteria",
}

# Columns used as categorical filter options
CATEGORICAL_FILTER_COLS = [
    "Class", "Location", "Region", "Team",
    "Department", "CI Type", "Hardware Status",
    "Manufacturer", "Company", "Asset Criteria",
]

# ---------------------------------------------------------------------------
# KPI Thresholds
# ---------------------------------------------------------------------------
KPI_THRESHOLDS = {
    "active_asset_pct_good"    : 80,   # % active considered healthy
    "active_asset_pct_warning" : 60,
    "top_n_performers"         : 10,
    "bottom_n_performers"      : 10,
}

# ---------------------------------------------------------------------------
# Cache TTL (seconds) for Streamlit cache_data
# ---------------------------------------------------------------------------
CACHE_TTL = 300   # 5 minutes

# ---------------------------------------------------------------------------
# Page Navigation
# ---------------------------------------------------------------------------
PAGES = [
    "🏠 Executive Summary",
    "📦 Asset Analytics",
    "📍 Location Analytics",
    "🏢 Department Analytics",
    "👤 Custodian Analytics",
    "🔧 Hardware Status",
    "📅 Installation Trends",
    "🔬 Advanced Analytics",
    "🤖 AI Insights",
    "📤 Export",
]
