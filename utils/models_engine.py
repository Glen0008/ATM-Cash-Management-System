"""
Model Engine for ATM Cash Management DSS.
Handles model loading, inference, feature importance, and academic evaluation benchmarks.
"""

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

# Hard-coded ground-truth benchmark metrics from ATM_Phase3_EDA (9).ipynb
NOTEBOOK_FORECASTING_METRICS = {
    "Naive: Same Day Last Week": {
        "MAE": 11196.0,
        "RMSE": 14780.0,
        "MAPE": "—",
        "R²": "—",
        "Description": "Simple lag baseline: repeats withdrawal amount from exactly 7 days prior."
    },
    "Naive: 7-Day Rolling Average": {
        "MAE": 8591.0,
        "RMSE": 11278.0,
        "MAPE": "—",
        "R²": "—",
        "Description": "Smooths day-to-day noise using trailing 7-day moving average."
    },
    "Pooled XGBoost (All 60 ATMs)": {
        "MAE": 7793.0,
        "RMSE": 10081.0,
        "MAPE": "82.4%",
        "R²": 0.297,
        "Description": "Global gradient boosting regressor incorporating lag, rolling, calendar, and location codes."
    },
    "ARIMA(2,1,2) Benchmark (ATM0017)": {
        "MAE": 10746.0,
        "RMSE": 13838.0,
        "MAPE": "—",
        "R²": "—",
        "Description": "Classical univariate ARIMA benchmark fit to single representative ATM (ATM0017)."
    }
}

NOTEBOOK_CLASSIFICATION_METRICS = {
    "low_cash_next_1d — LogReg (Class-Weighted)": {
        "Precision": 0.031, "Recall": 0.848, "F1": 0.060, "PR-AUC": 0.047, "ROC-AUC": 0.879
    },
    "low_cash_next_1d — XGBoost": {
        "Precision": 0.032, "Recall": 0.667, "F1": 0.062, "PR-AUC": 0.066, "ROC-AUC": 0.875
    },
    "low_cash_next_3d — LogReg (Class-Weighted)": {
        "Precision": 0.046, "Recall": 0.645, "F1": 0.086, "PR-AUC": 0.074, "ROC-AUC": 0.686
    },
    "low_cash_next_3d — XGBoost": {
        "Precision": 0.108, "Recall": 0.796, "F1": 0.190, "PR-AUC": 0.527, "ROC-AUC": 0.917
    }
}

@st.cache_resource(show_spinner=False)
def load_models():
    """Loads saved XGBoost classifiers and metadata."""
    models = {}
    meta = {}
    
    meta_path = "models/model_metadata.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)

    for target in ['low_cash_next_1d', 'low_cash_next_3d']:
        path = f"models/{target}_xgb.json"
        if os.path.exists(path):
            m = xgb.XGBClassifier()
            m.load_model(path)
            models[target] = m

    fc_path = "models/forecasting_xgb.json"
    if os.path.exists(fc_path):
        m_fc = xgb.XGBRegressor()
        m_fc.load_model(fc_path)
        models['forecasting'] = m_fc

    return models, meta

def prepare_features_for_inference(df: pd.DataFrame, meta: dict):
    """Encodes categorical fields according to trained model classes."""
    data = df.copy()
    
    # Label encoding for ATM ID, location type, city
    atm_classes = meta.get('atm_classes', sorted(data['atm_id'].unique().tolist()))
    loc_classes = meta.get('loc_classes', sorted(data['atm_location_type'].unique().tolist()))
    city_classes = meta.get('city_classes', sorted(data['city'].unique().tolist()))

    data['atm_id_code'] = data['atm_id'].apply(lambda x: atm_classes.index(x) if x in atm_classes else 0)
    data['loc_code'] = data['atm_location_type'].apply(lambda x: loc_classes.index(x) if x in loc_classes else 0)
    data['city_code'] = data['city'].apply(lambda x: city_classes.index(x) if x in city_classes else 0)

    return data

