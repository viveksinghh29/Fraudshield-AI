"""Aggregates all v1 routers into a single APIRouter mounted by main.py."""

from fastapi import APIRouter

from app.api.v1.routers import (
    analytics,
    audit,
    auth,
    chat,
    dashboard,
    explain,
    health,
    model,
    predict,
    transactions,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(predict.router, prefix="/predict", tags=["Prediction"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(explain.router, prefix="/explain", tags=["Explainability"])
api_router.include_router(model.router, prefix="/model", tags=["Model Management"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
api_router.include_router(chat.router, prefix="/chat", tags=["Analyst Assistant"])
