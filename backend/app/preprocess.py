from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Tuple, List

FEATURE_COLUMNS: List[str] = ["cpu", "memory", "disk_io", "net_io", "errors"]


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Ensure all expected columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
    return df


def dataframe_to_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    X = df[FEATURE_COLUMNS].astype(float).values
    timestamps = df["timestamp"].astype(str).tolist() if "timestamp" in df else [""] * len(df)
    return X, timestamps


def normalize_features(X: np.ndarray) -> np.ndarray:
    # Simple min-max normalization per column with epsilon for stability
    eps = 1e-9
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    denom = np.where((maxs - mins) < eps, 1.0, (maxs - mins))
    return (X - mins) / denom

