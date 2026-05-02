@echo off
cd /d "%~dp0"
if not exist "dist\LCMS\LCMS.exe" (
  echo LCMS.exe not found. Run build_exe.bat first.
  exit /b 1
)
start "" "dist\LCMS\LCMS.exe"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"
