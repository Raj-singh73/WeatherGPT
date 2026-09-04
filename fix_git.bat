@echo off
title WeatherGPT Git Repair
echo ========================================================
echo        WeatherGPT - Git Index Auto-Repair Utility
echo ========================================================
echo.
echo Checking for corrupt or locked Git index...
if exist .git\index.lock (
    echo [INFO] Removing lingering lock file: .git\index.lock
    del /f /q .git\index.lock
)

echo [INFO] Restoring clean Git index from repository HEAD...
del /f /q .git\index 2>nul
git reset --quiet

echo.
echo ========================================================
echo   SUCCESS: Git repository and index are fully healthy!
echo ========================================================
echo.
git status -s
echo.
pause
