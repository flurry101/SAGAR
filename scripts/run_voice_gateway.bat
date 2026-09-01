@echo off
echo ========================================================
echo   Starting Vexyl Voice Gateway (Docker)
echo ========================================================
docker run --env-file "%~dp0\..\backend\.env" -p 8081:8081 -p 8082:8082 vexyl/vexyl-voice-gateway:latest
pause
