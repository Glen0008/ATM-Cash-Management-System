"""
Page 2: ATM Network Monitor & Deep Dive
Complete fleet exploration, interactive table filtering, and individual ATM operational profiles.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.styling import (
    inject_custom_css, render_header, render_kpi,
    get_risk_badge_html, format_currency_inr, apply_chart_theme,
    COLOR_URGENT, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW, RISK_COLORS
)
from utils.data_loader import load_atm_data, render_global_sidebar, filter_dataset
from utils.models_engine import get_snapshot_predictions
from utils.replenishment_engine import calculate_replenishment_needs

def main():
    st.set_page_config(
        page_title="ATM Network Monitor | ATM Cash DSS",
        page_icon="📍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    filters = render_global_sidebar(df)

    render_header(
        title="ATM Network Monitor & Fleet Explorer",
        subtitle=f"Comprehensive fleet status • Snapshot Date: {filters['date'].strftime('%d %b %Y')}",
        badge="Network Explorer"
    )

    # Compute snapshot predictions
    snapshot_raw = get_snapshot_predictions(df, filters['date'])
    snapshot_filtered = filter_dataset(snapshot_raw, filters, apply_date=False)
    snapshot_filtered = calculate_replenishment_needs(snapshot_filtered)

    if snapshot_filtered.empty:
        st.warning("⚠️ No ATMs match the selected sidebar filters. Please adjust your criteria.")
        return

    # Fleet-wide KPI Row
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)
    with kpi_c1:
        render_kpi("Filtered ATMs", f"{len(snapshot_filtered)}", f"Of {len(snapshot_raw)} total fleet")
    with kpi_c2:
        active_count = (snapshot_filtered['atm_status'] == 'Active').sum()
        render_kpi("Active Status", f"{active_count}", f"{(active_count/len(snapshot_filtered)*100):.0f}% operational")
    with kpi_c3:
        low_cash = (snapshot_filtered['pct_capacity_eod'] < 20.0).sum()
        render_kpi("Below 20% Cash", f"{low_cash}", "Critical balance", COLOR_URGENT if low_cash > 0 else COLOR_LOW)
    with kpi_c4:
        render_kpi("Mean Cash %", f"{snapshot_filtered['pct_capacity_eod'].mean():.1f}%", f"Median: {snapshot_filtered['pct_capacity_eod'].median():.1f}%")
    with kpi_c5:
        avg_demand = snapshot_filtered['withdrawal_roll7_mean'].mean()
        render_kpi("Avg Daily Demand", format_currency_inr(avg_demand), "7-day rolling window")
    with kpi_c6:
        avg_days = snapshot_filtered['days_since_replenishment'].mean()
        render_kpi("Avg Days Since Refill", f"{avg_days:.1f} days", "Fleet turnaround cycle")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Tabs for Network Table vs ATM Deep Dive
    tab_table, tab_deep_dive = st.tabs(["📋 Fleet-Wide ATM Table", "🔍 Individual ATM Deep Dive"])

    with tab_table:
        st.markdown("<div class='dss-card-title'>Interactive ATM Operations Table</div>", unsafe_allow_html=True)
        st.caption("Search, sort, and inspect fleet parameters. Download filtered records for field dispatch.")

        # Prepare formatted table
        table_export = snapshot_filtered[[
            'priority_rank', 'atm_id', 'city', 'atm_location_type', 'atm_status',
            'cash_eod', 'atm_cash_capacity', 'pct_capacity_eod', 'withdrawal_roll7_mean',
            'urgent_1d_score', 'priority_score', 'risk_level',
            'days_since_replenishment', 'recommended_refill_amount'
        ]].copy()

        # Download button
        csv_data = table_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered ATM Data (CSV)",
            data=csv_data,
            file_name=f"atm_network_status_{filters['date'].strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        display_df = pd.DataFrame({
            "Rank": table_export['priority_rank'],
            "ATM ID": table_export['atm_id'],
            "City": table_export['city'],
            "Location Type": table_export['atm_location_type'],
            "Status": table_export['atm_status'],
            "Current Cash (₹)": table_export['cash_eod'].apply(lambda x: f"₹{x:,.0f}"),
            "Capacity (₹)": table_export['atm_cash_capacity'].apply(lambda x: f"₹{x:,.0f}"),
            "Cash Utilization %": table_export['pct_capacity_eod'].round(1),
            "7D Avg Demand (₹)": table_export['withdrawal_roll7_mean'].apply(lambda x: f"₹{x:,.0f}"),
            "1D Risk (Urgency)": table_export['urgent_1d_score'].apply(lambda x: f"{x*100:.1f}%"),
            "3D Risk (Priority)": table_export['priority_score'].apply(lambda x: f"{x*100:.1f}%"),
            "Risk Tier": table_export['risk_level'],
            "Days Since Refill": table_export['days_since_replenishment'].astype(int),
            "Recommended Refill (₹)": table_export['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}")
        })

        st.dataframe(
            display_df,
            column_config={
                "Cash Utilization %": st.column_config.ProgressColumn(
                    "Cash Utilization %",
                    help="End-of-day cash as percentage of capacity",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            },
            use_container_width=True,
            hide_index=True
        )

    with tab_deep_dive:
        st.markdown("<div class='dss-card-title'>ATM Detailed Operational Profile</div>", unsafe_allow_html=True)
        
        atm_options = sorted(snapshot_filtered['atm_id'].unique().tolist())
        selected_atm_id = st.selectbox("Select Target ATM to Analyze:", options=atm_options, index=0)

        # Get ATM full history from base dataframe
        atm_history = df[df['atm_id'] == selected_atm_id].sort_values('transaction_date').copy()
        atm_current = snapshot_filtered[snapshot_filtered['atm_id'] == selected_atm_id].iloc[0]

        # Top Header Profile Card
        with st.container(border=True):
            dd_top_l, dd_top_r = st.columns([3, 1])
            with dd_top_l:
                st.markdown(f"<h2 style='margin: 0; color: #0F172A; font-weight: 700; font-size: 1.6rem;'>{atm_current['atm_id']}</h2>", unsafe_allow_html=True)
                st.caption(f"📍 **{atm_current['city']}** • {atm_current['atm_location_type']} • Branch {atm_current['branch_id']} • Status: **{atm_current['atm_status']}**")
            with dd_top_r:
                badge_html = get_risk_badge_html(atm_current['risk_level'])
                st.markdown(badge_html, unsafe_allow_html=True)

            m_row1, m_row2, m_row3 = st.columns(3)
            with m_row1:
                st.metric("Current Cash", f"₹{atm_current['cash_eod']:,.0f}", f"Cap: ₹{atm_current['atm_cash_capacity']:,.0f}", delta_color="off")
            with m_row2:
                is_crit = atm_current['pct_capacity_eod'] < 20
                st.metric("Cash Utilization", f"{atm_current['pct_capacity_eod']:.1f}%", "Critical (<20%)" if is_crit else "Healthy (>20%)", delta_color="inverse" if is_crit else "normal")
            with m_row3:
                st.metric("Priority Rank", f"#{atm_current['priority_rank']}", f"Of {len(snapshot_raw)} ATMs", delta_color="off")

            m_row4, m_row5, m_row6 = st.columns(3)
            with m_row4:
                is_urg = atm_current['urgent_1d_score'] > 0.3
                st.metric("1-Day Urgency", f"{atm_current['urgent_1d_score']*100:.1f}%", "Urgent Alert" if is_urg else "Normal", delta_color="inverse" if is_urg else "off")
            with m_row5:
                st.metric("Days Since Refill", f"{int(atm_current['days_since_replenishment'])} days", "Elapsed time", delta_color="off")
            with m_row6:
                st.metric("Recommended Refill", f"₹{atm_current['recommended_refill_amount']:,.0f}", "To 90% target fill", delta_color="normal")

        # Historical Cash Level Trajectory Chart
        st.markdown("<div class='dss-card-title'>Historical Cash Trajectory & Replenishment Cycles</div>", unsafe_allow_html=True)
        st.caption("Visualizing the cash depletion rate, replenishment injections, and the critical 20% shortage risk threshold over time.")

        # Date range slider for the selected ATM
        min_date = atm_history['transaction_date'].min().date()
        max_date = atm_history['transaction_date'].max().date()
        date_range = st.slider(
            "Select Historical Window:",
            min_value=min_date,
            max_value=max_date,
            value=(max(min_date, max_date - pd.Timedelta(days=120)), max_date)
        )

        filtered_history = atm_history[
            (atm_history['transaction_date'].dt.date >= date_range[0]) &
            (atm_history['transaction_date'].dt.date <= date_range[1])
        ].copy()

        fig_atm_hist = go.Figure()

        # Cash balance line
        fig_atm_hist.add_trace(go.Scatter(
            x=filtered_history['transaction_date'],
            y=filtered_history['cash_eod'],
            mode='lines',
            name='Cash Level (EOD)',
            line=dict(color='#2563EB', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.06)'
        ))

        # 20% Critical threshold line
        capacity_val = atm_current['atm_cash_capacity']
        low_cash_val = capacity_val * 0.20
        fig_atm_hist.add_hline(
            y=low_cash_val,
            line_dash="dash",
            line_color="#DC2626",
            annotation_text=f"20% Threshold (₹{low_cash_val:,.0f})",
            annotation_position="bottom right"
        )

        # 90% Capacity Target Line
        target_val = capacity_val * 0.90
        fig_atm_hist.add_hline(
            y=target_val,
            line_dash="dot",
            line_color="#059669",
            annotation_text=f"90% Refill Target (₹{target_val:,.0f})",
            annotation_position="top right"
        )

        # Mark replenishment days
        replen_events = filtered_history[filtered_history['replenishment_flag'] == 1]
        if not replen_events.empty:
            fig_atm_hist.add_trace(go.Scatter(
                x=replen_events['transaction_date'],
                y=replen_events['cash_eod'],
                mode='markers',
                name='Replenishment Event',
                marker=dict(symbol='triangle-up', size=12, color='#10B981', line=dict(width=1, color='#047857'))
            ))

        fig_atm_hist = apply_chart_theme(fig_atm_hist, title=f"{selected_atm_id} Cash Level (INR) Over Time", height=380)
        fig_atm_hist.update_layout(yaxis_title="Available Cash (₹)", hovermode="x unified")
        st.plotly_chart(fig_atm_hist, use_container_width=True)

        # Daily Withdrawal Demand History
        st.markdown("<div class='dss-card-title'>Daily Withdrawal Demand vs 7-Day Rolling Average</div>", unsafe_allow_html=True)
        fig_wd = go.Figure()
        fig_wd.add_trace(go.Bar(
            x=filtered_history['transaction_date'],
            y=filtered_history['withdrawal_amount'],
            name='Daily Withdrawal (₹)',
            marker_color='rgba(100, 116, 139, 0.45)'
        ))
        fig_wd.add_trace(go.Scatter(
            x=filtered_history['transaction_date'],
            y=filtered_history['withdrawal_roll7_mean'],
            name='7-Day Rolling Mean',
            line=dict(color='#DC2626', width=2)
        ))
        fig_wd = apply_chart_theme(fig_wd, title=f"{selected_atm_id} Withdrawal Velocity", height=300)
        fig_wd.update_layout(yaxis_title="Withdrawals (₹)", hovermode="x unified")
        st.plotly_chart(fig_wd, use_container_width=True)

if __name__ == "__main__":
    main()
