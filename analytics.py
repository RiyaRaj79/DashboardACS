# =============================================================================
# analytics.py - Business Analytics & KPI Engine
# =============================================================================
"""
Computes:
  - KPI Cards
  - Executive Summary metrics
  - Category / location / department breakdowns
  - Moving averages & growth rates
  - Outlier detection
  - Correlation analysis
  - AI-generated insights (rule-based)
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, date
from scipy import stats as scipy_stats

from config import COLUMNS, KPI_THRESHOLDS

logger = logging.getLogger("analytics")


# ===========================================================================
# HELPER UTILITIES
# ===========================================================================

def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division returning *default* when denominator is zero."""
    return numerator / denominator if denominator else default


def pct(part: float, total: float) -> float:
    """Return percentage (0-100)."""
    return round(safe_div(part, total) * 100, 2)


# ===========================================================================
# EXECUTIVE SUMMARY KPIs
# ===========================================================================

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Return a flat dict of all executive-level KPIs.
    """
    if df.empty:
        return {}

    total   = len(df)
    hw_col  = COLUMNS["hw_status"]
    loc_col = COLUMNS["location"]
    dept_col= COLUMNS["department"]
    ci_col  = COLUMNS["ci_type"]
    mfr_col = COLUMNS["manufacturer"]
    io_col  = COLUMNS["installed_on"]
    cls_col = COLUMNS["asset_class"]
    crit_col= COLUMNS["asset_criteria"]

    # Active asset count
    active_mask = (df[hw_col].str.lower() == "active") if hw_col in df.columns else pd.Series([True]*total)
    active_count= int(active_mask.sum())
    active_pct  = pct(active_count, total)

    # Retired / Decommissioned
    retired_mask = df[hw_col].str.lower().isin(["retired","decommissioned"]) if hw_col in df.columns else pd.Series([False]*total)
    retired_count= int(retired_mask.sum())

    # Maintenance
    maint_mask = df[hw_col].str.lower().str.contains("maint", na=False) if hw_col in df.columns else pd.Series([False]*total)
    maint_count= int(maint_mask.sum())

    # Critical assets
    critical_count = 0
    if crit_col in df.columns:
        critical_count = int((df[crit_col].str.lower() == "critical").sum())

    # Top location
    top_location = _top_value(df, loc_col)

    # Top department
    top_department = _top_value(df, dept_col)

    # Top CI type
    top_ci_type = _top_value(df, ci_col)

    # Top manufacturer
    top_manufacturer = _top_value(df, mfr_col)

    # Unique values
    n_locations   = df[loc_col].nunique()  if loc_col  in df.columns else 0
    n_departments = df[dept_col].nunique() if dept_col in df.columns else 0
    n_custodians  = df[COLUMNS["custodian"]].nunique() if COLUMNS["custodian"] in df.columns else 0
    n_ci_types    = df[ci_col].nunique()   if ci_col   in df.columns else 0

    # Installation range
    install_start = install_end = None
    assets_this_year = assets_last_year = 0
    yoy_growth = 0.0
    if io_col in df.columns:
        valid_dates   = df[io_col].dropna()
        if not valid_dates.empty:
            install_start = valid_dates.min().date()
            install_end   = valid_dates.max().date()
            cy = datetime.now().year
            assets_this_year = int((df["_install_year"] == cy).sum())
            assets_last_year = int((df["_install_year"] == cy - 1).sum())
            yoy_growth = safe_div(
                (assets_this_year - assets_last_year), assets_last_year
            ) * 100

    # Asset class breakdown
    top_class = _top_value(df, cls_col) if cls_col in df.columns else "N/A"

    return dict(
        total_assets      = total,
        active_count      = active_count,
        active_pct        = active_pct,
        retired_count     = retired_count,
        maint_count       = maint_count,
        critical_count    = critical_count,
        top_location      = top_location,
        top_department    = top_department,
        top_ci_type       = top_ci_type,
        top_manufacturer  = top_manufacturer,
        top_class         = top_class,
        n_locations       = n_locations,
        n_departments     = n_departments,
        n_custodians      = n_custodians,
        n_ci_types        = n_ci_types,
        install_start     = install_start,
        install_end       = install_end,
        assets_this_year  = assets_this_year,
        assets_last_year  = assets_last_year,
        yoy_growth        = round(yoy_growth, 1),
    )


def _top_value(df: pd.DataFrame, col: str) -> str:
    """Return the most frequent value in *col* or 'N/A'."""
    if col not in df.columns or df[col].dropna().empty:
        return "N/A"
    return str(df[col].value_counts().idxmax())


# ===========================================================================
# BREAKDOWNS
# ===========================================================================

def breakdown_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return a counts + percentage breakdown for a single column."""
    if col not in df.columns or df.empty:
        return pd.DataFrame()
    counts = df[col].value_counts(dropna=False).reset_index()
    counts.columns = [col, "Count"]
    counts["Percentage"] = (counts["Count"] / counts["Count"].sum() * 100).round(2)
    return counts


