"""
Page 7: Replenishment Policy Simulator
Simulates operational policies under fleet capacity constraints, highlighting the honest negative case at N=5.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.styling import (
    inject_custom_css, render_header, render_kpi,
    apply_chart_theme, COLOR_URGENT, COLOR_HIGH, COLOR_LOW, COLOR_PRIMARY_NAVY
)
from utils.data_loader import load_atm_data, render_global_sidebar
from utils.simulation_engine import (
    BACKTEST_BENCHMARK_RESULTS,
    get_policy_comparison_metrics
)

def main():
    st.set_page_config(
        page_title="Policy Simulator | ATM Cash DSS",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    _ = render_global_sidebar(df)

    render_header(
        title="Replenishment Policy Simulator & Stress Test",
        subtitle="Empirical backtesting across 60 ATMs over 59 out-of-sample days • Fixed Schedule vs Model-Driven Prioritization",
        badge="Policy Simulation"
    )

    # 1. Operational Capacity Controls
    st.markdown("<div class='dss-card-title'>🎛️ Operational Parameter Simulation</div>", unsafe_allow_html=True)
    
    col_slider, col_desc = st.columns([1.5, 2])
    with col_slider:
        sim_capacity = st.slider(
            "Simulate Daily Servicing Capacity (ATMs / Day):",
            min_value=5,
            max_value=16,
            value=12,
            step=1,
            help="Backtested range in notebook: N = 5, 8, 12, 16."
        )
    with col_desc:
        st.markdown(f"""
        **Simulation Parameters:**
        - **Fleet:** 60 ATMs evaluated simultaneously
        - **Horizon:** 59 out-of-sample test days
        - **Target Fill:** 90% of ATM cash capacity upon visit
        - **Outage Criteria:** Cash available < 20% capacity threshold
        """)

    # Get comparison metrics
    res = get_policy_comparison_metrics(sim_capacity)

    # 2. Side-by-Side Head-to-Head Comparison
    col_fix, col_mod, col_diff = st.columns(3)
    with col_fix:
        render_kpi(
            "Fixed 14-Day Schedule",
            f"{res['fixed_low_cash_days']:,} Days",
            f"Trips dispatched: {res['fixed_trips']:,}",
            "#64748B"
        )
    with col_mod:
        mod_color = COLOR_LOW if res['reduction_pct'] > 0 else COLOR_URGENT
        render_kpi(
            "Model-Driven Policy",
            f"{res['model_low_cash_days']:,} Days",
            f"Trips dispatched: {res['model_trips']:,}",
            mod_color
        )
    with col_diff:
        diff_color = COLOR_LOW if res['reduction_pct'] > 0 else COLOR_URGENT
        sign = "+" if res['reduction_pct'] > 0 else ""
        render_kpi(
            "Outage Reduction %",
            f"{sign}{res['reduction_pct']:.1f}%",
            res['performance'],
            diff_color
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Capacity Sensitivity Curve Chart
    st.markdown("<div class='dss-card-title'>📈 Capacity Sensitivity Curve (Low-Cash Days vs Visit Capacity)</div>", unsafe_allow_html=True)
    st.caption("Visualizing the performance crossover between fixed rotation and risk-ranked dispatch.")

    fig_sens = go.Figure()
    bench = BACKTEST_BENCHMARK_RESULTS

    # Fixed schedule curve
    fig_sens.add_trace(go.Scatter(
        x=bench['Capacity (N)'],
        y=bench['Fixed Low-Cash Days'],
        mode='lines+markers',
        name='Fixed 14-Day Schedule',
        line=dict(color='#475569', width=3),
        marker=dict(size=9)
    ))

    # Model-driven curve
    fig_sens.add_trace(go.Scatter(
        x=bench['Capacity (N)'],
        y=bench['Model Low-Cash Days'],
        mode='lines+markers',
        name='Model-Driven (Risk Ranking)',
        line=dict(color='#2563EB', width=3),
        marker=dict(size=9)
    ))

    # Highlight active slider capacity
    fig_sens.add_vline(
        x=sim_capacity,
        line_dash="dot",
        line_color="#DC2626",
        annotation_text=f"Selected N={sim_capacity}",
        annotation_position="top right"
    )

    fig_sens = apply_chart_theme(fig_sens, height=380)
    fig_sens.update_layout(
        xaxis=dict(title="Daily Armored Vehicle Capacity (N ATMs/Day)", tickmode='linear', tick0=5, dtick=1),
        yaxis=dict(title="Total Low-Cash ATM-Days (59-Day Period)"),
        legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98)
    )
    st.plotly_chart(fig_sens, use_container_width=True)

    # 4. Transparent Analysis of the Honest Negative Case at N=5
    st.markdown("<div class='dss-card-title'>⚠️ Honest Scientific Finding: The N=5 Bottleneck Failure Mode</div>", unsafe_allow_html=True)
    
    warn_col1, warn_col2 = st.columns([1.6, 1.0])
    with warn_col1:
        st.warning("""
        **Why the Model-Driven Strategy Fails at Very Tight Capacity (N = 5):**
        - At **N = 5**, the model-driven policy produces **1,849 low-cash days vs 1,712 for the fixed schedule (an 8% deficit)**.
        - **Root Operational Mechanism:** When armored courier capacity is severely constrained, ranking purely by *"highest risk today"* causes the algorithm to visit the **same small cluster of high-volume urban ATMs over and over again**.
        - Meanwhile, dozens of moderate-velocity machines slowly drifting toward stockout never quite breach the daily Top-5 threshold. They are **starved of visits** until they run dry.
        - The naive fixed schedule, despite having no machine learning, guarantees that every single ATM eventually receives a replenishment visit every 14 days, preventing systematic starvation.
        """)
    with warn_col2:
        st.info("""
        **Executive Recommendation — The Hybrid Policy:**
        - Below N <= 6, pure risk ranking should **not** be deployed autonomously.
        - Operations should adopt a **Hybrid Policy**:
          1. Allocate a baseline rotation floor (e.g. 2 visits) to guarantee turnaround.
          2. Direct remaining capacity (e.g. 3 visits) using model-driven risk ranking.
        - At N >= 8, the model-driven strategy decisively wins, reducing low-cash days by **25% to 69%**.
        """)

    st.markdown("---")

    # 5. Full Scenario Matrix Table
    st.markdown("<div class='dss-card-title'>📊 Complete Out-of-Sample Scenario Matrix</div>", unsafe_allow_html=True)
    
    st.dataframe(
        BACKTEST_BENCHMARK_RESULTS,
        column_config={
            "Reduction %": st.column_config.NumberColumn(
                "Reduction %",
                format="%.1f%%"
            )
        },
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()
