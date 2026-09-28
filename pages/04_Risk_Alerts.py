"""
Page 4: Risk & Alerts (ATM Early Warning Center)
Early warning monitoring, risk matrix bubble visualization, and non-causal model driver explanations.
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
from utils.models_engine import get_snapshot_predictions, get_feature_importances
from utils.replenishment_engine import calculate_replenishment_needs

def main():
    st.set_page_config(
        page_title="Risk & Alerts | ATM Cash DSS",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    filters = render_global_sidebar(df)

    render_header(
        title="ATM Early Warning Center & Risk Matrix",
        subtitle=f"Predictive Low-Cash Indicators • Snapshot: {filters['date'].strftime('%d %b %Y')}",
        badge="Early Warning System"
    )

    # Compute risk predictions and replenishment needs
    snapshot_raw = get_snapshot_predictions(df, filters['date'])
    snapshot_filtered = filter_dataset(snapshot_raw, filters, apply_date=False)
    snapshot_filtered = calculate_replenishment_needs(snapshot_filtered)

    if snapshot_filtered.empty:
        st.warning("⚠️ No ATMs match the active filters.")
        return

    # Counts
    urgent_cnt = (snapshot_filtered['urgent_1d_score'] > 0.30).sum()
    high_cnt = (snapshot_filtered['priority_score'] > 0.50).sum()
    mod_cnt = ((snapshot_filtered['priority_score'] >= 0.20) & (snapshot_filtered['priority_score'] <= 0.50)).sum()
    low_cnt = (snapshot_filtered['priority_score'] < 0.20).sum()

    # 1. Headline Alert Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi("🚨 Urgent Action Required", f"{urgent_cnt} ATMs", "1-Day Low-Cash Probability > 30%", COLOR_URGENT)
    with c2:
        render_kpi("⚠️ High 3-Day Risk", f"{high_cnt} ATMs", "3-Day Low-Cash Probability > 50%", COLOR_HIGH)
    with c3:
        render_kpi("🟡 Moderate Risk", f"{mod_cnt} ATMs", "3-Day Probability 20% - 50%", COLOR_MODERATE)
    with c4:
        render_kpi("🟢 Healthy / Monitor", f"{low_cnt} ATMs", "Low Probability < 20%", COLOR_LOW)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Main Visual: Risk Matrix (Scatter/Bubble Chart)
    st.markdown("<div class='dss-card-title'>🎯 ATM Risk Matrix (Cash % vs 3-Day Risk)</div>", unsafe_allow_html=True)
    st.caption("Identifies the operational danger zone: ATMs with low remaining cash AND high forward withdrawal velocity.")

    bubble_df = snapshot_filtered.copy()
    bubble_df['Cash %'] = bubble_df['pct_capacity_eod'].round(1)
    bubble_df['3-Day Risk %'] = (bubble_df['priority_score'] * 100).round(1)
    bubble_df['1-Day Urgency %'] = (bubble_df['urgent_1d_score'] * 100).round(1)
    bubble_df['Bubble Size'] = np.clip(bubble_df['withdrawal_roll7_mean'] / 800, 10, 32)
    bubble_df['Refill (INR)'] = bubble_df['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}")

    fig_matrix = px.scatter(
        bubble_df,
        x='Cash %',
        y='3-Day Risk %',
        size='Bubble Size',
        color='risk_level',
        color_discrete_map=RISK_COLORS,
        hover_name='atm_id',
        hover_data={
            'city': True,
            'atm_location_type': True,
            'Cash %': True,
            '3-Day Risk %': True,
            '1-Day Urgency %': True,
            'Refill (INR)': True,
            'Bubble Size': False,
            'risk_level': False
        },
        labels={'Cash %': 'Current Cash Level (% of Capacity)', '3-Day Risk %': 'Predicted 3-Day Low Cash Probability (%)'}
    )

    # Add Critical Operational Danger Zone Quadrant
    fig_matrix.add_vrect(
        x0=0, x1=35,
        fillcolor="rgba(220, 38, 38, 0.05)",
        layer="below", line_width=1, line_dash="dot", line_color="#DC2626"
    )
    fig_matrix.add_hline(y=50, line_dash="dash", line_color="#EA580C", annotation_text="High Risk Threshold (50%)")
    fig_matrix.add_vline(x=20, line_dash="dash", line_color="#DC2626", annotation_text="Low Cash Alert (20%)")

    fig_matrix = apply_chart_theme(fig_matrix, height=450)
    fig_matrix.update_layout(
        xaxis=dict(range=[0, 105]),
        yaxis=dict(range=[-5, 105]),
        legend=dict(title=dict(text="Risk Classification"), orientation="h", y=1.04, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")

    # 3. Alert Table & Feature Driver Attribution
    tab_alerts, tab_explanation = st.tabs(["📋 Prioritized Alert Roster", "🔬 Risk Driver Attribution (Model Signals)"])

    with tab_alerts:
        st.markdown("<div class='dss-card-title'>Categorized Alerts Roster</div>", unsafe_allow_html=True)
        
        # Download button
        csv_alerts = snapshot_filtered[[
            'priority_rank', 'atm_id', 'city', 'atm_location_type', 'pct_capacity_eod',
            'urgent_1d_score', 'priority_score', 'risk_level', 'days_since_replenishment',
            'withdrawal_roll7_mean', 'recommended_refill_amount'
        ]].to_csv(index=False).encode('utf-8')

        st.download_button(
            label="📥 Download Current Risk Assessment (CSV)",
            data=csv_alerts,
            file_name=f"atm_risk_assessment_{filters['date'].strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        alert_display = pd.DataFrame({
            "Rank": snapshot_filtered['priority_rank'],
            "ATM ID": snapshot_filtered['atm_id'],
            "City": snapshot_filtered['city'],
            "Location": snapshot_filtered['atm_location_type'],
            "Current Cash %": snapshot_filtered['pct_capacity_eod'].round(1).astype(str) + "%",
            "1-Day Urgency": (snapshot_filtered['urgent_1d_score'] * 100).round(1).astype(str) + "%",
            "3-Day Risk": (snapshot_filtered['priority_score'] * 100).round(1).astype(str) + "%",
            "Priority Score": snapshot_filtered['priority_score'].round(3),
            "Status Tier": snapshot_filtered['risk_level'],
            "Days Since Refill": snapshot_filtered['days_since_replenishment'].astype(int),
            "7D Avg Demand": snapshot_filtered['withdrawal_roll7_mean'].apply(lambda x: f"₹{x:,.0f}"),
            "Recommended Refill": snapshot_filtered['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}")
        })

        st.dataframe(alert_display, use_container_width=True, hide_index=True)

    with tab_explanation:
        st.markdown("<div class='dss-card-title'>Why Did the Model Flag This ATM?</div>", unsafe_allow_html=True)
        st.caption("Inspect the dominant model-driven risk signals for any chosen ATM. (Important: Represents statistical reliance in the model, not proved causal mechanisms.)")

        atm_choice = st.selectbox(
            "Select ATM to Inspect Risk Drivers:",
            options=snapshot_filtered.sort_values('priority_score', ascending=False)['atm_id'].tolist(),
            index=0
        )

        atm_inspect = snapshot_filtered[snapshot_filtered['atm_id'] == atm_choice].iloc[0]

        driver_c1, driver_c2 = st.columns([1, 1.4])

        with driver_c1:
            st.markdown(f"### Assessment for **{atm_choice}**")
            st.markdown(f"**Assigned Tier:** {get_risk_badge_html(atm_inspect['risk_level'])}", unsafe_allow_html=True)
            st.markdown(f"""
            - **Current Cash Level:** `{atm_inspect['pct_capacity_eod']:.1f}%` of capacity
            - **Days Since Replenishment:** `{int(atm_inspect['days_since_replenishment'])} days`
            - **Recent 7-Day Velocity:** `₹{atm_inspect['withdrawal_roll7_mean']:,.0f}/day`
            - **Yesterday's Withdrawal:** `₹{atm_inspect.get('withdrawal_lag_1d', 0):,.0f}`
            - **Day of Month:** `Day {int(atm_inspect['day_of_month'])}` {'(In Salary Window)' if atm_inspect['day_of_month'] in [1,2,3] else ''}
            - **Weekend Flag:** `{'Yes' if atm_inspect['is_weekend'] else 'No'}`
            """)

            st.info("""
            **Operational Interpretation:**
            The combination of low remaining reserve and elapsed days since the last refill creates high statistical likelihood of cash exhaustion under normal customer withdrawal demand.
            """)

        with driver_c2:
            st.markdown("#### Global Feature Importance (XGBoost 3-Day Risk Model)")
            imp_df = get_feature_importances()
            fig_imp = px.bar(
                imp_df,
                x='Importance',
                y='Feature',
                orientation='h',
                color='Importance',
                color_continuous_scale="Blues"
            )
            fig_imp = apply_chart_theme(fig_imp, height=340)
            fig_imp.update_layout(showlegend=False, xaxis_title="Model Relative Weight (Gain)", yaxis_title="")
            st.plotly_chart(fig_imp, use_container_width=True)

if __name__ == "__main__":
    main()
