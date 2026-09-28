"""
Page 5: Replenishment Planner & Interactive Refill Calculator
Translates predictive risk models into actionable daily servicing manifests and vehicle dispatch schedules.
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.styling import (
    inject_custom_css, render_header, render_kpi,
    get_risk_badge_html, format_currency_inr,
    COLOR_URGENT, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW
)
from utils.data_loader import load_atm_data, render_global_sidebar, filter_dataset
from utils.models_engine import get_snapshot_predictions
from utils.replenishment_engine import (
    calculate_replenishment_needs,
    generate_replenishment_plan,
    single_atm_refill_calculator
)

def main():
    st.set_page_config(
        page_title="Replenishment Planner | ATM Cash DSS",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    filters = render_global_sidebar(df)

    render_header(
        title="Replenishment Planning & Dispatch Manifest",
        subtitle=f"Constrained-Capacity Decision Engine • Planning Date: {filters['date'].strftime('%d %b %Y')}",
        badge="Decision Engine"
    )

    # Compute snapshot predictions
    snapshot_raw = get_snapshot_predictions(df, filters['date'])
    snapshot_filtered = filter_dataset(snapshot_raw, filters, apply_date=False)
    snapshot_filtered = calculate_replenishment_needs(snapshot_filtered)

    if snapshot_filtered.empty:
        st.warning("⚠️ No ATMs match the active filters.")
        return

    # 1. Operational Capacity Controls
    st.markdown("<div class='dss-card-title'>🚚 Operational Capacity & Strategy Constraints</div>", unsafe_allow_html=True)
    
    ctrl_col1, ctrl_col2 = st.columns([1.5, 2.0])
    with ctrl_col1:
        daily_capacity = st.slider(
            "Daily Armored Vehicle Servicing Capacity (ATMs/Day):",
            min_value=5,
            max_value=16,
            value=12,
            step=1,
            help="Select maximum number of ATMs operations can visit today (evaluated range: 5 to 16 ATMs/day)."
        )
    with ctrl_col2:
        strategy_mode = st.radio(
            "Prioritization Mechanism:",
            options=["Top-N Risk Ranking (Recommended)", "Arbitrary 50% Threshold Filter"],
            index=0,
            horizontal=True,
            help="Top-N ranking allocates scarce vehicle trips to the highest-risk ATMs rather than treating arbitrary probability thresholds as business truth."
        )

    # Strategy commentary
    if strategy_mode == "Top-N Risk Ranking (Recommended)":
        st.success(f"**Active Operational Policy:** Prioritizing the Top **{daily_capacity}** ATMs with highest 3-day risk scores. This dynamically maximizes risk mitigation within staff/vehicle constraints.")
    else:
        st.warning("⚠️ **Threshold Policy Notice:** The notebook cautions that arbitrary thresholds (e.g. 50% or 30%) do not account for resource constraints and can over-commit or under-utilize armored courier capacity.")

    # 2. Generate Plan
    plan_df = generate_replenishment_plan(snapshot_filtered, daily_capacity=daily_capacity)
    total_manifest_cash = plan_df['recommended_refill_amount'].sum()
    urgent_in_plan = (plan_df['urgent_1d_score'] > 0.30).sum()
    avg_cash_in_plan = plan_df['pct_capacity_eod'].mean()

    # Plan Summary KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("ATMs in Today's Manifest", f"{len(plan_df)} of {len(snapshot_filtered)}", f"Capacity limit: {daily_capacity}")
    with k2:
        render_kpi("Total Cash Required", format_currency_inr(total_manifest_cash), "To reach 90% target fill", COLOR_HIGH)
    with k3:
        render_kpi("Urgent ATMs Covered", f"{urgent_in_plan}", "1-day low-cash risk > 30%", COLOR_URGENT)
    with k4:
        render_kpi("Avg Cash Level in Queue", f"{avg_cash_in_plan:.1f}%", "Depleted inventory target", COLOR_MODERATE)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Recommended Replenishment Route / Manifest Table
    st.markdown(f"<div class='dss-card-title'>📋 Recommended Servicing Manifest (Top {len(plan_df)} Candidates)</div>", unsafe_allow_html=True)
    st.caption("Ranked by priority score (predicted 3-day low-cash probability). Urgent next-day risk highlighted.")

    # CSV Download
    csv_plan = plan_df[[
        'servicing_priority', 'atm_id', 'city', 'atm_location_type', 'pct_capacity_eod',
        'urgent_1d_score', 'priority_score', 'days_since_replenishment',
        'withdrawal_roll7_mean', 'recommended_refill_amount', 'equivalent_demand_days'
    ]].to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Replenishment Manifest (CSV)",
        data=csv_plan,
        file_name=f"replenishment_manifest_{filters['date'].strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    display_manifest = pd.DataFrame({
        "Priority": plan_df['servicing_priority'],
        "ATM ID": plan_df['atm_id'],
        "City": plan_df['city'],
        "Location": plan_df['atm_location_type'],
        "Current Cash %": plan_df['pct_capacity_eod'].round(1).astype(str) + "%",
        "1D Risk (Urgency)": (plan_df['urgent_1d_score'] * 100).round(1).astype(str) + "%",
        "3D Risk (Score)": (plan_df['priority_score'] * 100).round(1).astype(str) + "%",
        "Days Since Refill": plan_df['days_since_replenishment'].astype(int),
        "7D Avg Demand (₹)": plan_df['withdrawal_roll7_mean'].apply(lambda x: f"₹{x:,.0f}/day"),
        "Recommended Refill (₹)": plan_df['recommended_refill_amount'].apply(lambda x: f"₹{x:,.0f}"),
        "Demand Cover": plan_df['equivalent_demand_days'].apply(lambda x: f"{x:.1f} days")
    })

    st.dataframe(display_manifest, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 4. Interactive Refill Sizing Calculator
    st.markdown("<div class='dss-card-title'>💰 Interactive Refill Sizing Calculator</div>", unsafe_allow_html=True)
    st.caption("Adjust fill target percentages and simulate refill volume against expected local withdrawal demand.")

    calc_c1, calc_c2 = st.columns([1, 1.4])

    with calc_c1:
        atm_select_calc = st.selectbox(
            "Select ATM to Calculate Refill:",
            options=plan_df['atm_id'].tolist() if not plan_df.empty else snapshot_filtered['atm_id'].tolist(),
            index=0
        )
        target_fill_slider = st.slider(
            "Target Capacity Fill Percentage (%):",
            min_value=70,
            max_value=100,
            value=90,
            step=5,
            help="Standard banking target is 90% of ATM cash capacity."
        )

    atm_calc_row = snapshot_filtered[snapshot_filtered['atm_id'] == atm_select_calc].iloc[0]
    calc_res = single_atm_refill_calculator(
        current_cash=atm_calc_row['cash_eod'],
        capacity=atm_calc_row['atm_cash_capacity'],
        roll7_mean=atm_calc_row['withdrawal_roll7_mean'],
        target_pct=target_fill_slider / 100.0
    )

    with calc_c2:
        st.markdown(f"""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px;">
