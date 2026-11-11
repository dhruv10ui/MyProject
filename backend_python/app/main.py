import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routes import (
    auth_routes, student_routes, warden_routes, mess_routes,
    complaint_routes, fee_routes, admin_routes, analytics_routes,
    additional_routes
)

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-stack REST API for Hostel 360 Smart Hostel & Mess Management System (SRM University Live Project)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route blueprints
app.include_router(auth_routes.router, prefix=settings.API_PREFIX)
app.include_router(student_routes.router, prefix=settings.API_PREFIX)
app.include_router(warden_routes.router, prefix=settings.API_PREFIX)
app.include_router(mess_routes.router, prefix=settings.API_PREFIX)
app.include_router(complaint_routes.router, prefix=settings.API_PREFIX)
app.include_router(fee_routes.router, prefix=settings.API_PREFIX)
app.include_router(admin_routes.router, prefix=settings.API_PREFIX)
app.include_router(analytics_routes.router, prefix=settings.API_PREFIX)
app.include_router(additional_routes.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "institution": settings.INSTITUTION_NAME,
        "team": "Dhruv Bansal (11023210138), Arnav Ambasta (11023210146), Janak Vallecha (11023210195)",
        "supervisor": "Ms. Anju Goel",
        "documentation": "/docs",
        "status": "operational"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": os.getenv("CURRENT_TIME", "")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
