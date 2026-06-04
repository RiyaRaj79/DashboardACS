# =============================================================================
# app.py - Main Streamlit Application Entry Point
# =============================================================================
"""
Tata Steel IT Asset Management Dashboard
=========================================
Run with:
    streamlit run app.py

Pages:
  1. Executive Summary
  2. Asset Analytics
  3. Location Analytics
  4. Department Analytics
  5. Custodian Analytics
  6. Hardware Status
  7. Installation Trends
  8. Advanced Analytics
  9. AI Insights
  10. Export
"""

import os
import logging
import numpy as np
import pandas as pd
import streamlit as st

# ── Local modules ────────────────────────────────────────────────────────────
from config import (
    APP_TITLE, APP_ICON, COLORS, COLUMNS, PAGES,
    DEFAULT_EXCEL_PATH, CACHE_TTL
)
import database  as db
import analytics as an
import charts    as ch
import utils     as ut

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("app")


# ===========================================================================
# PAGE CONFIG  (must be first Streamlit call)
# ===========================================================================
st.set_page_config(
    page_title     = APP_TITLE,
    page_icon      = APP_ICON,
    layout         = "wide",
    initial_sidebar_state = "expanded",
    menu_items     = {
        "About": f"**{APP_TITLE}** v1.0 | Built with Streamlit & Plotly",
    },
)


# ===========================================================================
# GLOBAL CSS INJECTION
# ===========================================================================

