from fastapi import FastAPI
from app.database import engine, Base
import app.models  # noqa: F401 — registers models with Base.metadata
from app.routes import ingestion, analytics, backup

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Globant Data Engineering Challenge",
    description="REST API for data ingestion, analytics, and backup/restore",
    version="1.0.0",
)

app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(backup.router, prefix="/api/v1", tags=["Backup & Restore"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
