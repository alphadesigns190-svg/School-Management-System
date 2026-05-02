@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [1/4] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist LCMS.spec del /f /q LCMS.spec

echo [2/4] Ensuring required folders exist...
if not exist data mkdir data
if not exist app\data mkdir app\data
if not exist data\learning_center.sqlite3 (
  echo SQLite database not found at data\learning_center.sqlite3
  echo Run migration first: python scripts\migrate_mysql_to_sqlite.py
)

echo [3/4] Building executable with PyInstaller...
py -m PyInstaller --noconfirm --clean --onedir --name LCMS run.py ^
  --add-data "app\templates;app\templates" ^
  --add-data "app\static;app\static" ^
  --add-data ".env;." ^
  --add-data "data;data" ^
  --add-data "app\data;app\data"
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo [4/4] Build complete.
echo Output folder: dist\LCMS

echo.
echo Deploy these to client PC (inside dist\LCMS):
echo - LCMS.exe
echo - .env
echo - data\learning_center.sqlite3
echo - app\data\admin_settings.json (optional, created automatically if missing)

echo.
echo Run on client PC: LCMS.exe
endlocal
