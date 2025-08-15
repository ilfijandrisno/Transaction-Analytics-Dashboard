
# create_data_dummy.py
# Generate multi-year dummy transactions for the Streamlit dashboard
# Usage (optional): python create_data_dummy.py
# You can tweak parameters in the CONFIG section.

import os
import numpy as np
import pandas as pd
from datetime import datetime

# ===== CONFIG =====
SEED             = 42
START_YEAR       = 2020   # inclusive
N_YEARS          = 6      # 2021..2025
ROWS_TOTAL       = 160_000
FAILED_RATE      = 0.15   # 15% failed
OUT_DIR          = "data"
OUT_FILE         = "transactions_dummy.csv"

CATEGORIES = [
    ("Airtime",              0.30),
    ("Data Bundle",          0.25),
    ("Electricity Prepaid",  0.15),
    ("Water Utility",        0.10),
    ("Postpaid Bills",       0.10),
    ("Micro-Insurance",      0.10),
]
CHANNELS = [
    ("Agent", 0.45),
    ("App",   0.45),
    ("Web",   0.10),
]
REGIONS = [
    ("Zone 1", 0.15), ("Zone 2", 0.15), ("Zone 3", 0.14),
    ("Zone 4", 0.14), ("Zone 5", 0.14), ("Zone 6", 0.14),
    ("Unmapped", 0.14/6),  # kecil
]

FAILURE_REASONS = [
    ("Network Timeout",         0.50),  # sangat dominan
    ("Exceeded Limit",          0.20),
    ("Provider Unreachable",    0.15),
    ("Invalid Account Number",  0.10),
    ("Insufficient Balance",    0.04),
    ("Fraud Suspected",         0.01),  # sangat jarang
]

# Fee rate by channel (base); will be jittered later ±10%
FEE_RATE_BY_CHANNEL = {"Agent": 0.020, "App": 0.028, "Web": 0.024}

# Category factor for GMV scale (relative)
CAT_AMOUNT_FACTOR = {
    "Airtime": 1.00,
    "Data Bundle": 1.10,
    "Electricity Prepaid": 0.95,
    "Water Utility": 0.90,
    "Postpaid Bills": 0.92,
    "Micro-Insurance": 0.70,
}

# Month seasonality (rough): higher in Mar–Apr (Ramadan-ish) & Dec
MONTH_SEASON = {
    1: 0.95,  2: 0.93,  3: 1.08,  4: 1.10,
    5: 1.02,  6: 1.00,  7: 1.04,  8: 1.06,
    9: 1.05, 10: 1.02, 11: 1.06, 12: 1.15
}

# Day-of-week factor (weekend slightly lower)
DOW_FACTOR = {0:1.00, 1:1.00, 2:1.01, 3:1.01, 4:1.02, 5:0.95, 6:0.94}

def _weighted_choice(rng, items):
    labels = [x for x,_ in items]
    probs  = np.array([p for _,p in items], dtype=float)
    probs  = probs / probs.sum()
    return labels, probs

def generate():
    rng = np.random.default_rng(SEED)

    # Dates
    start = f"{START_YEAR}-01-01"
    end   = f"{START_YEAR + N_YEARS - 1}-12-31"
    dates = pd.date_range(start=start, end=end, freq="D")

    # Weighted discrete choices
    cat_labels, cat_probs = _weighted_choice(rng, CATEGORIES)
    ch_labels, ch_probs   = _weighted_choice(rng, CHANNELS)
    rg_labels, rg_probs   = _weighted_choice(rng, REGIONS)
    fr_labels, fr_probs   = _weighted_choice(rng, FAILURE_REASONS)

    n = ROWS_TOTAL
    df = pd.DataFrame({
        "date":    rng.choice(dates, size=n, replace=True),
        "category":rng.choice(cat_labels, size=n, p=cat_probs),
        "channel": rng.choice(ch_labels, size=n, p=ch_probs),
        "region":  rng.choice(rg_labels, size=n, p=rg_probs),
        "user_id": rng.integers(10_000, 19_999, size=n),
    })

    # Amount generation: lognormal base * category * month * dow * year growth
    date_dt = pd.to_datetime(df["date"])
    month = date_dt.dt.month
    dow   = date_dt.dt.dayofweek
    year  = date_dt.dt.year

    base = np.exp(rng.normal(10.2, 0.9, size=n))  # long-tail distribution
    cat_fac = df["category"].map(CAT_AMOUNT_FACTOR).values
    m_fac = np.vectorize(MONTH_SEASON.get)(month)
    d_fac = np.vectorize(DOW_FACTOR.get)(dow)
    yr_growth = 1.0 + 0.07 * (year - START_YEAR)  # ~7% YoY

    amount = base * cat_fac * m_fac * d_fac * yr_growth
    amount = np.clip(amount, 5_000, None).round(0)
    df["amount"] = amount

    # Fee = fee_rate_by_channel * amount with jitter ±10%
    base_rate = df["channel"].map(FEE_RATE_BY_CHANNEL).values
    jitter = rng.uniform(0.9, 1.1, size=n)
    fee_rate = (base_rate * jitter).clip(0.005, 0.08)  # clamp
    df["fee_amount"] = (df["amount"] * fee_rate).round(2)

    # Status & failure_reason
    rnd = rng.random(n)
    df["status"] = np.where(rnd < FAILED_RATE, "FAILED", "SUCCESS")
    fail_idx = df["status"] == "FAILED"
    df["failure_reason"] = ""
    if fail_idx.any():
        df.loc[fail_idx, "failure_reason"] = rng.choice(fr_labels, size=fail_idx.sum(), p=fr_probs)

    # Period columns
    df["year"]    = date_dt.dt.year
    df["month"]   = month
    df["week"]    = date_dt.dt.isocalendar().week.astype(int)
    df["quarter"] = date_dt.dt.quarter

    # Reorder columns
    cols = ["date","category","channel","region","user_id","amount","fee_amount",
            "status","failure_reason","year","month","week","quarter"]
    df = df[cols].sort_values("date").reset_index(drop=True)
    return df

def main():
    df = generate()
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_FILE)
    df.to_csv(out_path, index=False)
    print(f"Saved {out_path}  rows={len(df):,}  years={df['year'].min()}-{df['year'].max()}")

if __name__ == "__main__":
    main()
