from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class LogRecord(BaseModel):
    timestamp: str
    cpu: float = Field(ge=0)
    memory: float = Field(ge=0)
    disk_io: float = Field(ge=0)
    net_io: float = Field(ge=0)
    errors: int = Field(ge=0)


class PredictRequest(BaseModel):
    records: List[LogRecord]


class PredictResponse(BaseModel):
    risk_scores: List[float]
    anomaly_flags: List[int]


class AlertItem(BaseModel):
    timestamp: str
    priority: str
    risk_score: float
    anomaly: bool
    summary: str
    recommended_actions: List[str]


class AlertsResponse(BaseModel):
    alerts: List[AlertItem]
    totals: Dict[str, int]

