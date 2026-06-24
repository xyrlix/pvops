"""API V1 路由聚合."""

from fastapi import APIRouter

from app.api.v1 import alarms, auth, chat, dashboard, devices, diagnosis, health, ingest, knowledge, metrics, reports, simulator, stations, work_orders

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(stations.router, prefix="/stations", tags=["stations"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
api_router.include_router(work_orders.router, prefix="/workorders", tags=["workorders"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(diagnosis.router, prefix="/diagnosis", tags=["diagnosis"])
api_router.include_router(knowledge.router, prefix="/kb", tags=["knowledge"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(simulator.router, prefix="/simulator", tags=["simulator"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