def _inject_css():
    st.markdown(f"""
    <style>
    /* ─── Google Fonts ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ─── Root / Body ──────────────────────────────────────────────────── */
    html, body, [class*="css"] {{
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }}
    .stApp {{
        background: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
    }}

    /* ─── Sidebar ───────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, {COLORS['bg_sidebar']} 0%, #0D1420 100%);
        border-right: 1px solid {COLORS['border']};
    }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.84rem;
    }}

    /* ─── Metric Cards (native st.metric) ───────────────────────────────── */
    div[data-testid="metric-container"] {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 14px 18px;
    }}
    div[data-testid="metric-container"] label {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.78rem !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
        color: {COLORS['text_primary']} !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}

    /* ─── Tabs ───────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background: {COLORS['bg_card']};
        border-radius: 10px;
        border: 1px solid {COLORS['border']};
        padding: 4px;
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: {COLORS['text_secondary']};
        font-weight: 500;
        padding: 6px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['primary']} !important;
        color: {COLORS['text_primary']} !important;
        font-weight: 700 !important;
    }}

    /* ─── Dataframe ──────────────────────────────────────────────────────── */
    .stDataFrame {{
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ─── Buttons ────────────────────────────────────────────────────────── */
    .stDownloadButton > button, .stButton > button {{
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['info']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 8px 18px !important;
        transition: all 0.2s !important;
    }}
    .stDownloadButton > button:hover, .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(0,180,216,0.3) !important;
    }}

    /* ─── Selectbox / MultiSelect ────────────────────────────────────────── */
    .stMultiSelect > div, .stSelectbox > div {{
        background: {COLORS['bg_card2']} !important;
        border-color: {COLORS['border']} !important;
        border-radius: 8px !important;
    }}

    /* ─── Text Input ─────────────────────────────────────────────────────── */
    .stTextInput > div > div > input {{
        background: {COLORS['bg_card2']} !important;
        color: {COLORS['text_primary']} !important;
        border-color: {COLORS['border']} !important;
        border-radius: 8px !important;
    }}

    /* ─── Info / Warning boxes ───────────────────────────────────────────── */
    .stInfo  {{ background: rgba(46,134,193,0.15) !important; border-color: {COLORS['info']} !important; }}
    .stWarning {{ background: rgba(230,126,34,0.15) !important; border-color: {COLORS['warning']} !important; }}
    .stError   {{ background: rgba(231,76,60,0.15)  !important; border-color: {COLORS['danger']} !important; }}

    /* ─── Scrollbar ──────────────────────────────────────────────────────── */
    ::-webkit-scrollbar       {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {COLORS['bg_dark']}; }}
    ::-webkit-scrollbar-thumb {{ background: {COLORS['border']}; border-radius: 4px; }}

    /* ─── Hide Streamlit branding ────────────────────────────────────────── */
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* ─── Plotly chart container ─────────────────────────────────────────── */
    .js-plotly-plot .plotly {{
        border-radius: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)


# ===========================================================================
# SIDEBAR – Navigation + Data Upload + Filters
# ===========================================================================

def _render_sidebar() -> tuple[str, pd.DataFrame, dict]:
    """
    Renders the sidebar.  Returns (selected_page, dataframe, filters).
    """
    with st.sidebar:
        # Logo / Title
        st.markdown(f"""
        <div style="
            text-align:center; padding: 16px 0 20px;
            border-bottom: 1px solid {COLORS['border']}; margin-bottom:16px;
        ">
            <div style="font-size:2.2rem;">🏭</div>
            <div style="color:{COLORS['text_primary']};font-size:1rem;font-weight:800;
                        letter-spacing:0.02em;">Tata Steel</div>
            <div style="color:{COLORS['accent']};font-size:0.72rem;font-weight:600;
                        letter-spacing:0.12em;text-transform:uppercase;">IT Asset Dashboard</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Data Source ────────────────────────────────────────────────────
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.74rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;'>"
            f"📁 Data Source</p>",
            unsafe_allow_html=True,
        )
        source = st.radio(
            "", ["Upload File", "Use Demo Data"],
            index=1, horizontal=False, label_visibility="collapsed"
        )

        df = pd.DataFrame()

        if source == "Upload File":
            uploaded = st.file_uploader(
                "Drop your Excel or CSV file",
                type=["xlsx", "xls", "csv"],
                label_visibility="collapsed",
            )
            if uploaded:
                with st.spinner("Loading data…"):
                    df = db.load_from_bytes(uploaded.read(), uploaded.name)
                if not df.empty:
                    db.save_to_sqlite(df)
                    st.success(f"✅ Loaded {len(df):,} records")
                else:
                    st.error("⚠️ No data found in file.")
        else:
            with st.spinner("Generating demo data…"):
                df = db.generate_demo_data(204)
            st.info("ℹ️ Using synthetic demo data (204 assets)")

        ut.divider()

        # ── Navigation ─────────────────────────────────────────────────────
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.74rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>"
            f"🗺️ Navigation</p>",
            unsafe_allow_html=True,
        )
        page = st.radio("", PAGES, index=0, label_visibility="collapsed")

        ut.divider()

        # ── Filters ────────────────────────────────────────────────────────
        if not df.empty:
            st.markdown(
                f"<p style='color:{COLORS['text_secondary']};font-size:0.74rem;font-weight:600;"
                f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>"
                f"🎛️ Global Filters</p>",
                unsafe_allow_html=True,
            )
            filters = ut.build_sidebar_filters(df)
        else:
            filters = {}

        # Filtered record count badge
        if not df.empty:
            filtered_df = ut.apply_filters(df, filters)
            n_filtered  = len(filtered_df)
            total       = len(df)
            color = COLORS["success"] if n_filtered == total else COLORS["warning"]
            st.markdown(
                f"<div style='text-align:center;background:{COLORS['bg_card2']};"
                f"border:1px solid {color};border-radius:8px;padding:8px;margin-top:10px;'>"
                f"<span style='color:{color};font-weight:700;font-size:1rem;'>{n_filtered:,}</span>"
                f"<span style='color:{COLORS['text_secondary']};font-size:0.78rem;'> / {total:,} assets</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.68rem;text-align:center;'>"
            f"v1.0 · Tata Steel IT Division</p>",
            unsafe_allow_html=True,
        )

    return page, df, filters


# ===========================================================================
# PAGE 1 — EXECUTIVE SUMMARY
# ===========================================================================

