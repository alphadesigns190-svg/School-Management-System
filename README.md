# Learning Center Management System (LCMS)

Backend: Flask (Python)  
Frontend: HTML/CSS/JavaScript (Flask templates + static files)  
Database: MySQL (we only connect/use your existing tables)

## 1) Setup (Windows PowerShell)

```powershell
cd "c:\Users\Kandahar computer\Desktop\Academy"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Configure environment variables

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```powershell
Copy-Item .env.example .env
notepad .env
```

## 3) Run the app

```powershell
python run.py
```

Then open: `http://127.0.0.1:5000`

## 4) Quick checks

- App health: `GET /health`
- DB connection ping: `GET /db/ping`

