# MedLens — AI-Powered Medical Report & Patient Intake Intelligence

[![Python Tests](https://img.shields.io/badge/pytest-71%20passed-emerald)](backend/tests)
[![Ruff](https://img.shields.io/badge/linter-ruff%20passed-blue)](backend/ruff.toml)
[![Vite TypeScript](https://img.shields.io/badge/frontend-React%2019%20%2B%20TS-cyan)](frontend)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI%20async-teal)](backend/app)
[![License](https://img.shields.io/badge/license-MIT-purple)](#)

MedLens is an autonomous clinical intelligence platform that bridges patient intake history and unstructured diagnostic reports. It provides deterministic reference-range intelligence, drug allergy conflict detection, longitudinal parameter variance tracking, multi-modal AI clinical synthesis with provenance traceability, and human-in-the-loop review controls.

---

## 1. Key Features

### 🩺 Structured Clinical Intake
- Captures patient presenting symptoms, existing chronic comorbidities, documented drug allergies, and active medication regimens.
- Automatically cross-referenced against all subsequent laboratory findings.

### 📄 Multi-Format Diagnostic Ingestion
- Ingests native lab panels via file upload (`PDF`, `DOCX`, `TXT`) or direct text paste.
- Employs cryptographic content hashing (`SHA-256`) to ensure idempotency and prevent duplicate processing.

### 🧬 Deterministic Parameter Normalization
- Resolves disparate clinical aliases (e.g. `Hb`, `Hgb`, `Hemoglobin`, `WBC`, `Leukocyte Count`) to authoritative canonical identifiers using an extensible 100+ parameter medical dictionary lookup.

### 📊 Mathematical Reference-Range Intelligence
- Parses standard clinical ranges (`13.0 - 17.0`, `< 200`, `> 60`).
- Classifies each observed value mathematically into `BELOW`, `WITHIN`, or `ABOVE` without relying on non-deterministic LLM logic for arithmetic decisions.

### ⚠️ Real-Time Safety Conflict Detection
- **Allergy Conflicts:** Detects when report clinical recommendations (e.g. *"Consider ACE inhibitor Lisinopril for renal protection"*) contradict documented patient allergies (*"Lisinopril: severe angioedema"*).
- **Medication Contraindications:** Detects critical drug-lab interactions (e.g., hyperkalemia with elevated Serum Potassium 5.6 mEq/L, or hypoglycemia accumulation risk with Glipizide and dropping eGFR).

### 📈 Longitudinal Parameter Trajectory
- Paired comparison between baseline and current diagnostic panels.
- Calculates absolute delta, percentage shift, directionality arrows (`INCREASED`, `DECREASED`, `STABLE`), and significance indicators.

### 🔍 Source Traceability & Provenance
- Every extracted numerical datum links directly to its verbatim excerpt in the source document, page number, and extraction confidence score.

### 🤖 AI Clinical Intelligence Summary
- Multi-modal plain-English clinical synthesis generated via Gemini 2.5 Flash / OpenAI using strict JSON schemas and system prompt isolation.
- Prominent medical safety disclaimer: *"MedLens assists clinical evaluation; all decisions must be verified by a licensed clinician."*

### 👨‍⚕️ Clinician Review & Audit Trail
- Human-in-the-loop sign-off: Clinicians can `Accept`, `Flag`, or `Reject` reports, edit lab values with audit reasons, and review immutable timestamps and user actions.

### ⚡ 1-Click Competition Demonstration Mode
- Pre-seeded synthetic clinical dataset (`Robert Martinez`, 54M, 2 reports, 18 parameters, 3 safety conflicts, longitudinal comparison, clarification questions, and review audit history).

---

## 2. Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Vanilla CSS Design System with Clinical Dark Theme and glassmorphism, Lucide Icons.
- **Backend:** Python 3.11+, FastAPI (Async), SQLAlchemy 2.0 (Async ORM), Pydantic v2.
- **Database:** SQLite (Async via `aiosqlite`) for zero-dependency local execution; PostgreSQL (Async via `asyncpg`) for containerized deployment; Alembic for migrations.
- **AI Backend:** Google Gemini API (`gemini-2.5-flash` via official `google-genai` SDK), swappable OpenAI fallback.
- **Testing & Quality:** Pytest, pytest-asyncio, Ruff linter, TypeScript compiler.

---

## 3. Project Structure

```
project1030/
├── backend/
│   ├── alembic/              # Async database migrations
│   ├── app/
│   │   ├── analysis/         # Deterministic reference engine & conflict detection
│   │   ├── api/              # FastAPI REST endpoints (auth, patients, reports, analysis)
│   │   ├── core/             # Auth (JWT), async database engine, config, errors
│   │   ├── extraction/       # PDF/DOCX document text extraction & AI provider
│   │   ├── models/           # SQLAlchemy async ORM models (User, Patient, Report, Conflict, etc.)
│   │   ├── normalization/    # Canonical parameter normalization dictionary
│   │   ├── schemas/          # Strict Pydantic request/response validation models
│   │   ├── services/         # Business logic services
│   │   ├── main.py           # FastAPI entrypoint, CORS, request IDs, error handlers
│   │   └── seed.py           # Synthetic clinical demonstration dataset seeder
│   ├── tests/                # 71 Unit & API integration tests
│   ├── Dockerfile
│   ├── pytest.ini
│   ├── requirements.txt
│   └── ruff.toml
├── frontend/
│   ├── src/
│   │   ├── api/              # Typed REST client
│   │   ├── components/       # UI components (Navbar, Sidebar, ProvenanceModal, EditModal)
│   │   ├── views/            # Screen views (Dashboard, Workspace, Upload, Results, Conflicts, Comparison, Insights)
│   │   ├── types.ts          # TypeScript domain interfaces
│   │   ├── index.css         # Clinical dark mode design tokens & CSS system
│   │   └── App.tsx           # Master clinical application router
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.app.json
├── docker-compose.yml
└── README.md
```

---

## 4. Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Set Up and Run Backend
```bash
cd backend
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# (Linux / macOS: source .venv/bin/activate)

# Install dependencies
pip install -r requirements.txt

# Seed the synthetic demonstration dataset
python -m app.seed

# Run the backend API server (runs on port 8001)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
The backend API is live at `http://localhost:8001`.
Interactive Swagger API documentation: `http://localhost:8001/docs`.

### 2. Set Up and Run Frontend
```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm run dev -- --port 3000
```
Open `http://localhost:3000` in your web browser.

### 3. Log In with Demonstration Credentials
- **Email:** `doctor@medlens.health`
- **Password:** `DemoPassword123!`
- Or simply click the purple **"Instant Clinician Demo Login"** button on the sign-in screen.

---

## 5. Running Automated Tests & Quality Checks

### Backend Unit & Integration Tests
```bash
cd backend
.\.venv\Scripts\pytest.exe tests
```
*Output: 71 passed tests covering reference ranges, alias normalization, conflict detection, JWT auth, patient permissions, and report ingestion.*

### Backend Linting
```bash
cd backend
.\.venv\Scripts\ruff.exe check app
```
*Output: All checks passed!*

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```
*Output: 1,849 modules transformed, 0 errors, production bundle generated in `dist/`.*

---

## 6. Docker Deployment

To launch the complete application stack with Docker Compose:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001`
- Health check: `http://localhost:8001/health`

---

## 7. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./medlens.db` | SQLAlchemy connection URL (supports SQLite & PostgreSQL) |
| `BACKEND_PORT` | `8001` | Port for FastAPI backend service |
| `JWT_SECRET` | `medlens_production_jwt_secret...` | HMAC secret for access tokens |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins for web clients |
| `AI_PROVIDER` | `gemini` | Configured AI engine (`gemini` or `openai`) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key |
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum file upload size in megabytes |

---

## 8. Safety & Compliance Architecture

1. **AI is Not the Source of Truth:** Extraction strictly produces candidate facts. Reference ranges and mathematical shifts are computed deterministically by Python code.
2. **Deterministic Conflict Rules:** Allergy and drug contraindications are detected using rule engines rather than trusting LLM reasoning for safety-critical interactions.
3. **Traceability:** No metric is presented without access to its underlying source excerpt and page number.
4. **Provider-in-the-Loop:** Clinical summaries require explicit review, audit notes, and physician sign-off.