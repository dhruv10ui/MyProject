import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hostel 360: Smart Hostel & Mess Management System"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = os.getenv("HOSTEL360_SECRET_KEY", "hostel360-super-secret-jwt-signing-key-2026-srm")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    QR_TOKEN_EXPIRE_SECONDS: int = 120  # 2 minutes short-lived signed QR tokens
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hostel360.db")
    
    # Institutional details
    INSTITUTION_NAME: str = "SRM University Delhi-NCR, Sonepat"
    DEPARTMENT: str = "Department of Computer Science and Engineering"
    PROJECT_TYPE: str = "B.Tech CSE 7th Semester Live Project"
    
    # Mess Session Times (24h format)
    MEAL_TIMINGS: dict = {
        "Breakfast": {"start": "07:30", "end": "09:30", "default_price": 50.0},
        "Lunch": {"start": "12:00", "end": "14:30", "default_price": 75.0},
        "Snacks": {"start": "16:30", "end": "18:00", "default_price": 30.0},
        "Dinner": {"start": "19:30", "end": "22:00", "default_price": 80.0}
    }
    
    # Billing modes: "subscription", "wallet", "quota"
    ACTIVE_BILLING_MODEL: str = os.getenv("DEFAULT_BILLING_MODEL", "subscription")

    class Config:
        case_sensitive = True

settings = Settings()
