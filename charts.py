# =============================================================================
# charts.py - Plotly Visualisation Library
# =============================================================================
"""
Every function returns a ``plotly.graph_objects.Figure`` ready to be rendered
with ``st.plotly_chart``.

Design principles:
  - All charts use the global PLOTLY_LAYOUT_DEFAULTS from config.py
  - Dark-mode aware
  - Branded Tata Steel palette
  - Tooltips / hover templates are polished
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config import COLORS, CHART_COLORS, PLOTLY_LAYOUT_DEFAULTS, PLOTLY_TEMPLATE, COLUMNS

logger = logging.getLogger("charts")


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _apply_defaults(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply global layout defaults and title to *fig*."""
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title     = dict(text=title, font=dict(size=16, color=COLORS["text_primary"]), x=0.01),
        height    = height,
        template  = PLOTLY_TEMPLATE,
    )
    return fig


def _no_data_fig(message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text     = f"<b>{message}</b>",
        xref     = "paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font     = dict(size=16, color=COLORS["text_secondary"]),
    )
    return _apply_defaults(fig)


# ===========================================================================
# 1. BAR CHARTS
# ===========================================================================

def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str = None,
    orientation: str = "v",
    height: int = 420,
    top_n: int = None,
) -> go.Figure:
    """Generic vertical or horizontal bar chart."""
    if df.empty:
        return _no_data_fig()

    data = df.copy()
    if top_n:
        # Always sort by the numeric value column (y), never by the text label column (x)
        try:
            data = data.nlargest(top_n, y)
        except Exception:
            data = data.head(top_n)

    if orientation == "h":
        # Horizontal: flip so biggest is on top
        data = data.sort_values(y, ascending=True)

    bar_color = color or COLORS["accent"]
    n = len(data)
    colors_list = CHART_COLORS * (n // len(CHART_COLORS) + 1)

    if orientation == "v":
        fig = go.Figure(go.Bar(
            x          = data[x],
            y          = data[y],
            marker     = dict(
                color  = colors_list[:n],
                line   = dict(color=COLORS["border"], width=0.5),
            ),
            hovertemplate = f"<b>%{{x}}</b><br>{y}: %{{y:,}}<extra></extra>",
        ))
    else:
        fig = go.Figure(go.Bar(
            y          = data[x],
            x          = data[y],
            orientation= "h",
            marker     = dict(
                color  = colors_list[:n],
                line   = dict(color=COLORS["border"], width=0.5),
            ),
            hovertemplate = f"<b>%{{y}}</b><br>{y}: %{{x:,}}<extra></extra>",
        ))

    return _apply_defaults(fig, title, height)


def grouped_bar(df: pd.DataFrame, title: str = "", height: int = 440) -> go.Figure:
    """Grouped bar from a pivot (index = categories, columns = groups)."""
    if df.empty:
        return _no_data_fig()

    fig = go.Figure()
    for i, col in enumerate(df.columns):
        fig.add_trace(go.Bar(
            name  = str(col),
            x     = df.index.astype(str),
            y     = df[col],
            marker_color = CHART_COLORS[i % len(CHART_COLORS)],
            hovertemplate = f"<b>%{{x}}</b><br>{col}: %{{y:,}}<extra></extra>",
        ))
    fig.update_layout(barmode="group")
    return _apply_defaults(fig, title, height)


def stacked_bar(df: pd.DataFrame, title: str = "", height: int = 440) -> go.Figure:
    """Stacked bar from a pivot table."""
    if df.empty:
        return _no_data_fig()

    fig = go.Figure()
    for i, col in enumerate(df.columns):
        fig.add_trace(go.Bar(
            name  = str(col),
            x     = df.index.astype(str),
            y     = df[col],
            marker_color = CHART_COLORS[i % len(CHART_COLORS)],
        ))
    fig.update_layout(barmode="stack")
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 2. LINE / AREA CHARTS
# ===========================================================================

def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list,
    title: str = "",
    height: int = 400,
    fill: bool = False,
) -> go.Figure:
    """Line chart; set fill=True for area chart."""
    if df.empty:
        return _no_data_fig()

    ys = [y] if isinstance(y, str) else y
    fig = go.Figure()
    for i, col in enumerate(ys):
        fig.add_trace(go.Scatter(
            x    = df[x],
            y    = df[col],
            name = col,
            mode = "lines+markers",
            fill = "tozeroy" if (fill and i == 0) else "none",
            line = dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2.5),
            marker= dict(size=5),
            hovertemplate = f"<b>{col}</b>: %{{y:,}}<extra></extra>",
        ))
    return _apply_defaults(fig, title, height)


