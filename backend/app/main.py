from __future__ import annotations

import os
from typing import List

import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .schemas import PredictRequest, PredictResponse, AlertsResponse, AlertItem
from .preprocess import dataframe_to_features, normalize_features, load_csv
from .models import train_models, load_models, predict
from .alerts import score_to_priority, recommended_actions, summarize, notify_slack
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus metrics
REQUEST_COUNT = Counter("pdsa_requests_total", "Total API requests", ["endpoint", "method", "status"])
REQUEST_LATENCY = Histogram("pdsa_request_latency_seconds", "Request latency", ["endpoint"]) 
ALERTS_TOTAL = Gauge("pdsa_alerts_total", "Alerts by priority", ["priority"]) 

app = FastAPI(title="Predictive Downtime & Smart Alerts API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/train")
def train(dataset_path: str = os.getenv("TRAIN_DATA", "data/sample_logs.csv")):
    try:
        import time as _t
        start = _t.perf_counter()
        df = load_csv(dataset_path)
        X, _ = dataframe_to_features(df)
        Xn = normalize_features(X)
        train_models(Xn, None)
        REQUEST_COUNT.labels("/train", "POST", 200).inc()
        REQUEST_LATENCY.labels("/train").observe(_t.perf_counter() - start)
        return {"status": "trained", "samples": int(Xn.shape[0])}
    except Exception as exc:
        REQUEST_COUNT.labels("/train", "POST", 400).inc()
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(req: PredictRequest):
    try:
        import time as _t
        start = _t.perf_counter()
        import pandas as pd

        df = pd.DataFrame([r.model_dump() for r in req.records])
        X, _ = dataframe_to_features(df)
        Xn = normalize_features(X)
        risk_model, anomaly_model = load_models()
        risk_scores, anomaly_flags = predict(risk_model, anomaly_model, Xn)
        REQUEST_COUNT.labels("/predict", "POST", 200).inc()
        REQUEST_LATENCY.labels("/predict").observe(_t.perf_counter() - start)
        return PredictResponse(
            risk_scores=list(np.round(risk_scores, 4)),
            anomaly_flags=list(map(int, anomaly_flags.tolist())),
        )
    except FileNotFoundError:
        REQUEST_COUNT.labels("/predict", "POST", 400).inc()
        raise HTTPException(status_code=400, detail="Models not trained. Call /train first.")
    except Exception as exc:
        REQUEST_COUNT.labels("/predict", "POST", 400).inc()
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/alerts", response_model=AlertsResponse)
def alerts(dataset_path: str = os.getenv("ALERTS_DATA", "data/sample_logs.csv")):
    try:
        import time as _t
        start = _t.perf_counter()
        df = load_csv(dataset_path)
        X, timestamps = dataframe_to_features(df)
        Xn = normalize_features(X)
        risk_model, anomaly_model = load_models()
        risk_scores, anomaly_flags = predict(risk_model, anomaly_model, Xn)

        items: List[AlertItem] = []
        totals = {"GREEN": 0, "YELLOW": 0, "RED": 0}
        for ts, s, a in zip(timestamps, risk_scores, anomaly_flags):
            prio = score_to_priority(float(s), bool(a))
            totals[prio] += 1
            ALERTS_TOTAL.labels(prio).set(totals[prio])
            items.append(
                AlertItem(
                    timestamp=str(ts),
                    priority=prio,
                    risk_score=float(np.round(s, 4)),
                    anomaly=bool(a),
                    summary=summarize(prio),
                    recommended_actions=recommended_actions(prio),
                )
            )
        # Send a notification for the top-most RED alert (if any)
        try:
            top_red = next((i for i in items if i.priority == "RED"), None)
            if top_red is not None:
                import asyncio
                asyncio.create_task(
                    notify_slack(
                        priority=top_red.priority,
                        summary=top_red.summary,
                        details={
                            "timestamp": top_red.timestamp,
                            "risk_score": top_red.risk_score,
                            "anomaly": top_red.anomaly,
                        },
                    )
                )
        except Exception:
            pass
        REQUEST_COUNT.labels("/alerts", "GET", 200).inc()
        REQUEST_LATENCY.labels("/alerts").observe(_t.perf_counter() - start)
        return AlertsResponse(alerts=items, totals=totals)
    except FileNotFoundError:
        REQUEST_COUNT.labels("/alerts", "GET", 400).inc()
        raise HTTPException(status_code=400, detail="Models not trained. Call /train first.")
    except Exception as exc:
        REQUEST_COUNT.labels("/alerts", "GET", 400).inc()
        raise HTTPException(status_code=400, detail=str(exc))

