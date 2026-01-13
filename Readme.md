# NEPSE Empire Trading System - Frontend (Vite + React + Tailwind)

This repository contains a React frontend for NEPSE Empire Trading System (Vite + Tailwind). It pairs with your Python backend (api_server.py) located at the project root.

Quick start (development)
1. Install Python backend dependencies (if not already):
   - Create a virtualenv and install from `requirements.txt` (you already have api_server.py).
     ```
     python -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

2. Start the Python API (from repo root):
   ```
   python api_server.py
   ```
   The API runs on port 9000 by default.

3. Install Node dependencies and start the frontend:
   ```
   npm install
   npm run dev
   ```
   Open http://localhost:5173

Build for production
1. Build frontend:
   ```
   npm run build
   ```
2. Preview the built site:
   ```
   npm run preview
   ```

Notes
- Tailwind is configured in `tailwind.config.js`.
- The UI is purely client-side; integrate REST calls to `http://localhost:9000/api/...` where needed.
- If you plan to containerize, see the included `docker-compose.yml` for a starting point.