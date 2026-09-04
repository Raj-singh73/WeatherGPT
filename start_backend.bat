@echo off
echo ======================================================================
echo           Starting WeatherGPT FastAPI Backend Server (SIH 2026)
echo ======================================================================
cd /d "%~dp0"
python backend\main.py
if errorlevel 1 (
    if exist "C:\Users\rajs6\anaconda3\python.exe" (
        "C:\Users\rajs6\anaconda3\python.exe" backend\main.py
    )
)
pause
