"""
Data splitting.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from app.ml.pipeline.feature_engineering import get_model_feature_columns

RANDOM_STATE = 42


def three_way_split_raw(
    df: pd.DataFrame, *, test_size: float = 0.2, val_size: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the raw (pre-cleaning, pre-engineering) dataframe into
    (train_df, val_df, test_df), stratified on Class at each split.

    `val_size` is expressed as a fraction of the ORIGINAL dataframe
    (not of the remaining train+val portion), so e.g. test_size=0.2,
    val_size=0.15 yields roughly 65% train / 15% val / 20% test.
    """
    train_val_df, test_df = train_test_split(
        df, test_size=test_size, random_state=RANDOM_STATE, stratify=df["Class"]
    )

    # val_size was expressed relative to the full dataset; convert it to
    # a fraction of the remaining train_val_df before the second split.
    relative_val_size = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=relative_val_size,
        random_state=RANDOM_STATE,
        stratify=train_val_df["Class"],
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def extract_features_and_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Pulls (X, y) out of an already-cleaned, already-engineered
    dataframe, using only the model's declared feature columns
    (get_model_feature_columns()) -- never raw Time/Amount, never the
    outlier flag, never Class itself as a feature.
    """
    feature_columns = get_model_feature_columns()
    missing = set(feature_columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"DataFrame is missing engineered feature columns: {sorted(missing)}. "
            "Run engineer_features() before extracting features."
        )
    return df[feature_columns], df["Class"]
