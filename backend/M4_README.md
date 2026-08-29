M4 Migration Notes for Teammates
================================

Summary
-------
This file highlights the M4 migration I prepared from ORCA-Marine-AI into the SAGAR backend.
It is intended for teammates to quickly understand which files were added/modified and how to run the M4 tests.

What changed (high level)
-------------------------
- New/updated adapters in `backend/app/adapters/` for live vs static fallbacks.
- Rolling/relative fallback data in `backend/data/fallback/` (IBTrACS-derived hazard samples, demo cyclone).
- Verification scripts in `backend/scripts/` for local manual checks.
- M4 unit tests copied to `backend/tests/orca_m4/`.

Run tests
---------
From repo root:

```powershell
cd SAGAR/backend
pytest -q backend/tests/orca_m4/
```

Contact
-------
If any file here conflicts with upstream teammate work, do NOT accept automated merges — contact me or revert the file.
