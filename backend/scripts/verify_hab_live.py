# verify_hab_live.py
# Lightweight wrapper to run HAB verification scripts
from backend.app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter
from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    adapter = AmfitriteHABAdapter()
    ts = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:00:00Z")
    print(adapter.fetch_data(12.87, 74.84, ts))
