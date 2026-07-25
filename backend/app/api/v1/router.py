"""Assembles the v1 API surface."""

from fastapi import APIRouter

from app.api.v1 import analyses, auth, health, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(analyses.router)
