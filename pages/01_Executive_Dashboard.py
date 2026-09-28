"""
Page 1: Executive Dashboard (Operations Command Center)
High-level situational awareness across the entire ATM network.
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
        page_title="Executive Dashboard | ATM Cash DSS",
        page_icon="🏧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    filters = render_global_sidebar(df)
    active_mode = filters.get("mode", "Operations")

    render_header(
        title="ATM Operations Command Center",
        subtitle=f"Live Network Status • Snapshot Date: {filters['date'].strftime('%d %b %Y')} • Mode: {active_mode}",
        badge="Executive Overview"
    )

    # Compute risk predictions and replenishment on the selected date snapshot
    snapshot_raw = get_snapshot_predictions(df, filters['date'])
    snapshot_filtered = filter_dataset(snapshot_raw, filters, apply_date=False)
    snapshot_filtered = calculate_replenishment_needs(snapshot_filtered)

    if snapshot_filtered.empty:
        st.warning("⚠️ No ATMs match the currently selected sidebar filters. Please adjust your filters.")
        return

    # Compute Top KPI metrics
    total_atms = len(snapshot_filtered)
    urgent_count = (snapshot_filtered['urgent_1d_score'] > 0.30).sum()
    high_priority_count = (snapshot_filtered['priority_score'] > 0.50).sum()
    low_cash_atms = (snapshot_filtered['pct_capacity_eod'] < 20.0).sum()
    total_refill_needed = snapshot_filtered['recommended_refill_amount'].sum()
    avg_cash_utilization = snapshot_filtered['pct_capacity_eod'].mean()
    recommended_visits = min(12, total_atms)

    # 1. Top KPI Row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        render_kpi("ATMs Monitored", f"{total_atms}", "Active fleet size")
    with col2:
        render_kpi("🔴 Urgent (1-Day)", f"{urgent_count}", "Risk > 30% tomorrow", COLOR_URGENT)
    with col3:
        render_kpi("🟠 High (3-Day)", f"{high_priority_count}", "Risk > 50% in 3 days", COLOR_HIGH)
    with col4:
        render_kpi("Below 20% Cash", f"{low_cash_atms}", "Immediate low cash state", COLOR_MODERATE)
    with col5:
        render_kpi("Estimated Refill", format_currency_inr(total_refill_needed), "Target 90% capacity")
    with col6:
        render_kpi("Avg Cash Level", f"{avg_cash_utilization:.1f}%", f"Top {recommended_visits} visits queued", COLOR_LOW)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 2. Main Visual: Geographic Risk Map + ATM Selected Profile
    map_col, profile_col = st.columns([1.6, 1.0])

    with map_col:
        st.markdown("<div class='dss-card-title'>📍 ATM Network Geospatial Risk Map</div>", unsafe_allow_html=True)
        
        # Color mapping for risk
        color_discrete_map = {
            "Urgent": COLOR_URGENT,
            "High": COLOR_HIGH,
            "Moderate": COLOR_MODERATE,
            "Low": COLOR_LOW
        }

        # Clean hover info
        map_df = snapshot_filtered.copy()
        map_df['Current Cash (INR)'] = map_df['cash_eod'].apply(lambda x: f"₹{x:,.0f}")
        map_df['Recommended Refill (INR)'] = map_df['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}")
        map_df['1D Risk %'] = (map_df['urgent_1d_score'] * 100).round(1).astype(str) + "%"
        map_df['3D Risk %'] = (map_df['priority_score'] * 100).round(1).astype(str) + "%"
        map_df['Cash %'] = map_df['pct_capacity_eod'].round(1).astype(str) + "%"
        map_df['Marker Size'] = np.clip(map_df['withdrawal_roll7_mean'] / 1000, 8, 26)

        fig_map = px.scatter_geo(
            map_df,
            lat='latitude',
            lon='longitude',
            color='risk_level',
            size='Marker Size',
            hover_name='atm_id',
            hover_data={
                'city': True,
                'atm_location_type': True,
                'Cash %': True,
                '1D Risk %': True,
                '3D Risk %': True,
                'Recommended Refill (INR)': True,
                'latitude': False,
                'longitude': False,
                'risk_level': False,
                'Marker Size': False
            },
            color_discrete_map=color_discrete_map,
            scope='asia',
            center=dict(lat=21.0, lon=78.5)
        )
        fig_map.update_geos(
            fitbounds="locations",
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor="#CBD5E1",
            showsubunits=True,
            subunitcolor="#E2E8F0",
            showland=True,
            landcolor="#F8FAFC",
            showocean=True,
            oceancolor="#EFF6FF",
            showlakes=True,
            lakecolor="#EFF6FF"
        )
        fig_map = apply_chart_theme(fig_map, height=480)
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(title=dict(text="Risk Classification"), orientation="h", y=0.98, x=0.02)
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with profile_col:
        st.markdown("<div class='dss-card-title'>🔍 ATM Detail Card</div>", unsafe_allow_html=True)
        atm_select_list = snapshot_filtered.sort_values('priority_score', ascending=False)['atm_id'].tolist()
        
        # Default to highest priority ATM
        default_atm = atm_select_list[0] if atm_select_list else None
        target_atm_id = st.selectbox("Select ATM to Inspect:", options=atm_select_list, index=0)

        atm_row = snapshot_filtered[snapshot_filtered['atm_id'] == target_atm_id].iloc[0]
        
        # Risk Badge
        badge_html = get_risk_badge_html(atm_row['risk_level'])

        with st.container(border=True):
            card_top_l, card_top_r = st.columns([2, 1])
            with card_top_l:
                st.markdown(f"<h3 style='margin:0; font-size: 1.4rem; color: #0F172A;'>{atm_row['atm_id']}</h3>", unsafe_allow_html=True)
                st.caption(f"📍 **{atm_row['city']}** • {atm_row['atm_location_type']} Location • Rank **#{atm_row['priority_rank']} of {len(snapshot_raw)}**")
            with card_top_r:
                st.markdown(badge_html, unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            with m1:
                st.metric(
                    label="Current Cash",
                    value=f"₹{atm_row['cash_eod']:,.0f}",
                    delta=f"Cap: ₹{atm_row['atm_cash_capacity']:,.0f}",
                    delta_color="off"
                )
            with m2:
                is_crit = atm_row['pct_capacity_eod'] < 20
                st.metric(
                    label="Cash Utilization",
                    value=f"{atm_row['pct_capacity_eod']:.1f}%",
                    delta="Critical (<20%)" if is_crit else "Healthy (>20%)",
                    delta_color="inverse" if is_crit else "normal"
                )

            m3, m4 = st.columns(2)
            with m3:
                is_urg = atm_row['urgent_1d_score'] > 0.3
                st.metric(
                    label="1-Day Urgency",
                    value=f"{atm_row['urgent_1d_score']*100:.1f}%",
                    delta="Urgent Alert" if is_urg else "Normal",
                    delta_color="inverse" if is_urg else "off"
                )
            with m4:
                is_hi = atm_row['priority_score'] > 0.5
                st.metric(
                    label="3-Day Priority",
                    value=f"{atm_row['priority_score']*100:.1f}%",
                    delta="High Priority" if is_hi else "Normal",
                    delta_color="inverse" if is_hi else "off"
                )

            st.divider()
            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.markdown(f"**Days Since Refill:** `{int(atm_row['days_since_replenishment'])} days`")
            with c_info2:
                st.markdown(f"**7D Avg Demand:** `₹{atm_row['withdrawal_roll7_mean']:,.0f}/day`")
            
            st.info(f"🚚 **Recommended Refill:** **₹{atm_row['recommended_refill_amount']:,.0f}** *(Target 90% Capacity)*")

    st.markdown("---")

    # 3. Two-Column Analytical Charts: Network Cash Trend & Risk Distribution
    row2_col1, row2_col2 = st.columns([1.5, 1.0])

    with row2_col1:
        st.markdown("<div class='dss-card-title'>📈 Fleet-Wide Cash & Demand Trends</div>", unsafe_allow_html=True)
        metric_choice = st.radio(
            "Select Trend Metric:",
            options=["Average Cash %", "Total Available Cash (₹)", "Daily Total Withdrawal (₹)", "Average Daily Withdrawal (₹)"],
            horizontal=True
        )

        # Compute historical time series aggregated across fleet
        date_agg = df.groupby('transaction_date').agg(
            avg_pct=('pct_capacity_eod', 'mean'),
            total_cash=('cash_eod', 'sum'),
            total_wd=('withdrawal_amount', 'sum'),
            avg_wd=('withdrawal_amount', 'mean')
        ).reset_index()

        fig_trend = go.Figure()
        if metric_choice == "Average Cash %":
            fig_trend.add_trace(go.Scatter(
                x=date_agg['transaction_date'], y=date_agg['avg_pct'],
                mode='lines', line=dict(color='#2563EB', width=2.5), name='Fleet Avg Cash %'
            ))
            fig_trend.add_hline(y=20, line_dash="dash", line_color="#DC2626", annotation_text="20% Low-Cash Threshold")
            fig_trend.update_layout(yaxis_title="Capacity %")
        elif metric_choice == "Total Available Cash (₹)":
            fig_trend.add_trace(go.Scatter(
                x=date_agg['transaction_date'], y=date_agg['total_cash'],
                mode='lines', line=dict(color='#059669', width=2.5), name='Total Fleet Cash (₹)'
            ))
            fig_trend.update_layout(yaxis_title="INR (₹)")
        elif metric_choice == "Daily Total Withdrawal (₹)":
            fig_trend.add_trace(go.Scatter(
                x=date_agg['transaction_date'], y=date_agg['total_wd'],
                mode='lines', line=dict(color='#D97706', width=2), name='Total Withdrawn (₹)'
            ))
            fig_trend.update_layout(yaxis_title="INR (₹)")
        else:
            fig_trend.add_trace(go.Scatter(
                x=date_agg['transaction_date'], y=date_agg['avg_wd'],
                mode='lines', line=dict(color='#7C3AED', width=2), name='Avg per ATM (₹)'
            ))
            fig_trend.update_layout(yaxis_title="INR (₹)")

        fig_trend = apply_chart_theme(fig_trend, height=320)
        st.plotly_chart(fig_trend, use_container_width=True)

    with row2_col2:
        st.markdown("<div class='dss-card-title'>📊 Risk Score Distribution (3-Day Horizon)</div>", unsafe_allow_html=True)
        fig_hist = px.histogram(
            snapshot_filtered,
            x='priority_score',
            nbins=12,
            color='risk_level',
            color_discrete_map=RISK_COLORS,
            labels={'priority_score': '3-Day Low Cash Probability', 'count': 'Number of ATMs'}
        )
        fig_hist.add_vline(x=0.50, line_dash="dash", line_color="#EA580C", annotation_text="0.5 Priority Threshold")
        fig_hist = apply_chart_theme(fig_hist, height=320)
        fig_hist.update_layout(showlegend=False, xaxis_title="Predicted 3-Day Risk Probability", yaxis_title="ATM Count")
        st.plotly_chart(fig_hist, use_container_width=True)

    # 4. Top Priority ATMs Table
    st.markdown("<div class='dss-card-title'>🚨 Top Priority Servicing Queue</div>", unsafe_allow_html=True)
    st.caption("ATMs prioritized by 3-day low-cash probability with 1-day urgency alerts. Showing highest priority candidates for replenishment.")

    top_queue = snapshot_filtered.sort_values('priority_score', ascending=False).head(15).copy()
    
    display_table = pd.DataFrame({
        "Rank": top_queue['priority_rank'],
        "ATM ID": top_queue['atm_id'],
        "City": top_queue['city'],
        "Location": top_queue['atm_location_type'],
        "Cash %": top_queue['pct_capacity_eod'].apply(lambda x: f"{x:.1f}%"),
        "1D Risk": top_queue['urgent_1d_score'].apply(lambda x: f"{x*100:.1f}%"),
        "3D Risk": top_queue['priority_score'].apply(lambda x: f"{x*100:.1f}%"),
        "Urgency": top_queue['risk_level'],
        "Days Since Refill": top_queue['days_since_replenishment'].astype(int),
        "7D Avg Demand": top_queue['withdrawal_roll7_mean'].apply(lambda x: f"₹{x:,.0f}"),
        "Recommended Refill": top_queue['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}")
    })

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True
    )

    # 5. Quick Navigation & Context Collapsible
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    nav_col1, nav_col2, _ = st.columns([1, 1, 2])
    with nav_col1:
        if st.button("🚚 Go to Replenishment Planner", use_container_width=True):
            st.switch_page("pages/05_Replenishment_Planner.py")
    with nav_col2:
        if st.button("🔬 Go to Policy Simulator", use_container_width=True):
            st.switch_page("pages/07_Policy_Simulator.py")

    with st.expander("ℹ️ About This Decision Support System (Methodology & Transparency)", expanded=False):
        st.markdown("""
        **System Objective & Operational Architecture:**
        - This platform is an interactive **Decision Support System (DSS)** designed for bank ATM cash management operations.
        - The methodology follows an end-to-end framework: **Observe → Analyze → Predict → Prioritize → Replenish → Evaluate**.
        - **Data Baseline:** 60 ATMs monitored across 10 major metropolitan and regional areas over a 2-year horizon (2023–2024).
        - **Predictive Horizons:**
          - `low_cash_next_1d`: Binary flag indicating if cash depletion will drop below 20% tomorrow (Urgent warning).
          - `low_cash_next_3d`: Probability of low cash state over any of the following 3 days (Priority score).
        - **Replenishment Sizing:** Direct calculation targeting 90% capacity refill (`max(0, Target - Current)`), verified against 7-day average withdrawal demand.
        """)

if __name__ == "__main__":
    main()
