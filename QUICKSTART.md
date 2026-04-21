# 🚀 Quick Start Guide - Threadangle

## Option 1: Automatic Start (Easiest)

**Windows PowerShell:**
```powershell
cd F:\Threadforge
.\START.ps1
```

This will automatically open 2 terminal windows:
- Backend server (port 8000)
- Frontend server (port 5173)

Then open: **http://localhost:5173**

---

## Option 2: Manual Start (2 Terminals)

### Terminal 1 - Backend

```powershell
cd F:\Threadforge\backend
python start_backend.py
```

Wait until you see: `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2 - Frontend

```powershell
cd F:\Threadforge\frontend
npm install
npm run dev
```

Wait until you see: `Local: http://localhost:5173/`

Then open: **http://localhost:5173**

---

## Option 3: Just Commands

### Backend:
```powershell
cd F:\Threadforge\backend
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite python-dotenv anthropic httpx beautifulsoup4 python-jose[cryptography] passlib[bcrypt] python-multipart stripe slowapi aiosmtplib email-validator pydantic[email]
python -m uvicorn main:app --reload --port 8000
```

### Frontend:
```powershell
cd F:\Threadforge\frontend
npm install
npm run dev
```

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'fastapi'"**
- Make sure you're in the backend directory
- Run: `pip install -r requirements.txt`

**"email-validator is not installed"**
- Run: `pip install email-validator pydantic[email]`

**Frontend won't start:**
- Make sure Node.js is installed
- Run: `npm install --force`

**Backend API docs:**
- http://127.0.0.1:8000/docs

---

## What You Should See

✅ Backend: Console shows "Uvicorn running on http://127.0.0.1:8000"
✅ Frontend: Console shows "Local: http://localhost:5173/"
✅ Browser: React app loads with sign up/login page

---

## Stopping the Servers

Press **CTRL+C** in each terminal window
