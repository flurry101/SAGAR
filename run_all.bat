@echo off
echo ========================================================
echo   Starting ALL ORCA Services
echo ========================================================
echo Launching Backend in a new window...
start "ORCA Backend" cmd /k call run_backend.bat

echo Launching Voice Gateway in a new window...
start "Vexyl Voice Gateway" cmd /k call run_voice_gateway.bat

echo Launching Frontend in a new window...
start "ORCA Frontend" cmd /k call run_frontend.bat

echo.
echo All services have been launched in separate windows!
pause
