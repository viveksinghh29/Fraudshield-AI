"""Pydantic v2 schemas for transaction history, dashboard, and analytics endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    predicted_class: str
    fraud_probability: float
    risk_level: str
    created_at: datetime


class TransactionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    time: float
    amount: float
    batch_id: uuid.UUID | None
    created_at: datetime
    prediction: PredictionSummary | None = None


class TransactionListResponse(BaseModel):
    items: list[TransactionSummary]
    total: int
    page: int
    page_size: int


class TransactionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    time: float
    amount: float
    v1: float
    v2: float
    v3: float
    v4: float
    v5: float
    v6: float
    v7: float
    v8: float
    v9: float
    v10: float
    v11: float
    v12: float
    v13: float
    v14: float
    v15: float
    v16: float
    v17: float
    v18: float
    v19: float
    v20: float
    v21: float
    v22: float
    v23: float
    v24: float
    v25: float
    v26: float
    v27: float
    v28: float
    batch_id: uuid.UUID | None
    created_at: datetime
    prediction: PredictionSummary | None = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    resource_type: str | None
    resource_id: uuid.UUID | None
    log_metadata: dict | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class DashboardResponse(BaseModel):
    total_transactions: int
    fraud_count: int
    legitimate_count: int
    fraud_rate_pct: float
    risk_distribution: dict[str, int]
    recent_predictions: list[TransactionSummary]
    active_model_version: str | None
    active_model_algorithm: str | None


class FraudTrendPoint(BaseModel):
    date: str
    total_transactions: int
    fraud_count: int


class AnalyticsResponse(BaseModel):
    fraud_trend: list[FraudTrendPoint]
    risk_distribution: dict[str, int]
    avg_fraud_probability: float
    avg_prediction_confidence: float
    total_predictions: int
