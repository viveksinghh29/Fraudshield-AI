"""
Synthetic dataset generator — produces a CSV matching the exact schema
of the Kaggle Credit Card Fraud Detection dataset (Time, Amount,
V1-V28, Class), with realistic-ish statistical properties (heavily
imbalanced, right-skewed Amount, PCA-like V-features).

This is NOT a substitute for the real dataset. It exists purely so the
pipeline (data_loader -> EDA -> cleaning -> feature engineering ->
split -> SMOTE) can be run, tested, and verified end-to-end in this
environment, which has no network access to Kaggle. Point `train.py`
(Phase 6) at the real `creditcard.csv` for actual model training --
swap the --input path, nothing else changes, since the loader
validates on schema, not on file identity.

Usage:
    python -m ml_research.generate_synthetic_dataset --rows 20000 --output ml_research/data/synthetic_creditcard.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_STATE = 42


def generate_synthetic_dataset(n_rows: int = 20_000, fraud_rate: float = 0.0017) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)

    n_fraud = max(1, int(n_rows * fraud_rate))
    n_legit = n_rows - n_fraud

    # ---- Time: seconds elapsed across a simulated 2-day capture window ----
    time_span_seconds = 2 * 24 * 3600
    time = rng.uniform(0, time_span_seconds, n_rows)

    # ---- Amount: log-normal (heavily right-skewed, like real transaction amounts) ----
    amount_legit = rng.lognormal(mean=3.0, sigma=1.2, size=n_legit)
    amount_fraud = rng.lognormal(mean=4.2, sigma=1.6, size=n_fraud)  # fraud skews larger
    amount = np.concatenate([amount_legit, amount_fraud])

    # ---- V1-V28: PCA-like components, standard-normal for legitimate,
    #      shifted mean + higher variance for fraud (mimics separable structure) ----
    n_features = 28
    v_legit = rng.normal(loc=0.0, scale=1.0, size=(n_legit, n_features))
    v_fraud = rng.normal(loc=0.8, scale=2.2, size=(n_fraud, n_features))
    v_features = np.vstack([v_legit, v_fraud])

    labels = np.concatenate([np.zeros(n_legit, dtype=int), np.ones(n_fraud, dtype=int)])

    df = pd.DataFrame(v_features, columns=[f"V{i}" for i in range(1, n_features + 1)])
    df.insert(0, "Time", time)
    df["Amount"] = np.round(amount, 2)
    df["Class"] = labels

    # Shuffle so fraud rows aren't all clustered at the end
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    df["Time"] = df["Time"].sort_values().reset_index(drop=True)  # Time should be roughly monotonic

    return df


def _main() -> None:
    parser = argparse.ArgumentParser(description="Generate a schema-matched synthetic fraud dataset")
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--fraud-rate", type=float, default=0.0017)
    parser.add_argument("--output", default="ml_research/data/synthetic_creditcard.csv")
    args = parser.parse_args()

    df = generate_synthetic_dataset(n_rows=args.rows, fraud_rate=args.fraud_rate)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Synthetic dataset written to {output_path}")
    print(f"  Rows: {len(df)}, Fraud: {int(df['Class'].sum())} ({100 * df['Class'].mean():.3f}%)")


if __name__ == "__main__":
    _main()