def page_executive_summary(df: pd.DataFrame, kpis: dict):
    ut.page_header(
        "🏠 Executive Summary",
        "High-level overview of the complete IT asset fleet",
    )

    if df.empty:
        st.warning("No data loaded. Please upload a file or use demo data.")
        return

    # ── Row 1: KPI Cards ─────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    ut.kpi_card(c1, "📦", "Total Assets",    ut.fmt_number(kpis["total_assets"]),
                f"Across {kpis['n_locations']} locations")
    ut.kpi_card(c2, "✅", "Active Assets",   ut.fmt_number(kpis["active_count"]),
                f"{kpis['active_pct']:.1f}% of fleet",
                color=COLORS["success"])
    ut.kpi_card(c3, "🔧", "In Maintenance", ut.fmt_number(kpis["maint_count"]),
                "Awaiting resolution",
                color=COLORS["warning"])
    ut.kpi_card(c4, "🚫", "Retired / EOL",  ut.fmt_number(kpis["retired_count"]),
                "Decommissioned assets",
                color=COLORS["danger"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: More KPIs ─────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    ut.kpi_card(c5, "🔴", "Critical Assets",  ut.fmt_number(kpis["critical_count"]),
                "Require priority support",
                color=COLORS["secondary"])
    ut.kpi_card(c6, "🏢", "Departments",      ut.fmt_number(kpis["n_departments"]),
                "Active departments")
    ut.kpi_card(c7, "👤", "Custodians",       ut.fmt_number(kpis["n_custodians"]),
                "Unique asset owners")
    ut.kpi_card(c8, "📅", "This Year",        ut.fmt_number(kpis["assets_this_year"]),
                "New assets added",
                trend=kpis["yoy_growth"],
                color=COLORS["accent"])

    ut.divider()

    # ── Row 3: Charts ─────────────────────────────────────────────────────
    c_left, c_right = st.columns([1.2, 0.8])

    with c_left:
        ut.section_header("Hardware Status Distribution")
        hw_bd = an.breakdown_by(df, COLUMNS["hw_status"])
        if not hw_bd.empty:
            fig = ch.donut_chart(hw_bd, COLUMNS["hw_status"], "Count",
                                 "Assets by Hardware Status", height=380)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with c_right:
        ut.section_header("Asset Class Breakdown")
        cls_bd = an.breakdown_by(df, COLUMNS["asset_class"])
        if not cls_bd.empty:
            fig = ch.bar_chart(cls_bd, COLUMNS["asset_class"], "Count",
                               "Assets by Class", height=380)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.divider()

    # ── Row 4: Gauge + Top performers ─────────────────────────────────────
    c_gauge, c_top = st.columns([0.5, 1.5])
    with c_gauge:
        ut.section_header("Active Asset Rate")
        fig = ch.gauge_chart(kpis["active_pct"], "Active Rate", height=270)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.8rem;"
            f"text-align:center;'>📍 Top Location: <b style='color:{COLORS['text_primary']}'>"
            f"{kpis['top_location']}</b></p>",
            unsafe_allow_html=True,
        )

    with c_top:
        ut.section_header("Top Metrics at a Glance")
        labels = ["Top CI Type", "Top Manufacturer", "Top Department", "Top Class", "Top Location"]
        vals   = [
            kpis.get("top_ci_type", "N/A"),
            kpis.get("top_manufacturer", "N/A"),
            kpis.get("top_department", "N/A"),
            kpis.get("top_class", "N/A"),
            kpis.get("top_location", "N/A"),
        ]
        for label, val in zip(labels, vals):
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:8px 12px;background:{COLORS['bg_card2']};"
                f"border-radius:8px;margin-bottom:6px;border:1px solid {COLORS['border']};'>"
                f"<span style='color:{COLORS['text_secondary']};font-size:0.85rem;'>{label}</span>"
                f"<span style='color:{COLORS['accent']};font-weight:700;font-size:0.9rem;'>{val}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    ut.divider()

    # ── Row 5: Installation date info + yearly trend ─────────────────────
    ut.section_header("Installation Overview")
    c_info, c_trend = st.columns([0.4, 1.6])
    with c_info:
        if kpis.get("install_start"):
            st.markdown(f"""
            <div style='background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
                        border-radius:10px;padding:14px 16px;'>
                <div style='color:{COLORS['text_secondary']};font-size:0.78rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;'>📅 Date Range</div>
                <div style='color:{COLORS['text_primary']};font-size:0.9rem;margin-bottom:6px;'>
                    <b>First Install:</b><br>{ut.fmt_date(kpis['install_start'])}</div>
                <div style='color:{COLORS['text_primary']};font-size:0.9rem;'>
                    <b>Latest Install:</b><br>{ut.fmt_date(kpis['install_end'])}</div>
            </div>
            """, unsafe_allow_html=True)

    with c_trend:
        yearly = an.yearly_installation_trend(df)
        if not yearly.empty:
            fig = ch.trend_with_ma(yearly, "Year", "Assets Installed", None,
                                   "Yearly Asset Procurement Trend", height=260)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())


# ===========================================================================
# PAGE 2 — ASSET ANALYTICS
# ===========================================================================

