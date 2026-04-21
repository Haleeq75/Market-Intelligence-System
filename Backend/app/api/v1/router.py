"""
app/api/v1/router.py
─────────────────────
Aggregates all v1 sub-routers into a single APIRouter.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.analysis import analysis_router
from app.api.v1.journal import journal_router
from app.api.v1.signals import signals_router, assets_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(analysis_router)
v1_router.include_router(journal_router)
v1_router.include_router(signals_router)
v1_router.include_router(assets_router)
