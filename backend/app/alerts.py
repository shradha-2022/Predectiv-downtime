from __future__ import annotations

from typing import List, Dict
import os
import httpx


def score_to_priority(score: float, anomaly: bool) -> str:
    if score >= 0.85 or (anomaly and score >= 0.7):
        return "RED"
    if score >= 0.55 or anomaly:
        return "YELLOW"
    return "GREEN"


def recommended_actions(priority: str) -> List[str]:
    if priority == "RED":
        return [
            "Throttle non-critical workloads",
            "Scale up pods/instances",
            "Restart affected service with drain",
            "Escalate to on-call SRE",
        ]
    if priority == "YELLOW":
        return [
            "Investigate recent deploys",
            "Check spikes in CPU/memory/disk",
            "Increase resource limits if necessary",
        ]
    return [
        "No action required",
        "Monitor metrics",
    ]


def summarize(priority: str) -> str:
    if priority == "RED":
        return "Imminent failure risk detected. Immediate action recommended."
    if priority == "YELLOW":
        return "Elevated risk. Investigate and mitigate to prevent downtime."
    return "System healthy."


async def notify_slack(priority: str, summary: str, details: Dict[str, str]) -> None:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook or priority not in {"RED", "YELLOW"}:
        return
    color = "#E01E5A" if priority == "RED" else "#ECB22E"
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"{priority} Alert - Predictive Downtime",
                "text": summary,
                "fields": [{"title": k, "value": str(v), "short": True} for k, v in details.items()],
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(webhook, json=payload)
    except Exception:
        # Notification failures should never break the main flow
        pass

