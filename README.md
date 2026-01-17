# WordMem (skeleton)

This workspace contains a development plan and a minimal project skeleton to get started.

Security note: Do NOT commit real API keys into the repository. Use environment variables or a secret manager. See `.env.example`.

Quickstart (macOS, zsh):

Backend (FastAPI):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (placeholder):
```bash
cd frontend
npm install
npm run dev
```

Docker (if you prefer containers):
```bash
docker compose up --build
```