def page_asset_analytics(df: pd.DataFrame):
    ut.page_header("📦 Asset Analytics", "Deep-dive into asset types, classes, and manufacturers")

    tab1, tab2, tab3, tab4 = st.tabs(["By CI Type", "By Class", "By Manufacturer", "Treemap"])

    with tab1:
        ci_bd = an.breakdown_by(df, COLUMNS["ci_type"])
        c1, c2 = st.columns(2)
        with c1:
            fig = ch.bar_chart(ci_bd, COLUMNS["ci_type"], "Count",
                               "Assets by CI Type", orientation="h", height=440)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        with c2:
            fig = ch.donut_chart(ci_bd, COLUMNS["ci_type"], "Count",
                                 "CI Type Distribution", height=440)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        ut.render_data_table(ci_bd, "CI Type Breakdown Table")

    with tab2:
        cls_bd = an.breakdown_by(df, COLUMNS["asset_class"])
        c1, c2 = st.columns(2)
        with c1:
            fig = ch.bar_chart(cls_bd, COLUMNS["asset_class"], "Count",
                               "Assets by Class", height=380)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        with c2:
            fig = ch.donut_chart(cls_bd, COLUMNS["asset_class"], "Count",
                                 "Class Distribution", height=380)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab3:
        mfr_bd = an.breakdown_by(df, COLUMNS["manufacturer"])
        c1, c2 = st.columns(2)
        with c1:
            fig = ch.bar_chart(mfr_bd, COLUMNS["manufacturer"], "Count",
                               "Top Manufacturers", orientation="h", height=440)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        with c2:
            crit_bd = an.breakdown_by(df, COLUMNS["asset_criteria"])
            fig = ch.donut_chart(crit_bd, COLUMNS["asset_criteria"], "Count",
                                 "Asset Criticality Distribution", height=440)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab4:
        ut.section_header("Asset Hierarchy Treemap")
        path_cols = [COLUMNS["asset_class"], COLUMNS["ci_type"]]
        count_df  = df.assign(Count=1)
        fig = ch.treemap(
            count_df, path_cols, "Count",
            "Class → CI Type Hierarchy", height=550
        )
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())


# ===========================================================================
# PAGE 3 — LOCATION ANALYTICS
# ===========================================================================

def page_location_analytics(df: pd.DataFrame):
    ut.page_header("📍 Location Analytics", "Geographic distribution of IT assets across sites")

    # KPI row
    loc_bd = an.breakdown_by(df, COLUMNS["location"])
    c1, c2, c3 = st.columns(3)
    ut.kpi_card(c1, "📍", "Unique Locations", ut.fmt_number(df[COLUMNS["location"]].nunique() if COLUMNS["location"] in df.columns else 0), "")
    top_loc = loc_bd.iloc[0] if not loc_bd.empty else None
    ut.kpi_card(c2, "🥇", "Top Location", str(top_loc[COLUMNS["location"]]) if top_loc is not None else "N/A",
                f"{top_loc['Count']} assets" if top_loc is not None else "")
    ut.kpi_card(c3, "🌐", "Unique Regions", ut.fmt_number(df[COLUMNS["region"]].nunique() if COLUMNS["region"] in df.columns else 0), "")

    ut.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Location Bar", "Region Donut", "Heatmap", "Sunburst"])

    with tab1:
        fig = ch.bar_chart(loc_bd, COLUMNS["location"], "Count",
                           "Assets by Location", orientation="h", height=460)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        ut.render_data_table(loc_bd, "Location Breakdown")

    with tab2:
        reg_bd = an.breakdown_by(df, COLUMNS["region"])
        c1, c2 = st.columns(2)
        with c1:
            fig = ch.donut_chart(reg_bd, COLUMNS["region"], "Count",
                                 "Assets by Region", height=420)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        with c2:
            sub_bd = an.breakdown_by(df, COLUMNS["sublocation"])
            fig = ch.bar_chart(sub_bd, COLUMNS["sublocation"], "Count",
                               "Assets by Sublocation", orientation="h", height=420, top_n=15)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab3:
        ut.section_header("Location × CI Type Heatmap")
        heat_data = an.location_heatmap_data(df)
        if not heat_data.empty:
            fig = ch.heatmap(heat_data, "Location × CI Type Asset Distribution", height=500)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        else:
            st.info("Insufficient data for heatmap.")

    with tab4:
        ut.section_header("Regional Hierarchy – Sunburst Drill-Down")
        path_cols = [COLUMNS["region"], COLUMNS["location"], COLUMNS["sublocation"]]
        fig = ch.sunburst_chart(df, path_cols, "Region → Location → Sublocation", height=560)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())


# ===========================================================================
# PAGE 4 — DEPARTMENT ANALYTICS
# ===========================================================================

