import json
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from app.ml.dataset_generator import generate_historical_mess_data

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_FILE = os.path.join(MODEL_DIR, "model_metrics.json")

def encode_features(df: pd.DataFrame):
    """One-hot encode categorical features like meal_type."""
    meal_mapping = {"Breakfast": 0, "Lunch": 1, "Snacks": 2, "Dinner": 3}
    df_feat = df.copy()
    df_feat["meal_encoded"] = df_feat["meal_type"].map(meal_mapping)
    
    feature_cols = [
        "day_of_week",
        "meal_encoded",
        "is_weekend",
        "is_holiday",
        "is_exam_period",
        "enrolled_students",
        "declared_skips",
        "rolling_7day_avg"
    ]
    return df_feat[feature_cols], df_feat["actual_attendance"]

def train_and_evaluate_models(data: pd.DataFrame = None) -> dict:
    """
    Trains Moving Average baseline, Random Forest, and Gradient Boosting.
    Evaluates on a chronological holdout set (last 14 days of the semester).
    """
    if data is None:
        data = generate_historical_mess_data(120, total_students=450)

    # Chronological holdout split: last 14 days for testing
    split_index = len(data) - (14 * 4) # 4 meals per day
    train_df = data.iloc[:split_index].copy()
    test_df = data.iloc[split_index:].copy()

    X_train, y_train = encode_features(train_df)
    X_test, y_test = encode_features(test_df)

    # 1. Baseline: Moving Average
    baseline_preds = test_df["rolling_7day_avg"].values
    baseline_mae = float(mean_absolute_error(y_test, baseline_preds))
    baseline_mape = float(mean_absolute_percentage_error(y_test, baseline_preds) * 100)

    # 2. Random Forest Regressor
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_mae = float(mean_absolute_error(y_test, rf_preds))
    rf_mape = float(mean_absolute_percentage_error(y_test, rf_preds) * 100)

    # 3. Gradient Boosting Regressor
    gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, random_state=42)
    gb_model.fit(X_train, y_train)
    gb_preds = gb_model.predict(X_test)
    gb_mae = float(mean_absolute_error(y_test, gb_preds))
    gb_mape = float(mean_absolute_percentage_error(y_test, gb_preds) * 100)

    # Calculate Food Waste Averted (kg and INR)
    # Traditional overpreparation error vs Best ML model error
    traditional_errors = test_df["traditional_prepared"] - y_test
    traditional_waste_kg = float(traditional_errors[traditional_errors > 0].sum() * 0.42)
    
    # ML prepared buffer is predicted + 5% safety margin
    ml_buffer = rf_preds * 1.05
    ml_errors = ml_buffer - y_test
    ml_waste_kg = float(ml_errors[ml_errors > 0].sum() * 0.42)
    
    waste_saved_kg = round(max(0.0, traditional_waste_kg - ml_waste_kg), 1)
    savings_inr = round(waste_saved_kg * 75.0, 2) # Est. ₹75 per kg food raw materials

    # Recent predicted vs actual comparisons for UI chart
    recent_eval = []
    test_df_reset = test_df.reset_index(drop=True)
    for i in range(min(28, len(test_df_reset))): # Last 7 days (4 meals/day)
        row = test_df_reset.iloc[i]
        recent_eval.append({
            "date": row["date"],
            "meal_type": row["meal_type"],
            "actual": int(row["actual_attendance"]),
            "predicted_rf": int(round(rf_preds[i])),
            "traditional": int(row["traditional_prepared"]),
            "skips": int(row["declared_skips"])
        })

    results = {
        "dataset_summary": {
            "total_records": len(data),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "features_used": [
                "day_of_week", "meal_type", "is_weekend", "is_holiday",
                "is_exam_period", "enrolled_students", "declared_skips", "rolling_7day_avg"
            ]
        },
        "model_comparison": [
            {
                "model_name": "7-Day Moving Average (Baseline)",
                "mae": round(baseline_mae, 2),
                "mape": round(baseline_mape, 2),
                "is_best": False
            },
            {
                "model_name": "Random Forest Regressor (Hostel 360 Primary)",
                "mae": round(rf_mae, 2),
                "mape": round(rf_mape, 2),
                "is_best": rf_mae <= gb_mae
            },
            {
                "model_name": "Gradient Boosting Regressor",
                "mae": round(gb_mae, 2),
                "mape": round(gb_mape, 2),
                "is_best": gb_mae < rf_mae
            }
        ],
        "impact_metrics": {
            "waste_saved_kg_14days": waste_saved_kg,
            "cost_savings_inr_14days": savings_inr,
            "waste_reduction_percentage": round(((traditional_waste_kg - ml_waste_kg) / max(1, traditional_waste_kg)) * 100, 1),
            "traditional_waste_kg": round(traditional_waste_kg, 1),
            "ml_waste_kg": round(ml_waste_kg, 1)
        },
        "recent_evaluation": recent_eval
    }

    # Save metrics to disk
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    res = train_and_evaluate_models()
    print("Model Evaluation Complete:")
    print(json.dumps(res["model_comparison"], indent=2))
    print("Impact Metrics:", res["impact_metrics"])
