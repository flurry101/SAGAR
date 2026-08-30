# verify_live.py
from datetime import datetime, timezone, timedelta

def get_current_utc_timestamp():
    dt = datetime.now(timezone.utc) + timedelta(hours=3)
    return dt.strftime("%Y-%m-%dT%H:00:00Z")

if __name__ == "__main__":
    print(get_current_utc_timestamp())