def multi_breakdown(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """Cross-tab pivot of col1 vs col2."""
    if col1 not in df.columns or col2 not in df.columns:
        return pd.DataFrame()
    pivot = pd.crosstab(df[col1], df[col2])
    return pivot


# ===========================================================================
# INSTALLATION TRENDS
# ===========================================================================

def monthly_installation_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Assets installed per year-month (string period)."""
    if "_install_ym" not in df.columns:
        return pd.DataFrame()
    trend = (
        df.groupby("_install_ym").size()
          .reset_index(name="Assets Installed")
          .sort_values("_install_ym")
    )
    trend.rename(columns={"_install_ym": "Year-Month"}, inplace=True)
    trend["Moving Avg (3M)"] = (
        trend["Assets Installed"].rolling(window=3, min_periods=1).mean().round(1)
    )
    return trend


def yearly_installation_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Assets installed per year with YoY growth %."""
    if "_install_year" not in df.columns:
        return pd.DataFrame()
    trend = (
        df.groupby("_install_year").size()
          .reset_index(name="Assets Installed")
          .sort_values("_install_year")
    )
    trend["YoY Growth %"] = trend["Assets Installed"].pct_change().mul(100).round(1)
    trend.rename(columns={"_install_year": "Year"}, inplace=True)
    return trend


def quarterly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Assets installed per quarter."""
    if "_install_quarter" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby("_install_quarter").size()
          .reset_index(name="Assets Installed")
          .sort_values("_install_quarter")
          .rename(columns={"_install_quarter": "Quarter"})
    )


# ===========================================================================
# ADVANCED ANALYTICS
# ===========================================================================

def top_n_by(df: pd.DataFrame, col: str, n: int = 10) -> pd.DataFrame:
    """Top-N rows by asset count for a given column."""
    return breakdown_by(df, col).head(n)


def bottom_n_by(df: pd.DataFrame, col: str, n: int = 10) -> pd.DataFrame:
    """Bottom-N rows by asset count for a given column."""
    return breakdown_by(df, col).tail(n).iloc[::-1]


def detect_outliers_zscore(df: pd.DataFrame, col: str, threshold: float = 2.5) -> pd.DataFrame:
    """
    Flag rows where the numeric *col* is an outlier (|z-score| > threshold).
    Returns the flagged rows with a z_score column added.
    """
    if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
        return pd.DataFrame()
    z = np.abs(scipy_stats.zscore(df[col].dropna()))
    outlier_idx = df[col].dropna().index[z > threshold]
    result = df.loc[outlier_idx].copy()
    result["z_score"] = np.abs(scipy_stats.zscore(df[col].dropna()))[z > threshold]
    return result


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix of numeric columns (min 2 numeric cols required)."""
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return pd.DataFrame()
    return num_df.corr().round(3)


def growth_rate_by_period(df: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month growth rate table."""
    trend = monthly_installation_trend(df)
    if trend.empty:
        return pd.DataFrame()
    trend["MoM Growth %"] = trend["Assets Installed"].pct_change().mul(100).round(1)
    return trend


def assets_by_age(df: pd.DataFrame) -> pd.DataFrame:
    """Bucket assets by age (years since installation)."""
    io_col = COLUMNS["installed_on"]
    if io_col not in df.columns:
        return pd.DataFrame()
    now = pd.Timestamp.now()
    df = df.copy()
    df["Age (Years)"] = ((now - df[io_col]).dt.days / 365.25).round(1)
    df["Age Bucket"] = pd.cut(
        df["Age (Years)"],
        bins  = [-0.1, 1, 3, 5, 7, np.inf],
        labels= ["<1 yr", "1-3 yrs", "3-5 yrs", "5-7 yrs", "7+ yrs"],
    )
    return df[["Asset ID", "Name", "Age (Years)", "Age Bucket", "Location", "Department", "Hardware Status"]].dropna(subset=["Age (Years)"])


def custodian_load(df: pd.DataFrame) -> pd.DataFrame:
    """Number of assets per custodian (workload distribution)."""
    col = COLUMNS["custodian"]
    if col not in df.columns:
        return pd.DataFrame()
    return breakdown_by(df, col)


def location_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tab of Location × CI Type for heatmap."""
    return multi_breakdown(df, COLUMNS["location"], COLUMNS["ci_type"])


def department_status_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tab of Department × Hardware Status for stacked bar."""
    return multi_breakdown(df, COLUMNS["department"], COLUMNS["hw_status"])


# ===========================================================================
# AI INSIGHTS
# ===========================================================================

def generate_insights(df: pd.DataFrame, kpis: dict) -> list:
    """
    Rule-based AI insights engine.
    Returns a list of insight dicts with keys:
      type       – 'success' | 'warning' | 'danger' | 'info'
      title      – short headline
      detail     – explanation
      icon       – emoji
    """
    insights = []
    if df.empty or not kpis:
        return insights

    ap    = kpis.get("active_pct", 0)
    rc    = kpis.get("retired_count", 0)
    mc    = kpis.get("maint_count", 0)
    cc    = kpis.get("critical_count", 0)
    total = kpis.get("total_assets", 1) or 1
    yoy   = kpis.get("yoy_growth", 0)

    # --- Active rate ---
    good = KPI_THRESHOLDS["active_asset_pct_good"]
    warn = KPI_THRESHOLDS["active_asset_pct_warning"]
    if ap >= good:
        insights.append(dict(
            type="success", icon="✅",
            title="Healthy Asset Utilisation",
            detail=f"{ap:.1f}% of assets are active – above the {good}% benchmark. Fleet is in excellent operational condition.",
        ))
    elif ap >= warn:
        insights.append(dict(
            type="warning", icon="⚠️",
            title="Moderate Asset Activity Rate",
            detail=f"Only {ap:.1f}% of assets are active. Review inactive assets to determine if they can be redeployed or decommissioned.",
        ))
    else:
        insights.append(dict(
            type="danger", icon="🚨",
            title="Low Asset Activity – Action Required",
            detail=f"Active rate is critically low at {ap:.1f}%. Immediate audit recommended.",
        ))

    # --- Retired / Decommissioned ---
    ret_pct = pct(rc, total)
    if ret_pct > 15:
        insights.append(dict(
            type="warning", icon="♻️",
            title="High Retirement Volume",
            detail=f"{rc} assets ({ret_pct:.1f}%) are retired / decommissioned. Consider optimising disposal and replacement planning.",
        ))

    # --- Maintenance queue ---
    maint_pct = pct(mc, total)
    if mc > 0:
        t = "danger" if maint_pct > 10 else "warning"
        insights.append(dict(
            type=t, icon="🔧",
            title=f"Maintenance Queue: {mc} Assets",
            detail=f"{maint_pct:.1f}% of assets are under maintenance. Ensure SLA timelines are tracked to avoid operational disruption.",
        ))

    # --- Critical assets ---
    crit_pct = pct(cc, total)
    if cc > 0:
        insights.append(dict(
            type="info", icon="🔴",
            title=f"{cc} Critical Assets Detected",
            detail=f"{crit_pct:.1f}% of assets are marked Critical. Ensure redundancy and priority support contracts are in place.",
        ))

    # --- YoY growth ---
    if yoy > 10:
        insights.append(dict(
            type="success", icon="📈",
            title="Strong Asset Growth This Year",
            detail=f"Year-over-Year asset addition grew by {yoy:.1f}%. Indicates expanding IT infrastructure investment.",
        ))
    elif yoy < -5:
        insights.append(dict(
            type="warning", icon="📉",
            title="Asset Addition Declined YoY",
            detail=f"New asset procurement declined by {abs(yoy):.1f}% compared to last year. Review budget allocation.",
        ))

    # --- Location concentration risk (fully safe) ---
    try:
        loc_col = COLUMNS["location"]
        if loc_col in df.columns:
            loc_vc = df[loc_col].dropna().value_counts()
            if len(loc_vc) > 0:
                top_loc_count = int(loc_vc.iat[0])
                top_loc_name  = str(loc_vc.index[0])
                top_loc_pct   = pct(top_loc_count, total)
                if top_loc_pct > 40:
                    insights.append(dict(
                        type="warning", icon="📍",
                        title="Location Concentration Risk",
                        detail=f"{top_loc_pct:.1f}% of assets are concentrated at '{top_loc_name}'. A single-point failure could have major operational impact.",
                    ))
    except Exception:
        pass

    # --- Manufacturer diversity (fully safe) ---
    try:
        mfr_col = COLUMNS["manufacturer"]
        if mfr_col in df.columns:
            mfr_vc = df[mfr_col].dropna().value_counts()
            if len(mfr_vc) > 0:
                top_mfr_count = int(mfr_vc.iat[0])
                top_mfr_name  = str(mfr_vc.index[0])
                top_mfr_pct   = pct(top_mfr_count, total)
                if top_mfr_pct > 50:
                    insights.append(dict(
                        type="info", icon="🏭",
                        title="Vendor Dependency Risk",
                        detail=f"{top_mfr_pct:.1f}% of assets are from '{top_mfr_name}'. Consider diversifying vendors to reduce supply chain risk.",
                    ))
    except Exception:
        pass

    # --- Custodian overload (fully safe) ---
    try:
        cust_col = COLUMNS["custodian"]
        if cust_col in df.columns:
            cust_vc = cust_col_data = df[cust_col].dropna().value_counts()
            if len(cust_vc) > 0:
                avg_load   = float(cust_vc.mean())
                overloaded = int((cust_vc > avg_load * 2).sum())
                if overloaded > 0:
                    insights.append(dict(
                        type="warning", icon="👤",
                        title=f"{overloaded} Overloaded Custodian(s)",
                        detail=f"Some custodians manage more than 2× the average asset load ({avg_load:.0f}). Redistribute for better accountability.",
                    ))
    except Exception:
        pass

    # --- Aging fleet (fully safe) ---
    try:
        io_col = COLUMNS["installed_on"]
        if io_col in df.columns:
            age_df = assets_by_age(df)
            if not age_df.empty and "Age Bucket" in age_df.columns:
                old_count = int((age_df["Age Bucket"] == "7+ yrs").sum())
                old_pct   = pct(old_count, total)
                if old_pct > 20:
                    insights.append(dict(
                        type="danger", icon="⏳",
                        title="Aging Fleet Risk",
                        detail=f"{old_pct:.1f}% of assets are 7+ years old. Plan for technology refresh to maintain reliability and security.",
                    ))
    except Exception:
        pass

    # --- Growth opportunity ---
    insights.append(dict(
        type="info", icon="💡",
        title="Growth Opportunity",
        detail="Use Location & Department heatmaps to identify departments with sub-optimal IT coverage and plan targeted investments.",
    ))

    return insights


# ===========================================================================
# SEARCH
# ===========================================================================

def search_assets(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Full-text search across all string columns."""
    if not query or df.empty:
        return df
    q = query.lower()
    mask = pd.Series([False] * len(df), index=df.index)
    for col in df.select_dtypes(include="object").columns:
        mask |= df[col].str.lower().str.contains(q, na=False)
    return df[mask]