def page_department_analytics(df: pd.DataFrame):
    ut.page_header("🏢 Department Analytics", "Asset distribution across business units")

    dept_bd = an.breakdown_by(df, COLUMNS["department"])

    c1, c2 = st.columns(2)
    with c1:
        fig = ch.bar_chart(dept_bd, COLUMNS["department"], "Count",
                           "Assets per Department", orientation="h", height=460)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
    with c2:
        fig = ch.donut_chart(dept_bd, COLUMNS["department"], "Count",
                             "Department Share", height=460)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.divider()
    ut.section_header("Department × Hardware Status (Stacked)", "Which departments have high maintenance / retired assets?")

    dept_status = an.department_status_pivot(df)
    if not dept_status.empty:
        fig = ch.stacked_bar(dept_status, "Department × Hardware Status Breakdown", height=440)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.divider()
    ut.section_header("Department × CI Type Heatmap")
    if COLUMNS["department"] in df.columns and COLUMNS["ci_type"] in df.columns:
        pivot = an.multi_breakdown(df, COLUMNS["department"], COLUMNS["ci_type"])
        if not pivot.empty:
            fig = ch.heatmap(pivot, "Department × CI Type Asset Count", height=480)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.render_data_table(dept_bd, "Department Details Table")


# ===========================================================================
# PAGE 5 — CUSTODIAN ANALYTICS
# ===========================================================================

def page_custodian_analytics(df: pd.DataFrame):
    ut.page_header("👤 Custodian Analytics", "Asset ownership & workload distribution")

    cust_bd = an.custodian_load(df)
    if cust_bd.empty:
        st.info("Custodian column not found.")
        return

    cust_col = COLUMNS["custodian"]
    avg_load  = cust_bd["Count"].mean()
    max_load  = cust_bd["Count"].max()
    overloaded= (cust_bd["Count"] > avg_load * 2).sum()

    c1, c2, c3 = st.columns(3)
    ut.kpi_card(c1, "👤", "Total Custodians", ut.fmt_number(len(cust_bd)), "Unique asset owners")
    ut.kpi_card(c2, "⚖️", "Avg Assets / Custodian", f"{avg_load:.1f}", "Workload average")
    ut.kpi_card(c3, "⚠️", "Overloaded Custodians", ut.fmt_number(overloaded),
                "Managing 2× avg assets", color=COLORS["warning"])

    ut.divider()

    tab1, tab2 = st.tabs(["Top 20 Custodians", "Workload Histogram"])

    with tab1:
        top20 = cust_bd.head(20)
        fig = ch.bar_chart(top20, cust_col, "Count",
                           "Top 20 Custodians by Asset Count", orientation="h", height=500)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab2:
        ut.section_header("Custodian Workload Distribution (Histogram)")
        fig = ch.histogram(cust_bd, "Count",
                           "Distribution of Assets per Custodian", nbins=15, height=420)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.render_data_table(cust_bd.head(50), "Custodian Workload Table (Top 50)")


# ===========================================================================
# PAGE 6 — HARDWARE STATUS
# ===========================================================================

def page_hardware_status(df: pd.DataFrame):
    ut.page_header("🔧 Hardware Status Analytics", "Operational state of the IT asset fleet")

    hw_col = COLUMNS["hw_status"]
    hw_bd  = an.breakdown_by(df, hw_col)

    # KPI row
    cols = st.columns(len(hw_bd))
    status_icons = {
        "active"          : ("✅", COLORS["success"]),
        "in maintenance"  : ("🔧", COLORS["warning"]),
        "retired"         : ("❌", COLORS["danger"]),
        "decommissioned"  : ("🗑️", COLORS["secondary"]),
        "spare"           : ("📦", COLORS["info"]),
    }
    for i, (_, row) in enumerate(hw_bd.iterrows()):
        status  = str(row[hw_col]).lower()
        icon, c = status_icons.get(status, ("📋", COLORS["accent"]))
        ut.kpi_card(cols[i % len(cols)], icon, str(row[hw_col]),
                    ut.fmt_number(row["Count"]),
                    ut.fmt_pct(row["Percentage"]),
                    color=c)

    ut.divider()

    c1, c2 = st.columns(2)
    with c1:
        fig = ch.donut_chart(hw_bd, hw_col, "Count",
                             "Hardware Status Distribution", height=400)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
    with c2:
        fig = ch.bar_chart(hw_bd, hw_col, "Count",
                           "Status Count Comparison", height=400)
        st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.divider()
    ut.section_header("Status by Location – Stacked Bar")

    if COLUMNS["location"] in df.columns:
        pivot = an.multi_breakdown(df, COLUMNS["location"], hw_col)
        if not pivot.empty:
            fig = ch.stacked_bar(pivot, "Hardware Status by Location", height=440)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    ut.render_data_table(hw_bd, "Hardware Status Summary")


