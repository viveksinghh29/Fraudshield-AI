"""Pydantic v2 schemas for prediction, transaction, and explanation endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionInput(BaseModel):
    """Raw transaction fields, matching the Kaggle schema exactly."""

    time: float = Field(alias="Time")
    amount: float = Field(alias="Amount", ge=0)
    v1: float = Field(alias="V1")
    v2: float = Field(alias="V2")
    v3: float = Field(alias="V3")
    v4: float = Field(alias="V4")
    v5: float = Field(alias="V5")
    v6: float = Field(alias="V6")
    v7: float = Field(alias="V7")
    v8: float = Field(alias="V8")
    v9: float = Field(alias="V9")
    v10: float = Field(alias="V10")
    v11: float = Field(alias="V11")
    v12: float = Field(alias="V12")
    v13: float = Field(alias="V13")
    v14: float = Field(alias="V14")
    v15: float = Field(alias="V15")
    v16: float = Field(alias="V16")
    v17: float = Field(alias="V17")
    v18: float = Field(alias="V18")
    v19: float = Field(alias="V19")
    v20: float = Field(alias="V20")
    v21: float = Field(alias="V21")
    v22: float = Field(alias="V22")
    v23: float = Field(alias="V23")
    v24: float = Field(alias="V24")
    v25: float = Field(alias="V25")
    v26: float = Field(alias="V26")
    v27: float = Field(alias="V27")
    v28: float = Field(alias="V28")

    model_config = ConfigDict(populate_by_name=True)

    def to_raw_dict(self) -> dict[str, float]:
        """Converts back to the Time/Amount/V1..V28 key format the Predictor expects."""
        data = {"Time": self.time, "Amount": self.amount}
        for i in range(1, 29):
            data[f"V{i}"] = getattr(self, f"v{i}")
        return data


class PredictionResponse(BaseModel):
    transaction_id: uuid.UUID
    predicted_class: str
    fraud_probability: float
    risk_level: str
    model_version: str
    threshold_used: float
    explanation_available: bool = True


class BatchUploadResponse(BaseModel):
    batch_id: uuid.UUID
    transaction_count: int
    task_id: str
    status: str = "queued"


class BatchStatusResponse(BaseModel):
    batch_id: uuid.UUID
    status: str
    total_transactions: int
    processed_transactions: int
    fraud_count: int | None = None


class ExplainRequest(BaseModel):
    transaction_id: uuid.UUID


class TopFeature(BaseModel):
    feature: str
    shap_value: float
    direction: str


class ExplanationResponse(BaseModel):
    transaction_id: uuid.UUID
    prediction_id: uuid.UUID
    predicted_class: str
    fraud_probability: float
    risk_level: str
    base_value: float
    value_space: str
    top_features: list[TopFeature]
    narrative_summary: str | None = None


class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    version_tag: str
    algorithm: str
    is_active: bool
    trained_at: datetime
    metrics: dict
