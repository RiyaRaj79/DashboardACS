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
    Render a KPI card using st.metric() — fully compatible with Streamlit Cloud.
    No raw HTML divs used, so no stray </div> text can appear.
    """
    border_color = color or COLORS["accent"]

    # Build delta string for st.metric (shows trend arrow automatically)
    delta_str = None
    if trend is not None:
        sign = "+" if trend >= 0 else ""
        delta_str = f"{sign}{trend:.1f}% YoY"

    # Inject a one-time CSS class for this card's left border colour.
    # We use a unique key based on label so multiple cards don't clash.
    safe_key = label.lower().replace(" ", "_").replace("/", "_")
    container.markdown(
        f"""
        <style>
        div[data-testid="metric-container"] {{
            border-left: 4px solid {COLORS['accent']} !important;
        }}
        </style>
        <p style="margin:0 0 2px 0;
                  font-size:0.78rem;
                  font-weight:600;
                  letter-spacing:0.08em;
                  text-transform:uppercase;
                  color:{COLORS['text_secondary']};">  
            {icon}&nbsp;&nbsp;{label}
        </p>
        """,
        unsafe_allow_html=True,
    )
    container.metric(
        label      = "",
        value      = value,
        delta      = delta_str,
        label_visibility = "collapsed",
    )
    if sub:
        container.markdown(
            f"<p style='margin:-8px 0 8px 0;font-size:0.78rem;color:{COLORS['text_secondary']};'>{sub}</p>",
            unsafe_allow_html=True,
        )


def insight_card(
    container: DeltaGenerator,
    insight: dict,
) -> None:
    """Render a single AI insight card using safe markdown (no nested divs)."""
    type_map = {
        "success": ("#27AE60", "#0D2E1A"),
        "warning": ("#E67E22", "#2E1F0A"),
        "danger" : ("#E74C3C", "#2E0D0D"),
        "info"   : ("#2E86C1", "#0A1A2E"),
    }
    border, bg = type_map.get(insight.get("type", "info"), (COLORS["accent"], COLORS["bg_card"]))
    icon  = insight.get("icon", "")
    title = insight.get("title", "")
    detail= insight.get("detail", "")
    # Use a table-free, single-tag approach to avoid sanitiser stripping
    container.markdown(
        f"<p style=\""
        f"background:{bg};"
        f"border:1px solid {border};"
        f"border-left:4px solid {border};"
        f"border-radius:10px;"
        f"padding:14px 16px;"
        f"margin-bottom:10px;"
        f"display:block;\""
        f"><strong style='color:{COLORS['text_primary']};font-size:1rem;'>"
        f"{icon} {title}</strong>"
        f"<br><span style='color:{COLORS['text_secondary']};font-size:0.87rem;line-height:1.6;'>"
        f"{detail}</span></p>",
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header using safe inline elements only."""
    st.markdown(
        f"<h3 style='color:{COLORS['text_primary']};font-size:1.2rem;font-weight:700;"
        f"margin:18px 0 4px 0;padding-bottom:8px;"
        f"border-bottom:2px solid {COLORS['border']};'>{title}</h3>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.83rem;margin:0 0 10px 0;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


def page_header(title: str, subtitle: str = "") -> None:
    """Render a styled page header using safe single-block markdown."""
    sub_html = (
        f"<br><span style='color:{COLORS['text_secondary']};font-size:0.9rem;'>{subtitle}</span>"
        if subtitle else ""
    )
    st.markdown(
        f"<h1 style=\""
        f"background:linear-gradient(90deg,{COLORS['gradient_start']},{COLORS['gradient_end']});"
        f"padding:22px 28px;"
        f"border-radius:14px;"
        f"margin-bottom:22px;"
        f"border:1px solid {COLORS['border']};"
        f"color:{COLORS['text_primary']};"
        f"font-size:1.7rem;"
        f"font-weight:800;\""
        f">{title}{sub_html}</h1>",
        unsafe_allow_html=True,
    )


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
        f"<p style='color:{COLORS['text_secondary']};font-size:0.75rem;"
        f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
        f"margin-bottom:8px;'>🔍 Search</p>",
        unsafe_allow_html=True,
    )
    selected["search"] = st.sidebar.text_input(
        "", placeholder="Asset ID, Name, Custodian…", label_visibility="collapsed"
    )

    st.sidebar.markdown(
        f"<p style='color:{COLORS['text_secondary']};font-size:0.75rem;"
        f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
        f"margin:12px 0 8px 0;'>📅 Install Date</p>",
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
                    f"<p style='color:{COLORS['text_secondary']};font-size:0.75rem;"
                    f"font-weight:600;letter-spacing:0.08em;text-transform:uppercase;"
                    f"margin:10px 0 4px 0;'>{label}</p>",
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

    # Drop internal helper columns and the Percentage column
    internal = [c for c in display_df.columns if str(c).startswith("_")]
    if "Percentage" in display_df.columns:
        internal.append("Percentage")
        
    if hide_cols:
        internal += hide_cols
    display_df.drop(columns=[c for c in internal if c in display_df.columns], inplace=True)

    # Format datetime cols
    for col in display_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        display_df[col] = display_df[col].dt.strftime("%d %b %Y")

    # Calculate and append TOTAL row
    numeric_cols = display_df.select_dtypes(include=["number"]).columns
    # Only add total row if there are numeric columns to sum, and there is more than 1 row
    if len(numeric_cols) > 0 and len(display_df) > 1:
        total_row = {col: None for col in display_df.columns}
        
        # Label the first column as TOTAL
        first_col = display_df.columns[0]
        total_row[first_col] = "TOTAL"
        
        # Sum numeric columns
        for col in numeric_cols:
            total_row[col] = display_df[col].sum()
            
        display_df = pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)
        record_count = len(display_df) - 1
    else:
        record_count = len(display_df)

    section_header(title, f"{record_count:,} records")
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
