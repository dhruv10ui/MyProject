import random
import datetime
import pandas as pd
import numpy as np

def generate_historical_mess_data(days: int = 120, total_students: int = 450) -> pd.DataFrame:
    """
    Generates realistic semester-long daily meal check-in, skips, and waste records
    incorporating weekly cyclicality, weekend drops, exam periods, and holidays.
    """
    np.random.seed(42)
    random.seed(42)

    records = []
    start_date = datetime.date(2026, 7, 1) # Start of odd semester

    meal_base_rates = {
        "Breakfast": 0.65, # 65% attendance
        "Lunch": 0.88,     # 88% attendance
        "Snacks": 0.58,    # 58% attendance
        "Dinner": 0.92     # 92% attendance
    }

    # Exam periods (mid-term mid-Sept, end-term Nov)
    exam_dates = set([
        start_date + datetime.timedelta(days=d) for d in range(70, 78)
    ] + [
        start_date + datetime.timedelta(days=d) for d in range(110, 120)
    ])

    for d in range(days):
        current_date = start_date + datetime.timedelta(days=d)
        day_of_week = current_date.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = 1 if day_of_week in [5, 6] else 0
        is_exam = 1 if current_date in exam_dates else 0
        is_holiday = 1 if (d in [15, 45, 60, 92] or (is_weekend and random.random() < 0.15)) else 0

        for meal_type, base_rate in meal_base_rates.items():
            rate = base_rate

            # Weekend effect: Many students go out / home on weekends
            if is_weekend:
                if meal_type == "Breakfast":
                    rate *= 0.60 # Wake up late / skip
                elif meal_type == "Lunch":
                    rate *= 0.75
                elif meal_type == "Dinner":
                    rate *= 0.70

            # Exam period effect: Students stay in hostel and eat mess meals
            if is_exam:
                rate = min(0.97, rate * 1.12)

            # Holiday effect: Campus mass departures
            if is_holiday:
                rate *= 0.45

            # Random natural variation (+/- 5%)
            jitter = np.random.normal(0, 0.03)
            final_rate = np.clip(rate + jitter, 0.25, 0.98)

            expected_attendance = int(total_students * final_rate)
            # Declared skips correlation: higher when students eat outside
            skip_probability = (1.0 - final_rate) * 0.75
            declared_skips = int(total_students * skip_probability + np.random.normal(0, 4))
            declared_skips = max(5, min(declared_skips, total_students - expected_attendance))

            # Without AI forecasting, kitchen traditionally cooks for ~90% capacity
            traditional_prepared = int(total_students * 0.90) if meal_type in ["Lunch", "Dinner"] else int(total_students * 0.72)
            surplus_meals = max(0, traditional_prepared - expected_attendance)
            waste_kg = round(surplus_meals * 0.42, 2) # Average 420 grams edible food per plated meal

            records.append({
                "date": current_date.isoformat(),
                "day_of_week": day_of_week,
                "meal_type": meal_type,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "is_exam_period": is_exam,
                "enrolled_students": total_students,
                "declared_skips": declared_skips,
                "traditional_prepared": traditional_prepared,
                "actual_attendance": expected_attendance,
                "waste_kg": waste_kg
            })

    df = pd.DataFrame(records)

    # Calculate rolling features
    df["rolling_7day_avg"] = df.groupby("meal_type")["actual_attendance"].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
    ).fillna(df["actual_attendance"].mean())

    return df

if __name__ == "__main__":
    df = generate_historical_mess_data(120)
    print("Generated mess attendance dataset sample:")
    print(df.head())