# ===========================================================================
# PAGE 7 — INSTALLATION TRENDS
# ===========================================================================

def page_installation_trends(df: pd.DataFrame):
    ut.page_header("📅 Installation Trends", "Historical analysis of asset procurement over time")

    io_col = COLUMNS["installed_on"]
    if io_col not in df.columns:
        st.warning("'Installed On' column not found in the dataset.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["Monthly", "Yearly", "Quarterly", "Asset Age"])

    with tab1:
        monthly = an.monthly_installation_trend(df)
        if not monthly.empty:
            fig = ch.trend_with_ma(
                monthly, "Year-Month", "Assets Installed", "Moving Avg (3M)",
                "Monthly Asset Installation Trend with 3-Month Moving Average", height=440,
            )
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
            mom = an.growth_rate_by_period(df)
            if not mom.empty:
                fig2 = ch.bar_chart(mom.dropna(subset=["MoM Growth %"]),
                                    "Year-Month", "MoM Growth %",
                                    "Month-over-Month Growth Rate (%)", height=280)
                st.plotly_chart(fig2, use_container_width=True, config=ut.chart_config())
        ut.render_data_table(monthly, "Monthly Installation Data")

    with tab2:
        yearly = an.yearly_installation_trend(df)
        if not yearly.empty:
            fig = ch.line_chart(yearly, "Year", ["Assets Installed"],
                                "Yearly Installation Trend", height=400)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
            fig2 = ch.bar_chart(
                yearly.dropna(subset=["YoY Growth %"]),
                "Year", "YoY Growth %",
                "Year-over-Year Growth Rate (%)", height=280,
            )
            st.plotly_chart(fig2, use_container_width=True, config=ut.chart_config())

    with tab3:
        quarterly = an.quarterly_trend(df)
        if not quarterly.empty:
            fig = ch.area_chart(quarterly, "Quarter", "Assets Installed",
                                "Quarterly Cumulative Installation", height=400)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab4:
        ut.section_header("Asset Age Distribution")
        age_df = an.assets_by_age(df)
        if not age_df.empty:
            fig = ch.age_distribution_chart(age_df, "Assets by Age Bucket", height=400)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
            fig2 = ch.histogram(age_df, "Age (Years)",
                                "Age Distribution (Years)", nbins=20, height=350)
            st.plotly_chart(fig2, use_container_width=True, config=ut.chart_config())
            ut.render_data_table(age_df, "Asset Age Details")


# ===========================================================================
# PAGE 8 — ADVANCED ANALYTICS
# ===========================================================================

def page_advanced_analytics(df: pd.DataFrame):
    ut.page_header("🔬 Advanced Analytics", "Statistical analysis, rankings, and anomaly detection")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Top / Bottom N", "Outlier Detection", "Correlation", "Multi-Dimension"
    ])

    with tab1:
        ut.section_header("Top & Bottom N Analysis")
        n_select = st.slider("Select N", 5, 30, 10, key="n_select")
        col_select = st.selectbox(
            "Analyse column",
            [COLUMNS["location"], COLUMNS["department"], COLUMNS["manufacturer"],
             COLUMNS["ci_type"], COLUMNS["custodian"], COLUMNS["team"]],
            key="topn_col",
        )
        c1, c2 = st.columns(2)
        with c1:
            ut.section_header(f"Top {n_select}")
            top_df = an.top_n_by(df, col_select, n_select)
            fig = ch.bar_chart(top_df, col_select, "Count",
                               f"Top {n_select} by {col_select}",
                               orientation="h", height=450)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        with c2:
            ut.section_header(f"Bottom {n_select}")
            bot_df = an.bottom_n_by(df, col_select, n_select)
            fig = ch.bar_chart(bot_df, col_select, "Count",
                               f"Bottom {n_select} by {col_select}",
                               orientation="h", height=450)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab2:
        ut.section_header("Outlier Detection – Custodian Workload")
        cust_bd = an.custodian_load(df)
        if not cust_bd.empty:
            threshold = st.slider("Z-score threshold", 1.5, 4.0, 2.5, 0.1, key="z_thresh")
            outliers  = an.detect_outliers_zscore(cust_bd, "Count", threshold)
            if not outliers.empty:
                st.warning(f"⚠️ {len(outliers)} outlier custodian(s) detected (|z| > {threshold})")
                fig = ch.scatter_chart(
                    cust_bd.reset_index(drop=True).assign(index=range(len(cust_bd))),
                    x="index", y="Count",
                    title="Custodian Asset Count (Outliers = High Values)",
                    height=420,
                )
                st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
                ut.render_data_table(outliers, "Detected Outliers")
            else:
                st.success("✅ No outliers found at this threshold.")

    with tab3:
        ut.section_header("Correlation Matrix")
        st.info("Correlation is computed on numerical columns derived from the dataset.")
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] >= 2:
            corr = an.correlation_matrix(df)
            if not corr.empty:
                fig = ch.correlation_heatmap(corr, "Numerical Feature Correlation", height=420)
                st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())
        else:
            # Encode key categoricals and compute correlation
            encode_cols = [COLUMNS["location"], COLUMNS["department"],
                           COLUMNS["ci_type"], COLUMNS["hw_status"]]
            enc_df = df[[c for c in encode_cols if c in df.columns]].copy()
            for c in enc_df.columns:
                enc_df[c], _ = pd.factorize(enc_df[c])
            if "_install_year" in df.columns:
                enc_df["Install Year"] = df["_install_year"]
            corr = enc_df.corr().round(3)
            fig = ch.correlation_heatmap(corr, "Encoded Column Correlation Matrix", height=420)
            st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())

    with tab4:
        ut.section_header("Multi-Dimensional Analysis")
        c1, c2 = st.columns([1, 2])
        with c1:
            grp1 = st.selectbox("Group By (Rows)",
                [COLUMNS["location"], COLUMNS["department"], COLUMNS["region"]], key="md1")
            grp2 = st.selectbox("Group By (Columns)",
                [COLUMNS["hw_status"], COLUMNS["ci_type"], COLUMNS["asset_class"]], key="md2")
        with c2:
            pivot = an.multi_breakdown(df, grp1, grp2)
            if not pivot.empty:
                fig = ch.heatmap(pivot, f"{grp1} × {grp2} Asset Heatmap", height=480)
                st.plotly_chart(fig, use_container_width=True, config=ut.chart_config())