@st.cache_data(show_spinner=False)
def get_snapshot_predictions(df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    """
    Computes model predictions and priority scores for all ATMs on the specified date.
    Returns enriched dataframe with priority_score, urgent_1d_score, and risk_level.
    """
    models, meta = load_models()
    
    snapshot = df[df['transaction_date'] == date].copy()
    if snapshot.empty:
        return snapshot

    clf_features = meta.get('clf_features', [
        'pct_capacity_eod', 'withdrawal_lag_1d', 'withdrawal_roll7_mean', 'days_since_replenishment',
        'is_weekend', 'is_holiday', 'day_of_month', 'atm_id_code', 'loc_code', 'city_code'
    ])

    encoded_snapshot = prepare_features_for_inference(snapshot, meta)

    # Impute missing lags if any
    for col in ['withdrawal_lag_1d', 'withdrawal_roll7_mean', 'pct_capacity_eod']:
        if col in encoded_snapshot.columns:
            encoded_snapshot[col] = encoded_snapshot[col].fillna(encoded_snapshot[col].median())

    if 'low_cash_next_3d' in models:
        snapshot['priority_score'] = models['low_cash_next_3d'].predict_proba(encoded_snapshot[clf_features])[:, 1]
    else:
        # Fallback if model not loaded
        snapshot['priority_score'] = 1.0 - (snapshot['pct_capacity_eod'] / 100.0).clip(0, 1)

    if 'low_cash_next_1d' in models:
        snapshot['urgent_1d_score'] = models['low_cash_next_1d'].predict_proba(encoded_snapshot[clf_features])[:, 1]
    else:
        snapshot['urgent_1d_score'] = snapshot['priority_score'] * 0.7

    # Assign Risk Categories based on notebook definition
    # URGENT_THRESHOLD = 0.3 for 1-day risk
    # Priority > 0.5 for 3-day risk
    def categorize_risk(row):
        if row['urgent_1d_score'] > 0.30:
            return "Urgent"
        elif row['priority_score'] > 0.50:
            return "High"
        elif row['priority_score'] >= 0.20:
            return "Moderate"
        else:
            return "Low"

    snapshot['risk_level'] = snapshot.apply(categorize_risk, axis=1)
    snapshot['is_urgent'] = snapshot['urgent_1d_score'] > 0.30

    # Sort descending by priority score and assign rank
    snapshot = snapshot.sort_values('priority_score', ascending=False).reset_index(drop=True)
    snapshot['priority_rank'] = snapshot.index + 1

    return snapshot

def get_feature_importances() -> pd.DataFrame:
    """Returns classification feature importance from the trained XGBoost model."""
    models, meta = load_models()
    clf_features = meta.get('clf_features', [
        'pct_capacity_eod', 'withdrawal_lag_1d', 'withdrawal_roll7_mean', 'days_since_replenishment',
        'is_weekend', 'is_holiday', 'day_of_month', 'atm_id_code', 'loc_code', 'city_code'
    ])

    friendly_names = {
        'pct_capacity_eod': "Current Cash % (pct_capacity_eod)",
        'days_since_replenishment': "Days Since Refill (days_since_replenishment)",
        'withdrawal_roll7_mean': "7-Day Avg Withdrawal (withdrawal_roll7_mean)",
        'withdrawal_lag_1d': "Yesterday's Withdrawal (withdrawal_lag_1d)",
        'loc_code': "Location Type (Urban / Rural / Semi-Urban)",
        'atm_id_code': "ATM Fixed Identity (Scale Effect)",
        'city_code': "City Code",
        'day_of_month': "Day of Month (Salary Window)",
        'is_weekend': "Weekend Flag",
        'is_holiday': "Holiday Flag"
    }

    if 'low_cash_next_3d' in models:
        raw_imp = models['low_cash_next_3d'].feature_importances_
        df_imp = pd.DataFrame({
            'Feature': [friendly_names.get(f, f) for f in clf_features],
            'RawFeature': clf_features,
            'Importance': raw_imp
        }).sort_values('Importance', ascending=True)
        return df_imp
    else:
        # Ground truth fallback from notebook Figure in cell 127
        return pd.DataFrame({
            'Feature': [
                "Current Cash % (pct_capacity_eod)",
                "Days Since Refill (days_since_replenishment)",
                "7-Day Avg Withdrawal (withdrawal_roll7_mean)",
                "Yesterday's Withdrawal (withdrawal_lag_1d)",
                "Location Type (loc_code)",
                "ATM Fixed Identity",
                "City Code",
                "Day of Month",
                "Weekend Flag",
                "Holiday Flag"
            ],
            'Importance': [0.46, 0.24, 0.11, 0.08, 0.04, 0.03, 0.02, 0.01, 0.005, 0.005]
        }).sort_values('Importance', ascending=True)
