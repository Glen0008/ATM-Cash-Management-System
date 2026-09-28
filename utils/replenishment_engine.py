"""
Replenishment Planning and Refill Calculation Engine.
Directly implements Section 6.6 & 6.7 of ATM_Phase3_EDA (9).ipynb.
"""

import pandas as pd
import numpy as np

DEFAULT_TARGET_FILL = 0.90  # 90% capacity refill rule

def calculate_replenishment_needs(
    snapshot_df: pd.DataFrame,
    target_fill_pct: float = DEFAULT_TARGET_FILL
) -> pd.DataFrame:
    """
    Computes recommended refill amount and demand sanity checks for all ATMs.
    Formula:
        target_cash = atm_cash_capacity * target_fill_pct
        recommended_refill = max(0, target_cash - current_cash)
        refill_vs_weekly_demand = recommended_refill / (withdrawal_roll7_mean * 7 + 1)
    """
    df = snapshot_df.copy()
    
    df['current_cash'] = df['cash_eod']
    df['target_cash'] = df['atm_cash_capacity'] * target_fill_pct
    df['recommended_refill_amount'] = (df['target_cash'] - df['current_cash']).clip(lower=0)

    # Sanity check: how many days of average demand does this refill represent?
    roll7 = df['withdrawal_roll7_mean'].fillna(df['withdrawal_amount']).clip(lower=1)
    df['refill_vs_weekly_demand'] = df['recommended_refill_amount'] / (roll7 * 7 + 1)
    df['equivalent_demand_days'] = df['recommended_refill_amount'] / roll7

    return df

def generate_replenishment_plan(
    snapshot_df: pd.DataFrame,
    daily_capacity: int = 12,
    target_fill_pct: float = DEFAULT_TARGET_FILL
) -> pd.DataFrame:
    """
    Generates operational manifest of top N ATMs prioritized by risk.
    Prioritizes ATMs by priority_score (3-day low cash risk) and flags next-day urgency.
    """
    df = calculate_replenishment_needs(snapshot_df, target_fill_pct)

    # Rank by priority_score
    manifest = df.sort_values('priority_score', ascending=False).reset_index(drop=True)
    manifest['servicing_priority'] = manifest.index + 1
    
    # Filter to top N capacity
    top_n = manifest.head(daily_capacity).copy()
    
    return top_n

def single_atm_refill_calculator(
    current_cash: float,
    capacity: float,
    roll7_mean: float,
    target_pct: float = 0.90
) -> dict:
    """Calculates refill details for a single selected ATM with demand sanity checks."""
    target_cash = capacity * target_pct
    refill = max(0.0, target_cash - current_cash)
    daily_demand = max(1.0, roll7_mean)
    equiv_days = refill / daily_demand
    equiv_weeks = refill / (daily_demand * 7)

    return {
        "current_cash": current_cash,
        "capacity": capacity,
        "target_pct": target_pct,
        "target_cash": target_cash,
        "recommended_refill": refill,
        "roll7_mean": daily_demand,
        "equivalent_days": equiv_days,
        "equivalent_weeks": equiv_weeks
    }