# ===========================================================================
# PAGE 9 — AI INSIGHTS
# ===========================================================================

def page_ai_insights(df: pd.DataFrame, kpis: dict, insights: list):
    ut.page_header("🤖 AI Insights", "Automated intelligence & recommendations for asset management")

    if not insights:
        st.info("No insights generated – load data first.")
        return

    # Categorise insights
    by_type = {"success": [], "warning": [], "danger": [], "info": []}
    for ins in insights:
        by_type.setdefault(ins.get("type", "info"), []).append(ins)

    # Summary badges
    c1, c2, c3, c4 = st.columns(4)
    ut.kpi_card(c1, "✅", "Positive Findings", str(len(by_type["success"])), "", color=COLORS["success"])
    ut.kpi_card(c2, "⚠️", "Warnings",          str(len(by_type["warning"])), "", color=COLORS["warning"])
    ut.kpi_card(c3, "🚨", "Critical Alerts",   str(len(by_type["danger"])),  "", color=COLORS["danger"])
    ut.kpi_card(c4, "💡", "Informational",     str(len(by_type["info"])),    "", color=COLORS["info"])

    ut.divider()

    # Display by priority
    for t in ["danger", "warning", "success", "info"]:
        for ins in by_type[t]:
            ut.insight_card(st, ins)

    ut.divider()
    ut.section_header("📋 Summary Report")
    st.markdown(f"""
    <div style='background:{COLORS['bg_card2']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:20px 24px;'>
        <div style='color:{COLORS['text_primary']};font-size:0.95rem;line-height:1.8;'>
            <b style='color:{COLORS['accent']};'>Fleet Overview:</b>
            The IT asset fleet comprises <b>{kpis.get('total_assets',0):,}</b> assets across
            <b>{kpis.get('n_locations',0)}</b> locations with
            <b>{kpis.get('n_departments',0)}</b> departments involved.
            <br><br>
            <b style='color:{COLORS['accent']};'>Operational Health:</b>
            <b>{kpis.get('active_pct',0):.1f}%</b> of assets are active.
            <b>{kpis.get('maint_count',0)}</b> are in maintenance and
            <b>{kpis.get('retired_count',0)}</b> have been retired or decommissioned.
            <br><br>
            <b style='color:{COLORS['accent']};'>Growth Trajectory:</b>
            YoY asset addition change stands at
            <b>{kpis.get('yoy_growth',0):+.1f}%</b>.
            <b>{kpis.get('assets_this_year',0)}</b> new assets were added in the current year.
            <br><br>
            <b style='color:{COLORS['accent']};'>Recommended Actions:</b><br>
            1. Review and reassign assets from overloaded custodians.<br>
            2. Prioritise refresh for assets older than 7 years.<br>
            3. Establish redundancy plans for the top concentration location.<br>
            4. Investigate maintenance queue SLA compliance.<br>
            5. Expand asset coverage in under-served departments.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ===========================================================================
# PAGE 10 — EXPORT
# ===========================================================================

def page_export(df: pd.DataFrame, filtered_df: pd.DataFrame):
    ut.page_header("📤 Data Export", "Download filtered data and reports")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style='background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
                    border-radius:12px;padding:20px 24px;margin-bottom:14px;'>
            <h4 style='color:{COLORS['accent']};margin-top:0;'>📊 Filtered Dataset</h4>
            <p style='color:{COLORS['text_secondary']};font-size:0.87rem;'>
                Export the currently filtered view ({len(filtered_df):,} records).
            </p>
        </div>
        """, unsafe_allow_html=True)
        ut.render_export_buttons(filtered_df, "filtered_assets")

    with c2:
        st.markdown(f"""
        <div style='background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
                    border-radius:12px;padding:20px 24px;margin-bottom:14px;'>
            <h4 style='color:{COLORS['accent']};margin-top:0;'>🗂️ Full Dataset</h4>
            <p style='color:{COLORS['text_secondary']};font-size:0.87rem;'>
                Export the complete unfiltered dataset ({len(df):,} records).
            </p>
        </div>
        """, unsafe_allow_html=True)
        ut.render_export_buttons(df, "full_assets")

    ut.divider()

    # Breakdown exports
    ut.section_header("📋 Summary Reports")
    reports = {
        "Hardware Status Summary"  : an.breakdown_by(df, COLUMNS["hw_status"]),
        "Location Summary"         : an.breakdown_by(df, COLUMNS["location"]),
        "Department Summary"       : an.breakdown_by(df, COLUMNS["department"]),
        "CI Type Summary"          : an.breakdown_by(df, COLUMNS["ci_type"]),
        "Manufacturer Summary"     : an.breakdown_by(df, COLUMNS["manufacturer"]),
        "Monthly Trend"            : an.monthly_installation_trend(df),
        "Yearly Trend"             : an.yearly_installation_trend(df),
        "Asset Age Report"         : an.assets_by_age(df),
    }

    for name, rdf in reports.items():
        if rdf is not None and not rdf.empty:
            with st.expander(f"📄 {name}  ({len(rdf):,} rows)"):
                st.dataframe(rdf, use_container_width=True)
                ut.render_export_buttons(rdf, name.lower().replace(" ", "_"))

    ut.divider()
    ut.section_header("📦 Raw Data Preview")
    ut.render_data_table(filtered_df, f"Filtered Data – {len(filtered_df):,} records", height=500)


