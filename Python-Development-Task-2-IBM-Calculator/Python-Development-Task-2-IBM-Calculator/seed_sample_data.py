"""
Sample Data Seeder for BMI Calculator

Populates the SQLite database (bmi_records.db) with realistic,
multi-user historical records demonstrating various BMI categories
and longitudinal progression for demonstration and testing.
"""

from datetime import datetime, timedelta
from database import DatabaseManager
from bmi_logic import calculate_bmi, classify_bmi


def seed_database(db_path: str = "bmi_records.db") -> None:
    """Populate sample BMI records for demonstration."""
    db = DatabaseManager(db_path)

    # Define sample users and realistic measurement progressions over time
    sample_users = {
        "John Doe": [
            # Height: 1.75m, Weight loss journey from Overweight to Normal
            {"days_ago": 120, "weight": 86.0, "height": 1.75},
            {"days_ago": 90,  "weight": 82.5, "height": 1.75},
            {"days_ago": 60,  "weight": 79.0, "height": 1.75},
            {"days_ago": 30,  "weight": 75.5, "height": 1.75},
            {"days_ago": 0,   "weight": 72.0, "height": 1.75},
        ],
        "Sarah Smith": [
            # Height: 1.65m, Maintaining healthy Normal BMI
            {"days_ago": 90,  "weight": 58.5, "height": 1.65},
            {"days_ago": 60,  "weight": 59.0, "height": 1.65},
            {"days_ago": 30,  "weight": 58.0, "height": 1.65},
            {"days_ago": 0,   "weight": 59.5, "height": 1.65},
        ],
        "Alex Rivera": [
            # Height: 1.82m, Fitness journey from Underweight to Normal
            {"days_ago": 90,  "weight": 58.0, "height": 1.82},
            {"days_ago": 45,  "weight": 62.0, "height": 1.82},
            {"days_ago": 0,   "weight": 66.5, "height": 1.82},
        ],
        "David Miller": [
            # Single baseline record for testing 1-record chart display
            {"days_ago": 10,  "weight": 102.0, "height": 1.78},
        ]
    }

    base_time = datetime.now()
    records_added = 0

    for user_name, measurements in sample_users.items():
        for m in measurements:
            rec_time = base_time - timedelta(days=m["days_ago"])
            time_str = rec_time.strftime("%Y-%m-%d %H:%M:%S")
            
            bmi = calculate_bmi(m["weight"], m["height"])
            category, _ = classify_bmi(bmi)
            
            db.add_record(
                user_name=user_name,
                weight=m["weight"],
                height=m["height"],
                bmi=bmi,
                category=category,
                recorded_at=time_str
            )
            records_added += 1

    print(f"Successfully seeded {records_added} sample records across {len(sample_users)} users into '{db_path}'.")


if __name__ == "__main__":
    seed_database()
