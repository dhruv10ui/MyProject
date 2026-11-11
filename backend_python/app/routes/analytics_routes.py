import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, MessTransaction, MealSkip, Complaint, Room, Payment
from app.rbac import get_current_user
from app.ml.predictor import predict_demand, get_ml_metrics
from app.ml.model_trainer import train_and_evaluate_models

router = APIRouter(prefix="/analytics", tags=["Food-Waste Analytics & ML Forecasting"])

@router.get("/ml-forecast")
def get_ml_food_forecast(
    date_str: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Signature ML Feature:
    Meal demand forecasting and food waste prediction.
    Outputs:
    1. Session-by-session predicted headcount for the day.
    2. Model comparison table (Moving Average baseline vs Random Forest vs Gradient Boosting).
    3. Error evaluation (MAE, MAPE on time-based holdout set).
    4. Quantified food waste prevented in kg and cost savings in INR.
    """
    if not date_str:
        date_str = datetime.date.today().isoformat()

    total_students = db.query(Student).count()
    if total_students == 0:
        total_students = 450 # Default sample cohort

    sessions = ["Breakfast", "Lunch", "Snacks", "Dinner"]
    session_forecasts = []

    for s in sessions:
        # Count declared skips for this session
        skips_count = db.query(MealSkip).filter(
            MealSkip.date == datetime.date.fromisoformat(date_str),
            MealSkip.meal_type == s
        ).count()

        pred = predict_demand(
            date_str=date_str,
            meal_type=s,
            enrolled_students=total_students,
            declared_skips=skips_count,
            is_exam_period=False,
            is_holiday=False
        )
        session_forecasts.append(pred)

    metrics = get_ml_metrics()

    return {
        "target_date": date_str,
        "enrolled_students": total_students,
        "sessions": session_forecasts,
        "benchmark_metrics": metrics.get("model_comparison", []),
        "impact_summary": metrics.get("impact_metrics", {}),
        "recent_evaluation_chart": metrics.get("recent_evaluation", [])
    }

@router.post("/train-model")
def trigger_model_retraining(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrain Random Forest and Gradient Boosting models on historical transaction data."""
    if current_user.role not in ["admin", "mess_staff", "warden"]:
        raise HTTPException(status_code=403, detail="Unauthorized to trigger ML model training.")

    try:
        results = train_and_evaluate_models()
        return {
            "status": "success",
            "message": "ML models retrained and evaluated on time-based test holdout set.",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training error: {str(e)}")

@router.get("/charts")
def get_chart_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregated charts for occupancy, complaints, and fee revenue."""
    # Occupancy by block
    rooms = db.query(Room).all()
    block_map = {}
    for r in rooms:
        if r.block not in block_map:
            block_map[r.block] = {"capacity": 0, "occupied": 0}
        block_map[r.block]["capacity"] += r.capacity
        block_map[r.block]["occupied"] += r.occupied_beds

    # Complaint categories breakdown
    complaints = db.query(Complaint).all()
    category_map = {}
    for c in complaints:
        category_map[c.category] = category_map.get(c.category, 0) + 1

    # Revenue by head
    payments = db.query(Payment).filter(Payment.payment_status == "Success").all()
    revenue_map = {}
    for p in payments:
        revenue_map[p.category] = revenue_map.get(p.category, 0.0) + p.amount

    return {
        "occupancy_by_block": block_map,
        "complaints_by_category": category_map,
        "revenue_by_head": revenue_map
    }
