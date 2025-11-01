import os
import json
import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# -------------------------------
# 🌐 Backend API Configuration
# -------------------------------
API_URL = os.getenv("API_URL", "http://localhost:8000")

# -------------------------------
# 🔄 Cached Alerts Fetching Function
# -------------------------------
@st.cache_data(ttl=60)
def fetch_alerts():
    """Fetch alerts from backend API with caching."""
    resp = requests.get(f"{API_URL}/alerts", timeout=30)
    resp.raise_for_status()
    return resp.json()

# -------------------------------
# ❤️ Health Check Function
# -------------------------------
def health_check() -> bool:
    """Check if backend is healthy and reachable."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.ok
    except Exception:
        return False

# -------------------------------
# 🧭 Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Predictive Downtime & Smart Alerts", layout="wide")
st.title("⚙️ Predictive Downtime & Smart Alerts")

# -------------------------------
# 🩺 Backend Health Status
# -------------------------------
status_col1, status_col2 = st.columns(2)
with status_col1:
    st.markdown("**Backend Health**")
    if health_check():
        st.success("✅ Online")
    else:
        st.error("❌ Offline")

with status_col2:
    if st.button("Train Models", type="primary"):
        with st.spinner("Training models..."):
            try:
                r = requests.post(f"{API_URL}/train", timeout=60)
                if r.ok:
                    st.success("🎉 Training completed successfully!")
                    st.rerun()
                else:
                    st.error(f"Training failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()

# -------------------------------
# 📊 Alerts and Visualization
# -------------------------------
try:
    data = fetch_alerts()
    totals = data.get("totals", {})
    alerts = data.get("alerts", [])

    # Handle case where totals might be empty
    if not totals:
        st.warning("No total data available. Please check the backend.")
        totals = {"GREEN": 0, "YELLOW": 0, "RED": 0}

    # -------------------------------
    # 🥧 Pie Chart - Server Health Overview
    # -------------------------------
    pie_df = pd.DataFrame({
        "status": list(totals.keys()),
        "count": list(totals.values()),
    })

    fig = px.pie(
        pie_df,
        names="status",
        values="count",
        color="status",
        color_discrete_map={"GREEN": "green", "YELLOW": "gold", "RED": "red"},
        hole=0.4,
        title="Server Health Overview"
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # 📋 Alerts Table + Guided Resolution
    # -------------------------------
    with col2:
        st.subheader("Server Status & Recommended Actions")

        if len(alerts) > 0:
            # Clean alerts data (remove any function-type objects)
            for alert in alerts:
                for key, value in alert.items():
                    if callable(value):
                        alert[key] = str(value)

            # Create DataFrame
            table_df = pd.DataFrame(alerts)

            # Safely select columns (in case any are missing)
            cols_to_show = [col for col in ["timestamp", "priority", "risk_score", "anomaly", "summary"] if col in table_df.columns]

            st.dataframe(
                table_df[cols_to_show],
                use_container_width=True,
                height=480
            )

            # Guided Resolution Steps
            st.markdown("### 🧭 Guided Resolution")
            selected = st.selectbox(
                "Select an alert to view recommended actions:",
                options=list(range(len(alerts))),
                format_func=lambda i: f"{alerts[i].get('timestamp', 'N/A')} - {alerts[i].get('priority', 'Unknown')}",
            )

            st.write("#### 🪜 Recommended Actions:")
            for step in alerts[selected].get("recommended_actions", []):
                st.markdown(f"- {step}")

        else:
            st.info("No alerts available. Try training the model or check the data source.")

except Exception as e:
    st.error(f"⚠️ Failed to load alerts: {e}")
