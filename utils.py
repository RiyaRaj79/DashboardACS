# =============================================================================
# utils.py - Utility Functions: Formatting, Export, UI Components
# =============================================================================
"""
Provides:
  - Number / date formatting helpers
  - KPI card HTML renderer
  - CSV / Excel export buffers
  - Streamlit sidebar filter builder
  - Loading spinner context
  - Data table renderer
"""

import io
import logging
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from config import COLORS, COLUMNS

logger = logging.getLogger("utils")


# ===========================================================================
# FORMATTING HELPERS
# ===========================================================================

def fmt_number(n: Any, decimals: int = 0) -> str:
    """Format a number with thousand-separator commas."""
    try:
        if decimals > 0:
            return f"{float(n):,.{decimals}f}"
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def fmt_pct(n: Any, decimals: int = 1) -> str:
    """Format number as percentage string."""
    try:
        return f"{float(n):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def fmt_date(d: Any) -> str:
    """Format a date or datetime to a readable string."""
    if d is None or (isinstance(d, float) and np.isnan(d)):
        return "N/A"
    try:
        return pd.Timestamp(d).strftime("%d %b %Y")
    except Exception:
        return str(d)


def trend_icon(value: float) -> str:
    """Return ↑ / ↓ / → based on numeric growth value."""
    if value > 0:
        return "↑"
    if value < 0:
        return "↓"
    return "→"


def trend_color(value: float) -> str:
    """Return CSS colour for positive/negative/neutral trend."""
    if value > 0:
        return COLORS["success"]
    if value < 0:
        return COLORS["danger"]
    return COLORS["text_secondary"]


# ===========================================================================
# KPI CARD COMPONENT
# ===========================================================================

def kpi_card(
    container: DeltaGenerator,
    icon: str,
    label: str,
    value: str,
    sub: str = "",
    trend: float = None,
    color: str = None,
) -> None:
    """
    Render a styled KPI metric card using Streamlit markdown.

    Parameters
    ----------
    container : st column or container
    icon      : Emoji icon
    label     : KPI label text
    value     : Primary value (already formatted as string)
    sub       : Subtitle / secondary metric
    trend     : Optional float growth % for the trend indicator
    color     : Optional override for the accent border color
    """
    border_color = color or COLORS["accent"]
    trend_html   = ""
    if trend is not None:
        t_color = trend_color(trend)
        t_icon  = trend_icon(trend)
        trend_html = (
            f'<span style="color:{t_color};font-size:0.85rem;font-weight:600;">'
            f'{t_icon} {fmt_pct(abs(trend))} YoY</span>'
        )

    html = f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['bg_card']} 0%, {COLORS['bg_card2']} 100%);
        border: 1px solid {COLORS['border']};
        border-left: 4px solid {border_color};
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    ">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:1.6rem;">{icon}</span>
            <span style="color:{COLORS['text_secondary']};font-size:0.78rem;font-weight:600;
                         letter-spacing:0.08em;text-transform:uppercase;">{label}</span>
        </div>
        <div style="color:{COLORS['text_primary']};font-size:2rem;font-weight:700;
                    line-height:1.1;margin-bottom:4px;">{value}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:{COLORS['text_secondary']};font-size:0.8rem;">{sub}</span>
            {trend_html}
        </div>
    </div>
    """
    container.markdown(html, unsafe_allow_html=True)


def insight_card(
    container: DeltaGenerator,
    insight: dict,
) -> None:
    """Render a single AI insight card."""
    type_styles = {
        "success": (COLORS["success"],  "#0D2E1A"),
        "warning": (COLORS["warning"],  "#2E1F0A"),
        "danger" : (COLORS["danger"],   "#2E0D0D"),
        "info"   : (COLORS["info"],     "#0A1A2E"),
    }
    border, bg = type_styles.get(insight.get("type", "info"), (COLORS["accent"], COLORS["bg_card"]))
    html = f"""
    <div style="
        background: {bg};
        border: 1px solid {border};
        border-left: 4px solid {border};
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    ">
        <div style="font-size:1.05rem;font-weight:700;color:{COLORS['text_primary']};margin-bottom:5px;">
            {insight.get('icon','')} &nbsp;{insight.get('title','')}
        </div>
        <div style="color:{COLORS['text_secondary']};font-size:0.88rem;line-height:1.55;">
            {insight.get('detail','')}
        </div>
    </div>
    """
    container.markdown(html, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header."""
    st.markdown(f"""
    <div style="margin: 18px 0 14px 0; padding-bottom: 8px;
                border-bottom: 2px solid {COLORS['border']};">
        <h3 style="color:{COLORS['text_primary']};font-size:1.3rem;margin:0;font-weight:700;">
            {title}
        </h3>
        {"<p style='color:"+COLORS['text_secondary']+";font-size:0.85rem;margin:4px 0 0 0;'>"+subtitle+"</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """Render a styled page header."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {COLORS['gradient_start']} 0%, {COLORS['gradient_end']} 100%);
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 22px;
        border: 1px solid {COLORS['border']};
    ">
        <h1 style="color:{COLORS['text_primary']};font-size:1.7rem;margin:0;font-weight:800;">
            {title}
        </h1>
        {"<p style='color:"+COLORS['text_secondary']+";font-size:0.9rem;margin:6px 0 0 0;'>"+subtitle+"</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def divider() -> None:
    st.markdown(
        f'<hr style="border:none;border-top:1px solid {COLORS["border"]};margin:14px 0;">',
        unsafe_allow_html=True,
    )


# ===========================================================================
# FILTER BUILDER
# ===========================================================================

def build_sidebar_filters(df: pd.DataFrame) -> dict:
    """
    Build all sidebar filter widgets and return a dict of selected values.
    Returns ``{}`` if *df* is empty.
    """
    if df.empty:
        return {}

    selected = {}

    st.sidebar.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:0.75rem;"
        f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
        f"margin-bottom:8px;'>🔍 Search</div>",
        unsafe_allow_html=True,
    )
    selected["search"] = st.sidebar.text_input(
        "", placeholder="Asset ID, Name, Custodian…", label_visibility="collapsed"
    )

    st.sidebar.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:0.75rem;"
        f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
        f"margin:12px 0 8px 0;'>📅 Install Date</div>",
        unsafe_allow_html=True,
    )
    io_col = COLUMNS["installed_on"]
    date_start = date_end = None
    if io_col in df.columns:
        valid_dates = df[io_col].dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min().date()
            max_d = valid_dates.max().date()
            date_start = st.sidebar.date_input("From", value=min_d, min_value=min_d, max_value=max_d, key="date_from")
            date_end   = st.sidebar.date_input("To",   value=max_d, min_value=min_d, max_value=max_d, key="date_to")
    selected["date_start"] = date_start
    selected["date_end"]   = date_end

    # Categorical multi-select filters
    filters_cfg = [
        ("🏷️ Class",           COLUMNS["asset_class"]),
        ("📍 Location",        COLUMNS["location"]),
        ("🌐 Region",          COLUMNS["region"]),
        ("🏢 Department",      COLUMNS["department"]),
        ("🔧 CI Type",         COLUMNS["ci_type"]),
        ("💡 Hardware Status", COLUMNS["hw_status"]),
        ("🏭 Manufacturer",    COLUMNS["manufacturer"]),
        ("📊 Asset Criteria",  COLUMNS["asset_criteria"]),
        ("👥 Team",            COLUMNS["team"]),
    ]

    for label, col in filters_cfg:
        if col in df.columns:
            unique_vals = sorted(df[col].dropna().unique().tolist())
            if unique_vals:
                st.sidebar.markdown(
                    f"<div style='color:{COLORS['text_secondary']};font-size:0.75rem;"
                    f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
                    f"margin:10px 0 4px 0;'>{label}</div>",
                    unsafe_allow_html=True,
                )
                selected[col] = st.sidebar.multiselect(
                    "", options=unique_vals, default=[], label_visibility="collapsed",
                    key=f"filter_{col}"
                )

    return selected


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply all filters from *build_sidebar_filters* to *df*.
    Returns the filtered DataFrame.
    """
    if df.empty or not filters:
        return df

    result = df.copy()
    io_col = COLUMNS["installed_on"]

    # Search
    from analytics import search_assets
    if filters.get("search"):
        result = search_assets(result, filters["search"])

    # Date range
    if io_col in result.columns:
        ds = filters.get("date_start")
        de = filters.get("date_end")
        if ds:
            result = result[result[io_col].dt.date >= ds]
        if de:
            result = result[result[io_col].dt.date <= de]

    # Categorical multiselect filters
    for col in [
        COLUMNS["asset_class"], COLUMNS["location"], COLUMNS["region"],
        COLUMNS["department"], COLUMNS["ci_type"], COLUMNS["hw_status"],
        COLUMNS["manufacturer"], COLUMNS["asset_criteria"], COLUMNS["team"],
    ]:
        selected = filters.get(col, [])
        if selected and col in result.columns:
            result = result[result[col].isin(selected)]

    return result


# ===========================================================================
# EXPORT
# ===========================================================================

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return DataFrame as UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Assets") -> bytes:
    """Return DataFrame as Excel bytes (xlsx)."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        # Auto-size columns
        ws = writer.sheets[sheet_name]
        for col in ws.columns:
            max_len = max(
                len(str(cell.value)) if cell.value else 0
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)
    return buf.getvalue()


