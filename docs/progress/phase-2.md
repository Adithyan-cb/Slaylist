# Phase 2 — Real AI Integration & Simplification

**Date:** 2026-06-10

## Objective
Replace dummy JSON with real AI analysis and simplify the app to focus on the core features: aura score and roast.

---

## What was done

### 1. Backend — Real AI Integration

**AI Provider:** OpenRouter (Nvidia Nemotron Nano 12B VL) via LangChain ChatOpenAI
- Model: `nvidia/nemotron-nano-12b-v2-vl:free`
- Uses the OpenAI-compatible API on OpenRouter's endpoint
- Vision model analyzes playlist screenshots directly

**Files changed:**

- **`backend/main.py`** — Replaced dummy JSON response with real AI call:
  - `_build_llm()` — Initializes ChatOpenAI with OpenRouter base URL, API key from `.env`, and the multimodal model
  - `_call_ai()` — Accepts `list[bytes]`, encodes each image to base64 and sends all alongside the prompt in one request; extracts JSON from the response, validates with Pydantic
  - `_extract_json()` — Robust JSON extraction handling markdown code blocks, stray characters, trailing commas
  - Full validation: each file must be an image, non-empty, combined total max 50MB
  - Error handling: malformed JSON, Pydantic validation failures, missing API key, generic server errors
  - `POST /api/analyze` accepts `list[UploadFile]` for multi-screenshot support (up to 3 images)

- **`backend/models.py`** — Created Pydantic `AuraResponse` model with fields: `score`, `max_score`, `tier`, `tier_title`, `tagline`, `specific_roast`

- **`backend/sysPrompt.md`** — Gen Z music critic persona prompt instructing the AI to return structured JSON with score, tier, tagline, and roast

- **`.env`** — Added `OPENROUTER_API_KEY` for API authentication

### 2. Response Schema Simplification

The original schema from Phase 1 had: breakdown (5 categories), penalties, prescription (3 recovery tips), verdict, score, tier, roast.

**Removed from schema:**
- `BreakdownItem` class and `breakdown` field (5 vibe categories with scores)
- `PenaltyItem` class and `penalties` field (deductions)
- `prescription` (recovery tips)
- `verdict`

**Kept:** `score`, `max_score`, `tier`, `tier_title`, `tagline`, `specific_roast`

The system prompt was updated to only request the remaining fields.

### 3. Frontend — Result Page Simplification

**`static/result.html`**:
- **Removed:** VIBE BREAKDOWN section (category breakdown with comments/penalties)
- **Removed:** Footer (later restored by request)
- **Kept:** Score badge card (score, max score, tier title, tagline)
- **Kept:** Roast section (large quote-styled roast paragraph)
- **Kept:** DOWNLOAD YOUR PLAYLIST AURA SCORE share section with download button and "TRY ANOTHER" button

**`static/js/result.js`**:
- Stripped all breakdown/penalties rendering logic
- Now only populates: score, max_score, tier_title, tagline, specific_roast
- Retained: localStorage read/write, redirect on missing data, try-another handler

### 4. Frontend — Landing Page Adjustments

**`static/index.html`**:
- **Removed:** CTA section ("READY TO CHECK YOUR PLAYLIST AURA?")
- **Kept:** HOW IT WORKS section (3-step: Upload, Analyze, Get Roasted)
- **Kept:** AURA TIERS showcase (6 tier cards with distinct styling)
- **Kept:** Hero section, upload zone, loading state, error modal
- Updated the GET ROASTED step text to Gen Z wording: "Catch your aura score and get absolutely roasted no cap"

### 5. Multi-Screenshot Support

**`backend/main.py`**:
- Endpoint changed from single `UploadFile` to `list[UploadFile]`
- Iterates over all uploaded files, validates each is an image, accumulates total size
- Combined size limit: **50MB** (up from 5MB to accommodate multiple screenshots)
- Sends all images to the AI vision model in one request so it can analyze the playlist across multiple screenshots

**`backend/sysPrompt.md`**:
- Prompt updated to mention "screenshots (1-3 images)" and "across all provided screenshots"

**`static/index.html`**:
- File input has `multiple` attribute
- Drop zone text: "Drop your playlist screenshots here or click to browse (up to 3)"
- Accept hint: "JPG, PNG, up to 3, max 50MB total"

**`static/js/app.js`**:
- Replaced single `selectedFile` with `selectedFiles` array
- `handleFiles()` takes a FileList, slices to first 3, displays all filenames
- FormData appends all files under the `files` key
- Validation checks `selectedFiles.length === 0` instead of `!selectedFile`

### 6. Footers

Added matching footers to both pages with "SLAYLIST" heading and "GITHUB" link.

---

## Key Differences from Original Phase 2 Plan (PRD)

| PRD Plan | Actual Implementation |
|----------|----------------------|
| Google GenAI (Gemini) via `langchain-google-genai` | OpenRouter (Nvidia Nemotron) via `langchain-openai` |
| Full schema (breakdown, penalties, prescription, verdict) | Simplified schema (score, tier, roast only) |
| All result page sections rendered | Only score badge and roast rendered |
| - | HOW IT WORKS / AURA TIERS sections kept on landing page |

---

## Verification

- `GET /api/health` → `200 OK`
- `POST /api/analyze` with real screenshot → returns AI-generated score + roast
- `POST /api/analyze` with non-image → `422 File must be an image`
- `POST /api/analyze` with empty file → `400 Uploaded file is empty`
- `POST /api/analyze` with 2-3 screenshots → AI analyzes all together
- `POST /api/analyze` with files > 50MB combined → `413 Total file size too large`
- `POST /api/analyze` with a non-image in a multi-file upload → `422 File must be an image`
- Frontend upload → localStorage → redirect → render flow intact
- Score badge displays correctly on result page
- Roast text populates from `specific_roast`
- Try Another button clears localStorage and redirects
