from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest

MODEL_DIR = Path("backend/models_store")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RISK_MODEL_PATH = MODEL_DIR / "risk_rf.joblib"
ANOMALY_MODEL_PATH = MODEL_DIR / "anomaly_if.joblib"


def train_models(X: np.ndarray, y: np.ndarray | None = None) -> Tuple[RandomForestClassifier, IsolationForest]:
    # Risk model (supervised). If y is None, create pseudo labels using heuristics.
    if y is None:
        # Higher cpu/memory/errors increase risk (simple heuristic for demo)
        weights = np.array([0.35, 0.35, 0.1, 0.1, 0.1])
        scores = (X * weights).sum(axis=1)
        thresh = np.quantile(scores, 0.8)
        y = (scores >= thresh).astype(int)

    risk_model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
    risk_model.fit(X, y)

    anomaly_model = IsolationForest(n_estimators=150, contamination=0.1, random_state=42)
    anomaly_model.fit(X)

    joblib.dump(risk_model, RISK_MODEL_PATH)
    joblib.dump(anomaly_model, ANOMALY_MODEL_PATH)
    return risk_model, anomaly_model


def load_models() -> Tuple[RandomForestClassifier, IsolationForest]:
    risk_model = joblib.load(RISK_MODEL_PATH) if RISK_MODEL_PATH.exists() else None
    anomaly_model = joblib.load(ANOMALY_MODEL_PATH) if ANOMALY_MODEL_PATH.exists() else None
    if risk_model is None or anomaly_model is None:
        raise FileNotFoundError("Models not trained yet. Call train first.")
    return risk_model, anomaly_model


def predict(risk_model: RandomForestClassifier, anomaly_model: IsolationForest, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    risk_scores = risk_model.predict_proba(X)[:, 1]
    # IsolationForest: anomaly = -1 is outlier
    anomaly_pred = anomaly_model.predict(X)
    anomaly_flags = (anomaly_pred == -1).astype(int)
    return risk_scores, anomaly_flags

