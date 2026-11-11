import pytest
from app.ml.predictor import predict_demand
from app.ml.dataset_generator import generate_historical_mess_data

def test_ml_demand_prediction_bounds():
    pred = predict_demand(
        date_str="2026-11-12",
        meal_type="Dinner",
        enrolled_students=450,
        declared_skips=30
    )
    assert "predicted_attendance" in pred
    assert "recommended_preparation" in pred
    assert pred["predicted_attendance"] > 0
    assert pred["predicted_attendance"] <= 450
    # Recommended preparation includes 5% safety margin
    assert pred["recommended_preparation"] >= pred["predicted_attendance"]

def test_historical_dataset_generation():
    df = generate_historical_mess_data(days=30, total_students=400)
    assert len(df) == 30 * 4 # 4 meals per day
    assert "actual_attendance" in df.columns
    assert "declared_skips" in df.columns
    assert "rolling_7day_avg" in df.columns
