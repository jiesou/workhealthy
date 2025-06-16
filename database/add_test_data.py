import time
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Assuming models.py and crud.py are in the same directory or accessible
# Adjust import paths if your project structure is different.
# If this script is inside 'database' directory, and 'models.py' is also there:
from models import WorkingSession, get_db, create_tables
# If 'crud.py' is needed for some helper (though direct model usage is fine here)
# import crud

def populate_test_data(db: Session, monitor_url: str, num_days: int):
    print(f"Populating test data for monitor '{monitor_url}' for the last {num_days} days...")

    # now = int(time.time()) # This variable is unused, can be removed or left.

    for i in range(num_days):
        # Go back i days
        current_day_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        current_day_start_ts = int(current_day_start_dt.timestamp())

        # Create 1 to 3 sessions per day
        num_sessions_today = random.randint(1, 3)

        # Simulate work hours (e.g., 9 AM to 5 PM)
        day_work_start_hour = 9
        day_work_end_hour = 17

        day_boundary_start_ts = current_day_start_ts + day_work_start_hour * 3600
        day_boundary_end_ts = current_day_start_ts + day_work_end_hour * 3600

        last_session_end_time_for_day = day_boundary_start_ts

        for _ in range(num_sessions_today):
            # Try to start after a small break from the last session
            possible_start_time = last_session_end_time_for_day + random.randint(0, 30 * 60) # 0-30 min break

            # Ensure it's not too late to start a meaningful session
            # Must be able to work for at least 30 mins before day_boundary_end_ts
            if possible_start_time >= day_boundary_end_ts - (30 * 60):
                continue

            start_time = possible_start_time

            # Max duration: up to 3 hours, but not exceeding day_boundary_end_ts
            # Min duration: 30 minutes
            min_duration = 30 * 60
            max_possible_duration = min(3 * 60 * 60, day_boundary_end_ts - start_time)

            if max_possible_duration < min_duration:
                continue

            duration_seconds = random.randint(min_duration, max_possible_duration)
            end_time = start_time + duration_seconds

            # Create session
            session = WorkingSession(
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                monitor_video_url=monitor_url
            )
            db.add(session)
            last_session_end_time_for_day = end_time

    db.commit()
    print(f"Finished populating test data for monitor '{monitor_url}'.")

if __name__ == "__main__":
    # Ensure tables are created
    print("Creating database tables if they don't exist...")
    create_tables() # This function should be in models.py

    print("Attempting to populate test data...")
    db_session = next(get_db())
    try:
        # Example usage:
        mock_monitor_url_1 = "test_monitor_1_fixed_url"
        # This URL is from the project's monitor_registry.py
        mock_monitor_url_2 = "udpserver://0.0.0.0:8099/192.168.10.100"

        populate_test_data(db_session, mock_monitor_url_1, 7)
        populate_test_data(db_session, mock_monitor_url_2, 7)

        print("Test data population successful.")
    except Exception as e:
        print(f"An error occurred during test data population: {e}")
    finally:
        db_session.close()
        print("Database session closed.")

```