def area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Filled area chart."""
    return line_chart(df, x, y, title, height, fill=True)


# ===========================================================================
# 3. PIE / DONUT CHARTS
# ===========================================================================

def donut_chart(
    df: pd.DataFrame,
    labels: str,
    values: str,
    title: str = "",
    height: int = 420,
    hole: float = 0.55,
) -> go.Figure:
    """Donut / pie chart."""
    if df.empty:
        return _no_data_fig()

    fig = go.Figure(go.Pie(
        labels        = df[labels],
        values        = df[values],
        hole          = hole,
        marker        = dict(colors=CHART_COLORS, line=dict(color=COLORS["bg_dark"], width=2)),
        textinfo      = "label+percent",
        hovertemplate = "<b>%{label}</b><br>Count: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 4. HEATMAP
# ===========================================================================

def heatmap(
    pivot: pd.DataFrame,
    title: str = "",
    height: int = 480,
    colorscale: str = "Blues",
) -> go.Figure:
    """Heatmap from a pivot table (index × columns)."""
    if pivot.empty:
        return _no_data_fig()

    fig = go.Figure(go.Heatmap(
        z            = pivot.values,
        x            = pivot.columns.astype(str).tolist(),
        y            = pivot.index.astype(str).tolist(),
        colorscale   = colorscale,
        hoverongaps  = False,
        hovertemplate= "<b>%{y}</b> × <b>%{x}</b><br>Count: %{z}<extra></extra>",
        showscale    = True,
    ))
    fig.update_layout(
        xaxis = dict(tickangle=-30),
        yaxis = dict(autorange="reversed"),
    )
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 5. SCATTER / BUBBLE CHART
# ===========================================================================

def scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str = None,
    size: str = None,
    title: str = "",
    height: int = 440,
) -> go.Figure:
    """Interactive scatter plot."""
    if df.empty or x not in df.columns or y not in df.columns:
        return _no_data_fig()

    kwargs = dict(
        data_frame    = df,
        x             = x,
        y             = y,
        title         = title,
        color_discrete_sequence = CHART_COLORS,
        template      = PLOTLY_TEMPLATE,
        height        = height,
    )
    if color and color in df.columns:
        kwargs["color"] = color
    if size and size in df.columns:
        kwargs["size"] = size

    fig = px.scatter(**kwargs)
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    return fig


# ===========================================================================
# 6. TREEMAP
# ===========================================================================

def treemap(
    df: pd.DataFrame,
    path_cols: list,
    values_col: str,
    title: str = "",
    height: int = 500,
) -> go.Figure:
    """Hierarchical treemap."""
    if df.empty:
        return _no_data_fig()

    valid_paths = [c for c in path_cols if c in df.columns]
    if not valid_paths:
        return _no_data_fig()

    fig = px.treemap(
        df,
        path     = valid_paths,
        values   = values_col if values_col in df.columns else None,
        color_discrete_sequence = CHART_COLORS,
        template = PLOTLY_TEMPLATE,
        height   = height,
    )
    fig.update_traces(
        hovertemplate = "<b>%{label}</b><br>Count: %{value}<extra></extra>",
        textinfo      = "label+value",
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, title=title)
    return fig


# ===========================================================================
# 7. HISTOGRAM
# ===========================================================================

def histogram(
    df: pd.DataFrame,
    col: str,
    title: str = "",
    nbins: int = 20,
    height: int = 400,
) -> go.Figure:
    """Frequency distribution histogram."""
    if col not in df.columns or df[col].dropna().empty:
        return _no_data_fig()

    fig = go.Figure(go.Histogram(
        x             = df[col].dropna(),
        nbinsx        = nbins,
        marker        = dict(color=COLORS["accent"], line=dict(color=COLORS["border"], width=0.5)),
        hovertemplate = "Range: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(bargap=0.05)
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 8. CORRELATION MATRIX
# ===========================================================================

def correlation_heatmap(corr: pd.DataFrame, title: str = "", height: int = 420) -> go.Figure:
    """Styled correlation matrix."""
    if corr.empty:
        return _no_data_fig()

    fig = go.Figure(go.Heatmap(
        z            = corr.values,
        x            = corr.columns.tolist(),
        y            = corr.index.tolist(),
        colorscale   = "RdBu",
        zmid         = 0,
        zmin         = -1,
        zmax         = 1,
        text         = corr.round(2).values,
        texttemplate = "%{text}",
        hovertemplate= "<b>%{y}</b> × <b>%{x}</b><br>r = %{z:.3f}<extra></extra>",
    ))
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 9. FUNNEL / RANKING CHART
# ===========================================================================

def funnel_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    height: int = 420,
) -> go.Figure:
    """Funnel chart for ranking/priority view."""
    if df.empty:
        return _no_data_fig()

    data = df.sort_values(y, ascending=False)
    fig = go.Figure(go.Funnel(
        y             = data[x].astype(str),
        x             = data[y],
        textinfo      = "value+percent initial",
        marker        = dict(color=CHART_COLORS[:len(data)]),
        hovertemplate = "<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
    ))
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 10. GAUGE / INDICATOR CHARTS
# ===========================================================================

def gauge_chart(
    value: float,
    title: str = "",
    max_val: float = 100,
    suffix: str = "%",
    height: int = 260,
) -> go.Figure:
    """Semi-circular gauge for KPI display."""
    color = (
        COLORS["success"] if value >= 80 else
        COLORS["warning"] if value >= 60 else
        COLORS["danger"]
    )
    fig = go.Figure(go.Indicator(
        mode   = "gauge+number+delta",
        value  = value,
        title  = dict(text=title, font=dict(size=14, color=COLORS["text_primary"])),
        number = dict(suffix=suffix, font=dict(size=32, color=color)),
        gauge  = dict(
            axis      = dict(range=[0, max_val], tickcolor=COLORS["text_secondary"]),
            bar       = dict(color=color, thickness=0.25),
            bgcolor   = COLORS["bg_card2"],
            bordercolor = COLORS["border"],
            steps     = [
                dict(range=[0,         max_val*0.6], color=COLORS["bg_card2"]),
                dict(range=[max_val*0.6, max_val*0.8], color=COLORS["bg_card"]),
            ],
            threshold = dict(
                line  = dict(color=COLORS["accent"], width=3),
                value = max_val * 0.8,
            ),
        ),
    ))
    return _apply_defaults(fig, "", height)


# ===========================================================================
# 11. MULTI-KPI SUMMARY BAR (Sparkline-style)
# ===========================================================================

def multi_kpi_bar(labels: list, values: list, title: str = "", height: int = 300) -> go.Figure:
    """Horizontal bar chart used as a mini KPI summary."""
    if not labels or not values:
        return _no_data_fig()

    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    fig = go.Figure(go.Bar(
        x             = values,
        y             = [str(l) for l in labels],
        orientation   = "h",
        marker        = dict(color=colors),
        text          = values,
        textposition  = "outside",
        hovertemplate = "<b>%{y}</b>: %{x:,}<extra></extra>",
    ))
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 12. TIMELINE / GANTT-STYLE AGE PLOT
# ===========================================================================

def age_distribution_chart(age_df: pd.DataFrame, title: str = "", height: int = 400) -> go.Figure:
    """Bar chart of age bucket distribution."""
    if age_df.empty or "Age Bucket" not in age_df.columns:
        return _no_data_fig()

    order = ["<1 yr", "1-3 yrs", "3-5 yrs", "5-7 yrs", "7+ yrs"]
    counts = age_df["Age Bucket"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Age Bucket", "Count"]

    fig = go.Figure(go.Bar(
        x             = counts["Age Bucket"],
        y             = counts["Count"],
        marker        = dict(
            color = [COLORS["success"], COLORS["accent"], COLORS["accent2"],
                     COLORS["warning"], COLORS["danger"]],
            line  = dict(color=COLORS["border"], width=0.5),
        ),
        text          = counts["Count"],
        textposition  = "outside",
        hovertemplate = "<b>Age: %{x}</b><br>Assets: %{y:,}<extra></extra>",
    ))
    return _apply_defaults(fig, title, height)


# ===========================================================================
# 13. SUNBURST CHART
# ===========================================================================

def sunburst_chart(
    df: pd.DataFrame,
    path_cols: list,
    title: str = "",
    height: int = 500,
) -> go.Figure:
    """Sunburst for hierarchical drill-down."""
    if df.empty:
        return _no_data_fig()
    valid = [c for c in path_cols if c in df.columns]
    if not valid:
        return _no_data_fig()

    # Count assets at leaf level
    count_df = df.groupby(valid).size().reset_index(name="Count")
    fig = px.sunburst(
        count_df,
        path     = valid,
        values   = "Count",
        color_discrete_sequence = CHART_COLORS,
        template = PLOTLY_TEMPLATE,
        height   = height,
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, title=title)
    return fig


# ===========================================================================
# 14. MOVING AVERAGE + TREND LINE
# ===========================================================================

def trend_with_ma(
    df: pd.DataFrame,
    x: str,
    y: str,
    ma_col: str = None,
    title: str = "",
    height: int = 420,
) -> go.Figure:
    """Line chart with optional moving average overlay."""
    if df.empty:
        return _no_data_fig()

    fig = go.Figure()

    # Raw line
    fig.add_trace(go.Scatter(
        x    = df[x],
        y    = df[y],
        name = y,
        mode = "lines+markers",
        line = dict(color=COLORS["accent"], width=2),
        fill = "tozeroy",
        fillcolor = "rgba(0,180,216,0.08)",
    ))

    # Moving average
    if ma_col and ma_col in df.columns:
        fig.add_trace(go.Scatter(
            x    = df[x],
            y    = df[ma_col],
            name = ma_col,
            mode = "lines",
            line = dict(color=COLORS["accent2"], width=2.5, dash="dot"),
        ))

    # Simple linear trend
    try:
        numeric_x = pd.to_numeric(pd.factorize(df[x])[0])
        z = np.polyfit(numeric_x, df[y].fillna(0), 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x    = df[x],
            y    = p(numeric_x),
            name = "Trend",
            mode = "lines",
            line = dict(color=COLORS["secondary"], width=1.5, dash="dash"),
        ))
    except Exception:
        pass

    return _apply_defaults(fig, title, height)
