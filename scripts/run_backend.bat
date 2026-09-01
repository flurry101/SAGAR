@echo off
echo ========================================================
echo   Starting ORCA Python Backend (FastAPI)
echo ========================================================
cd /d "%~dp0\..\backend"
call .\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
