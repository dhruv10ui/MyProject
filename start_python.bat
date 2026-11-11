@echo off
title Hostel 360 - Python FastAPI REST API
color 0B

echo ======================================================================
echo    HOSTEL 360: Python FastAPI REST API Backend
echo    SRM University Delhi-NCR, Sonepat - Department of CSE
echo ======================================================================
echo.

cd "%~dp0backend_python"

echo [*] Checking Python dependencies...
python -m pip install -r requirements.txt

echo [*] Initializing and seeding database...
python seed_data.py

echo [*] Starting Uvicorn API server on http://localhost:8000 ...
echo [*] Interactive Swagger UI docs available at: http://localhost:8000/docs
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
