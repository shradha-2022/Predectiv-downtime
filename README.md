## Predictive Downtime & Smart Alerts

Proactive, actionable, efficient alerting that predicts failures before they happen, cuts false positives, and provides guided resolutions.

### What makes it different?
- Reactive tools alert after failure; this system predicts at-risk states in advance.
- Reduces noise by ranking alerts by impact and confidence.
- Includes step-by-step auto-resolution guidance with every alert.

### How it solves the problem
- Ingests logs/metrics, learns failure patterns, and scores risk continuously.
- Detects anomalies via isolation forest and classifies failure risk via random forest.
- Surfaces prioritized alerts (GREEN/YELLOW/RED) with recommended actions.

### USP
- Proactive prevention, not just detection.
- Actionable runbooks attached to alerts.
- Efficiency: fewer false positives → lower alert fatigue.

### Features
- Predictive Alerting, Root Cause Signals, Smart Alerts, Auto-Resolution Guides
- Dashboard: Pie chart health overview, table with recommended actions
- Scalable via Docker + docker-compose (K8s-ready)

### Architecture (high-level)
```
[Data/Logs] → [Preprocess] → [Models: RF (risk) + IF (anomaly)] → [FastAPI]
                                                       ↘︎ [Streamlit UI]
```

### Process Flow
1. Ingest metrics/logs (CSV demo).
2. Train models (POST /train).
3. Predict and generate alerts (GET /alerts).
4. UI visualizes health + actions.

### Tech Stack
- Backend: FastAPI, scikit-learn, Pandas
- Frontend: Streamlit + Plotly
- Containerization: Docker + docker-compose

### Quick start (Docker)
```
docker compose build
docker compose up -d
# Train models
curl -X POST http://localhost:8000/train
# Open UI
http://localhost:8501
# Observability
# Prometheus: http://localhost:9090  | Grafana: http://localhost:3000 (default admin/admin)
```

### Local dev
```
python -m venv .venv && .venv/Scripts/activate
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
python scripts/seed_data.py --n 800 --out data/sample_logs.csv
uvicorn backend.app.main:app --reload
# In another terminal
streamlit run frontend/app.py
```

### Wireframes/Mockups
- Pie Chart: Server Health Overview (GREEN/YELLOW/RED)
- Table: Server Status + Recommended Actions (with guided steps)

### API
- GET `/health` → health probe
- GET `/metrics` → Prometheus metrics (pdsa_requests_total, pdsa_request_latency_seconds, pdsa_alerts_total)
- POST `/train` (env TRAIN_DATA) → trains models on CSV
- POST `/predict` → body: { records: [...] }
- GET `/alerts` → returns prioritized alerts and counts

### Notes
- Demo data and heuristics used for labels when none provided.
- Swap in ELK/Prometheus as sources in production.

### Slack Notifications (optional)
- Set `SLACK_WEBHOOK_URL` in environment to send notifications for RED/YELLOW alerts.
- In Docker:
```
backend:
  environment:
    - SLACK_WEBHOOK_URL=your_webhook
```

