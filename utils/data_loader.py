"""
Data loading and preprocessing module for ATM Cash Management DSS.
Uses Streamlit caching for instant reactivity.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

DAILY_FEATURES_PATH = "atm_daily_features (1).csv"
ATM_METADATA_PATH = "data/atm_metadata.csv"

def compute_days_since_replenishment(series: pd.Series) -> np.ndarray:
    """Running count of days since the last replenishment_flag == 1, per ATM."""
    out = np.zeros(len(series), dtype=int)
    counter = 999
    for i, v in enumerate(series):
        counter = 0 if v == 1 else counter + 1
        out[i] = counter
    return out

@st.cache_data(show_spinner=False)
def load_atm_data() -> pd.DataFrame:
    """
    Loads daily features and enriches with ATM metadata (lat, lon, status).
    Guarantees days_since_replenishment is calculated properly.
    """
    if not os.path.exists(DAILY_FEATURES_PATH):
        st.error(f"Required dataset file not found: `{DAILY_FEATURES_PATH}`.")
        st.stop()

    df = pd.read_csv(DAILY_FEATURES_PATH)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Ensure sorted order for time series operations
    df = df.sort_values(['atm_id', 'transaction_date']).reset_index(drop=True)

    # Compute days_since_replenishment if not already present
    if 'days_since_replenishment' not in df.columns:
        df['days_since_replenishment'] = df.groupby('atm_id')['replenishment_flag'].transform(
            lambda s: compute_days_since_replenishment(s.values)
        )

    # Merge metadata (lat, lon, atm_status)
    if os.path.exists(ATM_METADATA_PATH):
        meta = pd.read_csv(ATM_METADATA_PATH)
        cols_to_merge = [c for c in ['atm_id', 'latitude', 'longitude', 'atm_status'] if c in meta.columns]
        df = df.merge(meta[cols_to_merge], on='atm_id', how='left')
    else:
        # Default placeholder values if metadata is absent
        df['latitude'] = 19.0760
        df['longitude'] = 72.8777
        df['atm_status'] = 'Active'

    # Ensure atm_status has no NaNs
    df['atm_status'] = df['atm_status'].fillna('Active')
    
    # Calculate % capacity utilization
    if 'pct_capacity_eod' not in df.columns:
        df['pct_capacity_eod'] = (df['cash_eod'] / df['atm_cash_capacity']) * 100

    return df

@st.cache_data(show_spinner=False)
def load_atm_metadata() -> pd.DataFrame:
    """Loads static ATM metadata table."""
    if os.path.exists(ATM_METADATA_PATH):
        return pd.read_csv(ATM_METADATA_PATH)
    return pd.DataFrame()

def render_global_sidebar(df: pd.DataFrame) -> dict:
    """
    Renders persistent global filters in the Streamlit sidebar.
    Returns the dictionary of active filters.
    """
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 12px 0 16px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 16px;">
        <span style="font-size: 1.8rem;">🏧</span>
        <h2 style="margin: 4px 0 0 0; font-size: 1.25rem; font-weight: 700; color: #0F172A;">ATM CASH DSS</h2>
        <p style="margin: 0; font-size: 0.78rem; color: #64748B;">Operations & Risk Decision Support</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Action Mode Selector
    st.sidebar.markdown("### 🎯 Decision Perspective")
    mode_options = ["Operations", "Management", "Analytics"]
    selected_mode = st.sidebar.radio(
        "Dashboard Mode",
        options=mode_options,
        index=0,
        help="Customizes view focus: Operations (Daily Action Lists), Management (Executive Fleet KPIs), Analytics (Diagnostic EDA & Models)"
    )
    st.session_state['active_mode'] = selected_mode

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Global Network Filters")

    # Available Dates (Default to the latest date: 2024-12-29)
    all_dates = sorted(df['transaction_date'].dt.date.unique())
    default_date = pd.to_datetime("2024-12-29").date()
    default_idx = all_dates.index(default_date) if default_date in all_dates else len(all_dates) - 1

    selected_date = st.sidebar.selectbox(
        "📅 Analysis Date",
        options=all_dates,
        index=default_idx,
        help="Select snapshot date for risk assessment and operational planning."
    )

    # City Filter
    cities = ["All"] + sorted(df['city'].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("🏙️ City", options=cities, index=0)

    # Location Type Filter
    loc_types = ["All"] + sorted(df['atm_location_type'].dropna().unique().tolist())
    selected_loc = st.sidebar.selectbox("📍 Location Type", options=loc_types, index=0)

    # ATM Status
    statuses = ["All", "Active", "Inactive"]
    selected_status = st.sidebar.selectbox("⚡ ATM Status", options=statuses, index=0)

    # Risk Level Filter
    risk_options = ["All", "Urgent", "High", "Moderate", "Low"]
    selected_risk = st.sidebar.selectbox("⚠️ Risk Category", options=risk_options, index=0)

    # Specific ATM Search / Select
    atm_list = ["All"] + sorted(df['atm_id'].unique().tolist())
    selected_atm = st.sidebar.selectbox("🏧 Specific ATM Drilldown", options=atm_list, index=0)

    # Reset Filters Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.session_state['reset_filters'] = True
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("MSc Big Data Analytics Project • Production DSS v2.4")

    return {
        "mode": selected_mode,
        "date": pd.to_datetime(selected_date),
        "city": selected_city,
        "location_type": selected_loc,
        "status": selected_status,
        "risk_level": selected_risk,
        "atm_id": selected_atm
    }

def filter_dataset(df: pd.DataFrame, filters: dict, apply_date: bool = True) -> pd.DataFrame:
    """Applies global filters to a dataframe."""
    filtered = df.copy()

    if apply_date and filters.get("date") is not None:
        filtered = filtered[filtered['transaction_date'] == filters["date"]]

    if filters.get("city") and filters["city"] != "All":
        filtered = filtered[filtered['city'] == filters["city"]]

    if filters.get("location_type") and filters["location_type"] != "All":
        filtered = filtered[filtered['atm_location_type'] == filters["location_type"]]

    if filters.get("status") and filters["status"] != "All":
        filtered = filtered[filtered['atm_status'] == filters["status"]]

    if filters.get("atm_id") and filters["atm_id"] != "All":
        filtered = filtered[filtered['atm_id'] == filters["atm_id"]]

    return filtered
