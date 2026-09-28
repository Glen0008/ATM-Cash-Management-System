"""
Page 3: Demand & Cash Analytics
Transforms notebook EDA into a fully interactive diagnostic and exploratory suite.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.styling import (
    inject_custom_css, render_header, render_kpi,
    format_currency_inr, apply_chart_theme,
    COLOR_PRIMARY_NAVY, COLOR_ACCENT_BLUE, COLOR_URGENT,
    COLOR_HIGH, COLOR_MODERATE, COLOR_LOW
)
from utils.data_loader import load_atm_data, render_global_sidebar, filter_dataset

def main():
    st.set_page_config(
        page_title="Demand Analytics | ATM Cash DSS",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    filters = render_global_sidebar(df)

    render_header(
        title="Demand & Cash Flow Analytics",
        subtitle="Exploratory diagnostics, calendar cycles, salary waves, and holiday effects across the ATM fleet",
        badge="Analytics Engine"
    )

    # Filtered dataset (ignoring single-day filter for time-series EDA)
    df_filtered = filter_dataset(df, filters, apply_date=False)
    if df_filtered.empty:
        st.warning("⚠️ No data available for the active filters. Please adjust city/location filters.")
        return

    # Section A: Withdrawal Trends Over Time
    st.markdown("<div class='dss-card-title'>📈 Macro Withdrawal & Cash Trends Over Time</div>", unsafe_allow_html=True)
    
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.2, 1.2, 2.0])
    with ctrl_col1:
        metric_choice = st.selectbox(
            "Select Demand Metric:",
            options=["Total Withdrawal (₹)", "Average Withdrawal (₹)", "Transaction Count", "Cash Remaining (₹)"],
            index=0
        )
    with ctrl_col2:
        agg_choice = st.selectbox(
            "Time Aggregation:",
            options=["Daily", "Weekly", "Monthly"],
            index=0
        )
    with ctrl_col3:
        st.caption("Aggregates transactions across all ATMs matching your active sidebar filters.")

    # Prepare time-series aggregation
    ts_data = df_filtered.copy()
    if agg_choice == "Daily":
        ts_data['period'] = ts_data['transaction_date']
    elif agg_choice == "Weekly":
        ts_data['period'] = ts_data['transaction_date'].dt.to_period('W').dt.start_time
    else:
        ts_data['period'] = ts_data['transaction_date'].dt.to_period('M').dt.start_time

    if metric_choice == "Total Withdrawal (₹)":
        ts_agg = ts_data.groupby('period')['withdrawal_amount'].sum().reset_index()
        y_col = 'withdrawal_amount'
        y_label = "Total Withdrawn (₹)"
        chart_color = "#2563EB"
    elif metric_choice == "Average Withdrawal (₹)":
        ts_agg = ts_data.groupby('period')['withdrawal_amount'].mean().reset_index()
        y_col = 'withdrawal_amount'
        y_label = "Average Withdrawal per ATM (₹)"
        chart_color = "#059669"
    elif metric_choice == "Transaction Count":
        ts_agg = ts_data.groupby('period')['withdrawal_count'].sum().reset_index()
        y_col = 'withdrawal_count'
        y_label = "Total Customer Withdrawals"
        chart_color = "#D97706"
    else:
        ts_agg = ts_data.groupby('period')['cash_eod'].mean().reset_index()
        y_col = 'cash_eod'
        y_label = "Average Cash Remaining (₹)"
        chart_color = "#7C3AED"

    fig_ts = px.line(
        ts_agg,
        x='period',
        y=y_col,
        labels={'period': 'Date', y_col: y_label},
        title=f"{metric_choice} ({agg_choice} Aggregation)"
    )
    fig_ts.update_traces(line=dict(color=chart_color, width=2.5))
    fig_ts = apply_chart_theme(fig_ts, height=360)
    fig_ts.update_layout(xaxis=dict(rangeslider=dict(visible=True), type="date"))
    st.plotly_chart(fig_ts, use_container_width=True)

    st.markdown("---")

    # Section B & C: Day of Week & Salary Day Effect
    col_dow, col_salary = st.columns(2)

    with col_dow:
        st.markdown("<div class='dss-card-title'>📅 Day-of-Week Distribution</div>", unsafe_allow_html=True)
        dow_metric = st.selectbox(
            "Metric for Day-of-Week:",
            options=["Average Daily Withdrawal (₹)", "Total Withdrawal (₹)", "Average Transaction Count"],
            index=0,
            key="dow_metric"
        )
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if dow_metric == "Average Daily Withdrawal (₹)":
            dow_df = df_filtered.groupby('day_of_week')['withdrawal_amount'].mean().reindex(days_order).reset_index()
            y_dow = 'withdrawal_amount'
        elif dow_metric == "Total Withdrawal (₹)":
            dow_df = df_filtered.groupby('day_of_week')['withdrawal_amount'].sum().reindex(days_order).reset_index()
            y_dow = 'withdrawal_amount'
        else:
            dow_df = df_filtered.groupby('day_of_week')['withdrawal_count'].mean().reindex(days_order).reset_index()
            y_dow = 'withdrawal_count'

        colors_dow = ['#4C72B0' if d not in ['Saturday', 'Sunday'] else '#E28743' for d in dow_df['day_of_week']]
        fig_dow = go.Figure(go.Bar(
            x=dow_df['day_of_week'],
            y=dow_df[y_dow],
            marker_color=colors_dow
        ))
        fig_dow = apply_chart_theme(fig_dow, title="Demand by Day of Week (Weekends Highlighted)", height=340)
        fig_dow.update_layout(xaxis_title="Day of Week", yaxis_title=dow_metric)
        st.plotly_chart(fig_dow, use_container_width=True)

    with col_salary:
        st.markdown("<div class='dss-card-title'>💰 Day-of-Month & Salary-Period Effect</div>", unsafe_allow_html=True)
        st.caption("Notebook Insight: Days 1–3 display a notable spike in customer withdrawal volume driven by payroll cycles.")
        
        dom_agg = df_filtered.groupby('day_of_month')['withdrawal_amount'].mean().reset_index()
        dom_agg = dom_agg.sort_values('day_of_month')

        # Highlight days 1-3 with distinct red/accent color
        bar_colors = ['#DC2626' if d in [1, 2, 3] else '#2563EB' for d in dom_agg['day_of_month']]
        
        fig_dom = go.Figure(go.Bar(
            x=dom_agg['day_of_month'],
            y=dom_agg['withdrawal_amount'],
            marker_color=bar_colors,
            name='Daily Avg Withdrawal'
        ))
        fig_dom.add_vrect(
            x0=0.5, x1=3.5,
            fillcolor="rgba(220, 38, 38, 0.12)",
            layer="below", line_width=1, line_color="#DC2626",
            annotation_text="Salary Period (Days 1–3)",
            annotation_position="top left"
        )
        fig_dom = apply_chart_theme(fig_dom, title="Average Daily Withdrawal by Day of Month", height=340)
        fig_dom.update_layout(xaxis_title="Day of Month (1 - 31)", yaxis_title="Average Daily Withdrawal (₹)")
        st.plotly_chart(fig_dom, use_container_width=True)

    st.markdown("---")

    # Section D: Holiday Effect Analysis
    st.markdown("<div class='dss-card-title'>🎉 Holiday vs Non-Holiday Analysis</div>", unsafe_allow_html=True)
    st.caption("Critical Operational Nuance: Average withdrawal size per transaction may remain steady, but aggregate daily withdrawal and footfall shift substantially on holidays.")

    hol_agg = df_filtered.groupby('is_holiday').agg(
        avg_total_daily_wd=('withdrawal_amount', 'mean'),
        avg_txn_count=('withdrawal_count', 'mean'),
        total_days=('transaction_date', 'nunique')
    ).reset_index()
    hol_agg['Category'] = hol_agg['is_holiday'].map({0: 'Non-Holiday', 1: 'Bank / Public Holiday'})

    hcol1, hcol2, hcol3 = st.columns([1, 1, 1.4])
    non_hol_avg = hol_agg.loc[hol_agg['is_holiday'] == 0, 'avg_total_daily_wd'].values[0] if (hol_agg['is_holiday'] == 0).any() else 0
    hol_avg = hol_agg.loc[hol_agg['is_holiday'] == 1, 'avg_total_daily_wd'].values[0] if (hol_agg['is_holiday'] == 1).any() else 0
    diff_pct = ((hol_avg - non_hol_avg) / non_hol_avg) * 100 if non_hol_avg > 0 else 0

    with hcol1:
        render_kpi("Non-Holiday Daily Avg", format_currency_inr(non_hol_avg), "Standard operational days")
    with hcol2:
        render_kpi("Holiday Daily Avg", format_currency_inr(hol_avg), f"Variance: {diff_pct:+.1f}% vs normal", COLOR_HIGH if diff_pct < 0 else COLOR_LOW)
    with hcol3:
        fig_hol = px.bar(
            hol_agg,
            x='Category',
            y='avg_total_daily_wd',
            color='Category',
            color_discrete_map={'Non-Holiday': '#2563EB', 'Bank / Public Holiday': '#DC2626'},
            labels={'avg_total_daily_wd': 'Avg Daily Withdrawal (₹)'}
        )
        fig_hol = apply_chart_theme(fig_hol, height=220)
        fig_hol.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_hol, use_container_width=True)

    st.markdown("---")

    # Section E: Seasonality Heatmap
    st.markdown("<div class='dss-card-title'>🗓️ Calendar Seasonality Heatmap (Month × Day of Week)</div>", unsafe_allow_html=True)
    
    df_filtered['month_name'] = df_filtered['transaction_date'].dt.strftime('%B')
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    heat_pivot = df_filtered.pivot_table(
        index='month_name',
        columns='day_of_week',
        values='withdrawal_amount',
        aggfunc='mean'
    ).reindex(index=month_order, columns=days_order)

    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale="Blues",
        labels=dict(x="Day of Week", y="Month", color="Avg Withdrawal (₹)"),
        text_auto=".0f"
    )
    fig_heat = apply_chart_theme(fig_heat, title="Average Daily Withdrawal (₹) by Month and Weekday", height=420)
    fig_heat.update_layout(coloraxis_colorbar=dict(title="INR (₹)"))
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # Section F: Multi-ATM Comparison
    st.markdown("<div class='dss-card-title'>👥 Multi-ATM Demand Comparison</div>", unsafe_allow_html=True)
    atm_choices = st.multiselect(
        "Select 2 to 5 ATMs for Comparative Velocity Analysis:",
        options=sorted(df['atm_id'].unique().tolist()),
        default=['ATM0017', 'ATM0042', 'ATM0001']
    )

    if atm_choices:
        compare_df = df[df['atm_id'].isin(atm_choices)].copy()
        compare_df = compare_df.sort_values('transaction_date')
        
        # Group by week for cleaner multi-line plot
        compare_df['week'] = compare_df['transaction_date'].dt.to_period('W').dt.start_time
        comp_agg = compare_df.groupby(['week', 'atm_id'])['withdrawal_amount'].mean().reset_index()

        fig_comp = px.line(
            comp_agg,
            x='week',
            y='withdrawal_amount',
            color='atm_id',
            labels={'week': 'Week', 'withdrawal_amount': 'Avg Weekly Withdrawal (₹)', 'atm_id': 'ATM ID'}
        )
        fig_comp = apply_chart_theme(fig_comp, title="Comparative Withdrawal Trajectories (Weekly Moving Average)", height=360)
        st.plotly_chart(fig_comp, use_container_width=True)

if __name__ == "__main__":
    main()
