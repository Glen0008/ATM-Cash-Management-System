"""
Page 6: Model Performance & Validation
Academic rigor, empirical model validation, and comparative benchmarks directly from the notebook.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.styling import (
    inject_custom_css, render_header, render_kpi,
    apply_chart_theme, COLOR_PRIMARY_NAVY, COLOR_ACCENT_BLUE, COLOR_HIGH
)
from utils.data_loader import load_atm_data, render_global_sidebar
from utils.models_engine import (
    NOTEBOOK_FORECASTING_METRICS,
    NOTEBOOK_CLASSIFICATION_METRICS,
    get_feature_importances,
    load_models,
    prepare_features_for_inference
)

def main():
    st.set_page_config(
        page_title="Model Performance | ATM Cash DSS",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    df = load_atm_data()
    _ = render_global_sidebar(df)

    render_header(
        title="Model Performance & Empirical Validation",
        subtitle="Forecasting accuracy, classification discrimination, feature importance, and diagnostic benchmarks",
        badge="Model Validation"
    )

    tab_fc, tab_clf, tab_imp = st.tabs([
        "📈 Withdrawal Forecasting Benchmarks",
        "🎯 Low-Cash Classification Evaluation",
        "🧠 Feature Importance & Interpretability"
    ])

    # TAB 1: FORECASTING BENCHMARKS
    with tab_fc:
        st.markdown("<div class='dss-card-title'>Demand Forecasting Model Comparisons</div>", unsafe_allow_html=True)
        st.caption("Evaluated out-of-sample on held-out test data (last 60 days of dataset).")

        fc_summary = []
        for model_name, m_data in NOTEBOOK_FORECASTING_METRICS.items():
            fc_summary.append({
                "Model / Baseline": model_name,
                "MAE (₹)": f"₹{m_data['MAE']:,.0f}",
                "RMSE (₹)": f"₹{m_data['RMSE']:,.0f}",
                "MAPE": m_data['MAPE'],
                "R²": f"{m_data['R²']:.3f}" if isinstance(m_data['R²'], float) else m_data['R²'],
                "Description": m_data['Description']
            })

        st.dataframe(pd.DataFrame(fc_summary), use_container_width=True, hide_index=True)

        st.markdown("#### Actual vs Predicted Withdrawals (Test Period)")
        st.caption("Inspect daily actual withdrawals against the pooled XGBoost regressor for any ATM in the network.")

        models, meta = load_models()
        atm_list = sorted(df['atm_id'].unique().tolist())
        target_atm = st.selectbox("Select ATM for Forecast Verification:", options=atm_list, index=atm_list.index('ATM0017') if 'ATM0017' in atm_list else 0)

        # Generate test period comparison for target ATM
        cutoff_date = pd.to_datetime(meta.get('cutoff_date', '2024-10-31'))
        atm_test = df[(df['atm_id'] == target_atm) & (df['transaction_date'] > cutoff_date)].copy()

        if not atm_test.empty and 'forecasting' in models:
            enc_test = prepare_features_for_inference(atm_test, meta)
            fc_features = meta.get('fc_features', [
                'withdrawal_lag_1d', 'withdrawal_lag_7d', 'withdrawal_roll7_mean',
                'is_weekend', 'is_holiday', 'day_of_month', 'atm_id_code', 'loc_code', 'city_code'
            ])
            for f in fc_features:
                if f in enc_test.columns:
                    enc_test[f] = enc_test[f].fillna(enc_test[f].median())

            atm_test['predicted_withdrawal'] = models['forecasting'].predict(enc_test[fc_features])

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=atm_test['transaction_date'],
                y=atm_test['withdrawal_amount'],
                mode='lines+markers',
                name='Actual Withdrawal (₹)',
                line=dict(color='#0F172A', width=2)
            ))
            fig_fc.add_trace(go.Scatter(
                x=atm_test['transaction_date'],
                y=atm_test['predicted_withdrawal'],
                mode='lines',
                name='XGBoost Predicted (₹)',
                line=dict(color='#2563EB', width=2.5, dash='dash')
            ))
            fig_fc = apply_chart_theme(fig_fc, title=f"{target_atm} Test Set: Actual vs Predicted Demand", height=350)
            fig_fc.update_layout(yaxis_title="Withdrawals (₹)", hovermode="x unified")
            st.plotly_chart(fig_fc, use_container_width=True)

        with st.expander("🔍 Why Does the R² Ceiling Exist (~0.30)? (Ablation Findings)", expanded=False):
            st.markdown("""
            **Empirical Finding from Phase 5 Ablation Experiments:**
            - **High Idiosyncratic Noise:** Daily ATM withdrawals are inherently noisy at the individual machine level due to erratic foot traffic and non-deterministic transaction sizes.
            - **Static ATM Scale:** A significant fraction of the explainable variance simply reflects *which ATM* is being measured (Rural vs high-traffic Urban), rather than daily temporal fluctuations.
            - **Weekly Aggregation:** When daily data is aggregated to a weekly cadence, noise cancels out and R² jumps significantly.
            - **Operational Implication:** Because day-to-day point forecasting carries inherent uncertainty, operations should rely on **risk-based prioritization** (probabilistic classification) rather than pretending point forecasts are exact down to the rupee.
            """)

    # TAB 2: CLASSIFICATION EVALUATION
    with tab_clf:
        st.markdown("<div class='dss-card-title'>Low-Cash Alert Classification Metrics</div>", unsafe_allow_html=True)
        st.caption("Evaluated on rare-event targets: `low_cash_next_1d` (prevalence ~1-2%) and `low_cash_next_3d` (prevalence ~3-5%).")

        clf_rows = []
        for model_key, metrics in NOTEBOOK_CLASSIFICATION_METRICS.items():
            clf_rows.append({
                "Model & Horizon": model_key,
                "Precision": f"{metrics['Precision']:.3f}",
                "Recall": f"{metrics['Recall']:.3f}",
                "F1 Score": f"{metrics['F1']:.3f}",
                "PR-AUC": f"{metrics['PR-AUC']:.3f}",
                "ROC-AUC": f"{metrics['ROC-AUC']:.3f}"
            })

        st.dataframe(pd.DataFrame(clf_rows), use_container_width=True, hide_index=True)

        st.markdown("#### Metric Comparison: Logistic Regression vs XGBoost")
        comp_df = pd.DataFrame(NOTEBOOK_CLASSIFICATION_METRICS).T.reset_index()
        comp_df.rename(columns={'index': 'Model'}, inplace=True)

        # Plot PR-AUC and Recall side-by-side
        fig_clf_bar = px.bar(
            comp_df,
            x='Model',
            y=['Recall', 'PR-AUC', 'ROC-AUC'],
            barmode='group',
            labels={'value': 'Score', 'variable': 'Evaluation Metric'},
            color_discrete_sequence=['#2563EB', '#059669', '#D97706']
        )
        fig_clf_bar = apply_chart_theme(fig_clf_bar, title="Discriminative Power Across Horizons", height=350)
        st.plotly_chart(fig_clf_bar, use_container_width=True)

        st.info("""
        **Methodological Integrity Note:**
        Standard **Accuracy** is intentionally excluded because in an extreme class imbalance setting (97%+ negative days), a trivial model predicting 'healthy' 100% of the time achieves 97% accuracy while catching **zero** real alerts. We prioritize **PR-AUC**, **Recall**, and **ROC-AUC** as mathematically sound evaluation criteria.
        """)

    # TAB 3: FEATURE IMPORTANCE
    with tab_imp:
        st.markdown("<div class='dss-card-title'>Feature Importance & Driver Breakdown</div>", unsafe_allow_html=True)
        st.caption("Relative weight assigned by the gradient-boosted decision trees in predicting low-cash status within 3 days.")

        imp_df = get_feature_importances()
        fig_feat = px.bar(
            imp_df,
            x='Importance',
            y='Feature',
            orientation='h',
            color='Importance',
            color_continuous_scale="Blues",
            labels={'Importance': 'Relative Gain (Weight)', 'Feature': 'Predictor Variable'}
        )
        fig_feat = apply_chart_theme(fig_feat, title="XGBoost Feature Importance (3-Day Horizon)", height=380)
        fig_feat.update_layout(showlegend=False)
        st.plotly_chart(fig_feat, use_container_width=True)

        st.markdown("""
        **Core Insights on Model Behavior:**
        1. **`pct_capacity_eod` (Current Cash Level):** Dominates the decision boundary. If an ATM is already depleted, its probability of reaching critical threshold in 1–3 days is fundamentally elevated.
        2. **`days_since_replenishment`:** The second most powerful signal. Every elapsed day without a cash delivery increases the cumulative withdrawal exposure.
        3. **`withdrawal_roll7_mean`:** Captures the velocity of local footfall, scaling urgency for busy city-center locations.
        
        > **Academic Transparency:** Feature importance reflects model reliance across tree splits and does not establish independent causality.
        """)

if __name__ == "__main__":
    main()
