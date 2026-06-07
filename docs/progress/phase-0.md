# Phase 0 — Project Setup

**Date:** 2026-06-07

## Objective
Set up the project directory structure, config files, dependencies, and verify the server runs before any app logic is built.

## What was done

### 1. Directory Structure Created
```
slaylist/
├── backend/
│   └── main.py              # FastAPI application
├── static/
│   ├── index.html            # Landing page (from docs prototype)
│   ├── result.html           # Result page (from docs prototype)
│   └── js/
│       ├── app.js            # Upload → POST → localStorage → redirect
│       └── result.js         # Read localStorage → render result dynamically
├── .env                      # GOOGLE_API_KEY placeholder (for Phase 2)
├── .gitignore                # Python + dotenv + venv ignores
├── requirements.txt          # Phase 1 deps (AI pkgs commented out for Phase 2)
└── slaylist-venv/            # Python virtual environment (pre-existing)
```

### 2. Key Files Created

**`backend/main.py`**
- FastAPI app with `/api/health` endpoint
- Static file mount at `/` serving `./static/` with `html=True` (SPA-like index.html fallback)
- API routes defined before static mount to take precedence

**`static/index.html`**
- Adapted from `docs/slaylist-mainpage/code.html`
- Full design: hero section, upload zone (drag-and-drop + click), calculate button, how-it-works, aura tiers showcase, CTA section
- Added hidden loading section (spinner + "The Vibe Bureau is analyzing...")
- Added hidden error section (warning + inline error message + retry button)
- IDs wired: `#drop-zone`, `#file-input`, `#calculate-btn`, `#upload-section`, `#loading-section`, `#error-section`
- Bottom CTA button smooth-scrolls to upload section and opens file picker

**`static/result.html`**
- Adapted from `docs/slaylist-resultpage/code.html`
- All sections ID'd for dynamic population: `#score`, `#tier-title`, `#tagline`, `#breakdown`, `#penalties`, `#prescription`, `#roast`, `#verdict`, `#try-another`
- Includes mobile bottom nav bar

**`static/js/app.js`**
- Handles file selection via click and drag-and-drop
- Shows file preview with checkmark + filename
- On "Calculate Aura" click: validates file → shows loading → `fetch()` POST to `/api/analyze` → saves response to `localStorage` → redirects to `/result.html`
- On error: shows error section with message

**`static/js/result.js`**
- On page load: checks `localStorage` for `aura` data
- If empty: redirects to `/`
- If data exists: populates score, tier, tagline, breakdown, penalties, prescription, roast, verdict
- "Try Another" button: clears `localStorage` → redirects to `/`

**`requirements.txt`**
- Phase 1 deps installed: `fastapi[standard]==0.111.0`, `uvicorn[standard]==0.30.0`, `python-multipart==0.0.9`, `python-dotenv==1.0.0`
- Phase 2 AI deps commented out: `langchain`, `langchain-google-genai`, `google-generativeai`, `httpx`

### 3. Dependencies Installed
```bash
pip install -r requirements.txt
```
All packages installed successfully into `slaylist-venv/`.

### 4. Verification
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
- `GET /api/health` → `200 OK` → `{"status":"ok","service":"slaylist-api"}`
- `GET /` → `200` serves `index.html`
- `GET /result.html` → `200` serves `result.html`

### 5. How to Run
```bash
source slaylist-venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```
Open `http://localhost:8000` in browser.

## Ready for Phase 1
- Complete UI built and served
- JS logic wired for upload → API call → result display
- Backend dummy endpoint (`POST /api/analyze`) needs to be added
