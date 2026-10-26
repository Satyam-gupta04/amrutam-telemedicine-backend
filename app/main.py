from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.core.middleware import ObservabilityMiddleware, metrics_collector
from app.api import (
    auth_router,
    doctors_router,
    bookings_router,
    consultations_router,
    prescriptions_router,
    payments_router,
    admin_router
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ObservabilityMiddleware)

@app.get("/health", tags=["Health & Status"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

@app.get("/metrics", tags=["Observability"])
def get_metrics():
    return {
        "service": settings.PROJECT_NAME,
        "metrics": metrics_collector.get_stats()
    }

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(doctors_router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings_router, prefix=settings.API_V1_PREFIX)
app.include_router(consultations_router, prefix=settings.API_V1_PREFIX)
app.include_router(prescriptions_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