<div style="font-weight: 700; font-size: 1.15rem; color: #0F172A; margin-bottom: 12px;">Refill Assessment for <b>{atm_select_calc}</b> ({atm_calc_row['city']} • {atm_calc_row['atm_location_type']})</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">
<div><span style="font-size: 0.78rem; color: #64748B;">Current Available Cash:</span><br><b style="font-size: 1.1rem; color: #0F172A;">₹{calc_res['current_cash']:,.0f}</b></div>
<div><span style="font-size: 0.78rem; color: #64748B;">Total ATM Capacity:</span><br><b style="font-size: 1.1rem; color: #0F172A;">₹{calc_res['capacity']:,.0f}</b></div>
<div><span style="font-size: 0.78rem; color: #64748B;">Target Cash Level ({target_fill_slider}%):</span><br><b style="font-size: 1.1rem; color: #059669;">₹{calc_res['target_cash']:,.0f}</b></div>
<div><span style="font-size: 0.78rem; color: #1E40AF;">Recommended Refill Amount:</span><br><b style="font-size: 1.25rem; color: #1D4ED8;">₹{calc_res['recommended_refill']:,.0f}</b></div>
</div>
<div style="border-top: 1px solid #E2E8F0; padding-top: 10px;">
<div style="font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 4px;">Demand Sanity Check:</div>
<div style="font-size: 0.82rem; color: #334155;">
• Trailing 7-day average withdrawal: <b>₹{calc_res['roll7_mean']:,.0f}/day</b><br>
• This refill represents approximately <b>{calc_res['equivalent_days']:.1f} days</b> of typical demand (<b>{calc_res['equivalent_weeks']:.1f} weeks</b>).
</div>
<div style="font-size: 0.75rem; color: #64748B; margin-top: 6px; font-style: italic;">* Planning estimate for vehicle loading; does not represent a guaranteed time to stockout.</div>
</div>
</div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