# ===========================================================================
# MAIN APPLICATION ENTRY POINT
# ===========================================================================

def main():
    _inject_css()

    page, raw_df, filters = _render_sidebar()

    # Apply global filters
    filtered_df = ut.apply_filters(raw_df, filters) if not raw_df.empty else raw_df

    # Pre-compute KPIs and insights (cached via analytics layer)
    kpis     = an.compute_kpis(filtered_df) if not filtered_df.empty else {}
    insights = an.generate_insights(filtered_df, kpis) if not filtered_df.empty else []

    # ── Route to selected page ────────────────────────────────────────────
    if page == PAGES[0]:
        page_executive_summary(filtered_df, kpis)
    elif page == PAGES[1]:
        page_asset_analytics(filtered_df)
    elif page == PAGES[2]:
        page_location_analytics(filtered_df)
    elif page == PAGES[3]:
        page_department_analytics(filtered_df)
    elif page == PAGES[4]:
        page_custodian_analytics(filtered_df)
    elif page == PAGES[5]:
        page_hardware_status(filtered_df)
    elif page == PAGES[6]:
        page_installation_trends(filtered_df)
    elif page == PAGES[7]:
        page_advanced_analytics(filtered_df)
    elif page == PAGES[8]:
        page_ai_insights(filtered_df, kpis, insights)
    elif page == PAGES[9]:
        page_export(raw_df, filtered_df)


if __name__ == "__main__":
    main()