def render_export_buttons(df: pd.DataFrame, prefix: str = "assets") -> None:
    """Render CSV and Excel download buttons side-by-side."""
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        st.download_button(
            label     = "⬇️ Export CSV",
            data      = df_to_csv_bytes(df),
            file_name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime      = "text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            label     = "📊 Export Excel",
            data      = df_to_excel_bytes(df),
            file_name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ===========================================================================
# DATA TABLE
# ===========================================================================

def render_data_table(
    df: pd.DataFrame,
    title: str = "Data Table",
    height: int = 420,
    hide_cols: list = None,
) -> None:
    """Render a styled interactive data table."""
    if df.empty:
        st.info("No data to display.")
        return

    display_df = df.copy()

    # Drop internal helper columns
    internal = [c for c in display_df.columns if str(c).startswith("_")]
    if hide_cols:
        internal += hide_cols
    display_df.drop(columns=[c for c in internal if c in display_df.columns], inplace=True)

    # Format datetime cols
    for col in display_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        display_df[col] = display_df[col].dt.strftime("%d %b %Y")

    section_header(title, f"{len(display_df):,} records")
    st.dataframe(
        display_df,
        use_container_width = True,
        height              = height,
    )


# ===========================================================================
# CHART CONFIG HELPER
# ===========================================================================

def chart_config() -> dict:
    """Standard plotly chart config for st.plotly_chart."""
    return dict(
        displayModeBar  = True,
        modeBarButtonsToRemove = ["lasso2d", "select2d"],
        toImageButtonOptions   = dict(
            format   = "png",
            filename = "tata_steel_chart",
            height   = 600,
            width    = 1200,
            scale    = 2,
        ),
        responsive      = True,
    )
