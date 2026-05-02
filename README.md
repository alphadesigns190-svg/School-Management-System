# Learning Center Management System (LCMS)

Backend: Flask (Python)  
Frontend: HTML/CSS/JavaScript (Flask templates + static files)  
Database (runtime): SQLite

## 1) Setup (Windows PowerShell)

```powershell
cd "C:\Users\Kandahar computer\Desktop\School-Management-System"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Configure environment variables

Copy `.env.example` to `.env` and review values:

```powershell
Copy-Item .env.example .env
notepad .env
```

Important values:
- `SQLITE_PATH` = SQLite database file used by the app.
- `MYSQL_*` = source database values used only for one-time migration.

## 3) One-time migration (MySQL → SQLite)

```powershell
python scripts\migrate_mysql_to_sqlite.py
```

This copies data for all existing tables without changing table columns:
- `Students`
- `Teachers`
- `Courses`
- `Enrollments`
- `Payments`
- `Results`

## 4) Run the app

```powershell
python run.py
```

Then open: `http://127.0.0.1:5000`

## 5) Quick checks

- App health: `GET /health`
- DB connection ping: `GET /db/ping`

## 6) Build Windows .exe (client deployment)

```powershell
build_exe.bat
```

This creates `dist\LCMS\` and includes:
- `LCMS.exe`
- `.env`
- `data\learning_center.sqlite3` (your migrated SQLite database)
- `app\templates` and `app\static`

To test built app locally:

```powershell
run_built_app.bat
```

On client PC, copy the whole `dist\LCMS\` folder and run `LCMS.exe`.

