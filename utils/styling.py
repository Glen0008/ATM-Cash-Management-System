"""
Styling and Design System for ATM Cash Management DSS.
Enterprise banking visual identity: clean, polished, authoritative.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Enterprise Palette
COLOR_PRIMARY_NAVY = "#0F172A"      # Slate 900
COLOR_SECONDARY_NAVY = "#1E293B"    # Slate 800
COLOR_ACCENT_BLUE = "#2563EB"       # Blue 600
COLOR_LIGHT_BG = "#F8FAFC"          # Slate 50
COLOR_CARD_BORDER = "#E2E8F0"       # Slate 200
COLOR_TEXT_MUTED = "#64748B"        # Slate 500

# Semantic Risk Palette
COLOR_URGENT = "#DC2626"    # Red 600
COLOR_HIGH = "#EA580C"      # Orange 600
COLOR_MODERATE = "#D97706"  # Amber 600
COLOR_LOW = "#059669"       # Emerald 600

RISK_COLORS = {
    "Urgent": COLOR_URGENT,
    "High": COLOR_HIGH,
    "Moderate": COLOR_MODERATE,
    "Low": COLOR_LOW
}

def inject_custom_css():
    """Injects high-end banking stylesheet into Streamlit with full dark-mode support."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Design Tokens (Light Mode) ─────────────────────────────────── */
    :root {
        --dss-bg-card:        #FFFFFF;
        --dss-bg-inner:       #F8FAFC;
        --dss-border:         #E2E8F0;
        --dss-border-inner:   #F1F5F9;
        --dss-text-primary:   #0F172A;
        --dss-text-secondary: #334155;
        --dss-text-muted:     #64748B;
        --dss-shadow-sm:      rgba(0,0,0,0.05);
        --dss-shadow-md:      rgba(0,0,0,0.08);
    }

    /* ── Design Tokens (Dark Mode) ──────────────────────────────────── */
    /* Covers both OS dark mode AND Streamlit's built-in dark theme toggle */
    @media (prefers-color-scheme: dark) {
        :root {
            --dss-bg-card:        #1E293B;
            --dss-bg-inner:       #0F172A;
            --dss-border:         #334155;
            --dss-border-inner:   #1E293B;
            --dss-text-primary:   #F1F5F9;
            --dss-text-secondary: #CBD5E1;
            --dss-text-muted:     #94A3B8;
            --dss-shadow-sm:      rgba(0,0,0,0.25);
            --dss-shadow-md:      rgba(0,0,0,0.35);
        }
    }
    /* Streamlit injects data-theme="dark" on the root when dark mode is active */
    [data-theme="dark"] {
        --dss-bg-card:        #1E293B;
        --dss-bg-inner:       #0F172A;
        --dss-border:         #334155;
        --dss-border-inner:   #1E293B;
        --dss-text-primary:   #F1F5F9;
        --dss-text-secondary: #CBD5E1;
        --dss-text-muted:     #94A3B8;
        --dss-shadow-sm:      rgba(0,0,0,0.25);
        --dss-shadow-md:      rgba(0,0,0,0.35);
    }
    /* Badge dark overrides for Streamlit dark theme */
    [data-theme="dark"] .badge-urgent  { background-color: #450A0A; color: #FCA5A5; border-color: #7F1D1D; }
    [data-theme="dark"] .badge-high    { background-color: #431407; color: #FDBA74; border-color: #7C2D12; }
    [data-theme="dark"] .badge-moderate{ background-color: #451A03; color: #FCD34D; border-color: #78350F; }
    [data-theme="dark"] .badge-low     { background-color: #022C22; color: #6EE7B7; border-color: #065F46; }
    [data-theme="dark"] .mode-pill     { background: #1E3A8A;       color: #BFDBFE; border-color: #3B82F6; }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Top Banner / Header ────────────────────────────────────────── */
    .dss-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 22px 28px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.25);
    }
    .dss-header h1 {
        color: #FFFFFF !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    .dss-header p {
        color: #93C5FD !important;
        font-size: 0.95rem !important;
        margin: 6px 0 0 0 !important;
        font-weight: 400;
    }

    /* ── KPI Cards ──────────────────────────────────────────────────── */
    .kpi-container {
        display: flex;
        flex-direction: column;
        background: var(--dss-bg-card);
        border: 1px solid var(--dss-border);
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px var(--dss-shadow-sm);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 12px;
    }
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px var(--dss-shadow-md);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--dss-text-muted);
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: var(--dss-text-primary);
        line-height: 1.2;
    }
    .kpi-subtext {
        font-size: 0.78rem;
        color: var(--dss-text-muted);
        margin-top: 6px;
    }

    /* ── Status Badges ──────────────────────────────────────────────── */
    .badge-urgent {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
        border: 1px solid #FECACA;
    }
    @media (prefers-color-scheme: dark) {
        .badge-urgent { background-color: #450A0A; color: #FCA5A5; border-color: #7F1D1D; }
    }
    .badge-high {
        background-color: #FFEDD5;
        color: #9A3412;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
        border: 1px solid #FED7AA;
    }
    @media (prefers-color-scheme: dark) {
        .badge-high { background-color: #431407; color: #FDBA74; border-color: #7C2D12; }
    }
    .badge-moderate {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
        border: 1px solid #FDE68A;
    }
    @media (prefers-color-scheme: dark) {
        .badge-moderate { background-color: #451A03; color: #FCD34D; border-color: #78350F; }
    }
    .badge-low {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
        border: 1px solid #A7F3D0;
    }
    @media (prefers-color-scheme: dark) {
        .badge-low { background-color: #022C22; color: #6EE7B7; border-color: #065F46; }
    }

    /* ── Mode Pill Indicator ─────────────────────────────────────────── */
    .mode-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
        background: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
    }
    @media (prefers-color-scheme: dark) {
        .mode-pill { background: #1E3A8A; color: #BFDBFE; border-color: #3B82F6; }
    }

    /* ── Section Cards ───────────────────────────────────────────────── */
    .dss-card {
        background: var(--dss-bg-card);
        border: 1px solid var(--dss-border);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px var(--dss-shadow-sm);
    }
    .dss-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--dss-text-primary);
        margin-bottom: 14px;
        border-bottom: 1px solid var(--dss-border-inner);
        padding-bottom: 8px;
    }
    
    /* Clean tables */
    .dataframe {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str, badge: str = "Decision Support System"):
    """Renders a standard enterprise top banner."""
    st.markdown(f"""
    <div class="dss-header">
        <span class="mode-pill">{badge}</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_kpi(label: str, value: str, subtext: str = "", border_color: str = None):
    """Renders a styled KPI card."""
    border_style = f"border-left: 4px solid {border_color};" if border_color else ""
    st.markdown(f"""
    <div class="kpi-container" style="{border_style}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def get_risk_badge_html(risk_level: str) -> str:
    """Returns HTML badge for a given risk string."""
    lvl = risk_level.lower()
    if "urgent" in lvl:
        return '<span class="badge-urgent">🔴 Urgent</span>'
    elif "high" in lvl:
        return '<span class="badge-high">🟠 High</span>'
    elif "mod" in lvl:
        return '<span class="badge-moderate">🟡 Moderate</span>'
    else:
        return '<span class="badge-low">🟢 Low</span>'

def format_currency_inr(val: float) -> str:
    """Formats values nicely in Indian Rupee format."""
    if val is None or val != val:
        return "₹0"
    if abs(val) >= 1e7:
        return f"₹{val/1e7:.2f} Cr"
    elif abs(val) >= 1e5:
        return f"₹{val/1e5:.2f} Lakh"
    elif abs(val) >= 1e3:
        return f"₹{val:,.0f}"
    else:
        return f"₹{val:,.0f}"

def apply_chart_theme(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Applies a clean enterprise theme to any Plotly figure."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Inter", size=15, color="#0F172A")
        ),
        font=dict(family="Inter", color="#334155"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=40, r=30, t=50 if title else 25, b=40),
        height=height,
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_color="#FFFFFF",
            font_family="Inter"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            linecolor="#CBD5E1",
            tickfont=dict(size=11, color="#64748B")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            linecolor="#CBD5E1",
            tickfont=dict(size=11, color="#64748B")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )
    return fig
