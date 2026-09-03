"""Validates and uploads transaction CSVs, stores rows by batch_id, and returns the batch ID."""

import uuid
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.ml.pipeline.data_loader import REQUIRED_COLUMNS
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.prediction_schema import BatchUploadResponse
from app.schemas.transaction_schema import (
    PredictionSummary,
    TransactionDetailResponse,
    TransactionListResponse,
    TransactionSummary,
)
from app.services.transaction_service import TransactionService

router = APIRouter()
settings = get_settings()


def _prediction_summary(prediction) -> PredictionSummary | None:
    if prediction is None:
        return None
    return PredictionSummary(
        id=prediction.id,
        predicted_class=prediction.predicted_class.value,
        fraud_probability=prediction.fraud_probability,
        risk_level=prediction.risk_level.value,
        created_at=prediction.created_at,
    )


async def _read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """
    Reads in chunks up to max_bytes + 1, then stops -- so a huge upload
    is rejected after buffering at most (max_bytes + 1) in memory,
    never the full file, regardless of how large the client claims (or
    tries) to send.
    """
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1024 * 1024  # 1 MB per read

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            break

    return b"".join(chunks)


@router.post("/upload", response_model=BatchUploadResponse, status_code=202)
async def upload_transactions_csv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("Uploaded file must be a .csv file.")

    max_bytes = settings.MAX_CSV_UPLOAD_SIZE_MB * 1024 * 1024
    raw_bytes = await _read_upload_bounded(file, max_bytes)
    if len(raw_bytes) > max_bytes:
        raise ValidationError(
            f"File exceeds the {settings.MAX_CSV_UPLOAD_SIZE_MB}MB upload limit."
        )

    try:
        df = pd.read_csv(BytesIO(raw_bytes))
    except Exception as exc:
        raise ValidationError(f"Could not parse uploaded file as CSV: {exc}") from exc

    if len(df) > settings.MAX_CSV_UPLOAD_ROWS:
        raise ValidationError(
            f"CSV has {len(df)} rows, exceeding the {settings.MAX_CSV_UPLOAD_ROWS}-row "
            "limit per batch. Split it into smaller files."
        )

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValidationError(f"CSV is missing required columns: {sorted(missing)}")

    non_numeric = [col for col in REQUIRED_COLUMNS if not pd.api.types.is_numeric_dtype(df[col])]
    if non_numeric:
        raise ValidationError(f"CSV has non-numeric values in expected-numeric columns: {non_numeric}")

    batch_id = uuid.uuid4()
    rows = df[REQUIRED_COLUMNS].rename(columns=str.lower).to_dict(orient="records")
    for row in rows:
        row["batch_id"] = batch_id
        row["uploaded_by"] = current_user.id

    repo = TransactionRepository(db)
    created = await repo.bulk_create(rows)
    await db.commit()

    return BatchUploadResponse(
        batch_id=batch_id,
        transaction_count=len(created),
        task_id="",  # no task yet -- prediction is triggered separately via POST /predict/batch
        status="uploaded",
    )


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    risk_level: str | None = Query(default=None),
    predicted_class: str | None = Query(default=None),
    batch_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> TransactionListResponse:
    service = TransactionService(db)
    result = await service.list_transactions(
        page=page,
        page_size=page_size,
        risk_level=risk_level,
        predicted_class=predicted_class,
        batch_id=batch_id,
    )

    items = [
        TransactionSummary(
            id=entry["transaction"].id,
            time=entry["transaction"].time,
            amount=float(entry["transaction"].amount),
            batch_id=entry["transaction"].batch_id,
            created_at=entry["transaction"].created_at,
            prediction=_prediction_summary(entry["prediction"]),
        )
        for entry in result["items"]
    ]

    return TransactionListResponse(
        items=items, total=result["total"], page=result["page"], page_size=result["page_size"]
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> TransactionDetailResponse:
    service = TransactionService(db)
    result = await service.get_transaction_detail(transaction_id)
    txn = result["transaction"]

    data = {
        "id": txn.id,
        "time": txn.time,
        "amount": float(txn.amount),
        "batch_id": txn.batch_id,
        "created_at": txn.created_at,
        "prediction": _prediction_summary(result["prediction"]),
    }
    for i in range(1, 29):
        data[f"v{i}"] = getattr(txn, f"v{i}")

    return TransactionDetailResponse(**data)
