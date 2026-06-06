# Slaylist — Product Requirements Document

**Version:** 2.0  
**Date:** 2026-06-06  
**Status:** Draft

---

## 1. Project Description

**Slaylist** is a fun web app where users upload a screenshot of any Spotify playlist and get an **Aura Score** — a Gen Z-style rating of their music taste out of 100.

The app uses Google GenAI (Gemini) with vision capabilities to analyze the playlist name, visible songs, cover art, and overall vibe. It then roasts or praises the user with a shareable dark-purple badge optimized for Instagram Stories.

**How it works:**
1. User takes a screenshot of any Spotify playlist
2. Uploads it on the landing page
3. AI analyzes the screenshot and assigns a score across 5 categories
4. User receives a dark, glowing **Aura Badge** with their score, tier title, a personalized roast, and 3 tips to "recover" their aura
5. User screenshots the badge or downloads it as a story-ready image

**The vibe:** Playful, unhinged, meme-heavy. The AI speaks like a Gen Z critic — funny but not cruel. The design is dark purple (#22162b palette), bold typography (Anton + monospace), and minimalist.

---

## 2. Target Audience

- **Gen Z (16–26):** TikTok/Instagram power users looking for shareable content
- **Music obsessives:** People who curate playlists religiously and want validation or a roast
- **Meme culture participants:** Users who engage with ironic, quotable humor
- **Friend groups:** People who want to compare scores in group chats or social media

**Primary device:** Mobile web (70%+ traffic). The output badge is optimized for Instagram Stories.

---

## 3. Workflow

### User Flow
```
[Landing Page — index.html]
    → User selects playlist screenshot
    → Clicks "Calculate Aura"
    → JS shows loading state
    → JS fetch() POSTs to /api/analyze

[FastAPI Backend]
    → Receives image
    → Calls Google GenAI via LangChain (async, 5–10 seconds)
    → Returns JSON result

[Frontend — app.js]
    → Stores JSON in localStorage
    → Redirects to result.html

[Result Page — result.html]
    → Reads localStorage on page load
    → Renders full result page (badge, breakdown, roast, recovery, verdict)
    → User screenshots or downloads story image
    → Clicks "Try Another" → clears localStorage → back to index.html
```

### Data Flow
```
Browser (Vanilla JS + Tailwind)
    → POST /api/analyze (multipart image upload)

FastAPI Backend
    → Receives image → calls LangChain → Google GenAI Vision
    → Returns JSON aura result

Browser
    → localStorage.setItem('aura', JSON.stringify(result))
    → window.location.href = '/result.html'
    → result.html reads localStorage and renders
```

### Why localStorage?
- Survives page refresh, new tabs, and browser restart
- No backend state needed (no database, no temp files, no Redis)
- If localStorage is empty on result.html, redirect to index.html with "Upload a playlist first"
- Data auto-cleared when user clicks "Try Another"

---

## 4. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | HTML + Tailwind CSS (CDN) + Vanilla JavaScript | Zero build step, zero frameworks, open-and-edit files |
| **Backend API** | FastAPI + Uvicorn | Async-native, lightweight, perfect for single JSON endpoint |
| **AI** | LangChain + Google GenAI (Gemini) | Vision model reads screenshots, cheaper/faster than OpenAI for many use cases |
| **Data Storage** | Browser localStorage | No database, no Redis, no temp files. Result lives in user's browser. |
| **Story Export** | html-to-image (CDN) | Client-side DOM-to-PNG conversion, no server processing |
| **Deploy** | Railway or Render | One-click hosting for FastAPI + static files |

---

## 5. Requirements (Packages to Install)

### Backend (`requirements.txt`)

```
fastapi[standard]==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
langchain==0.2.0
langchain-google-genai==1.0.0
google-generativeai==0.6.0
python-dotenv==1.0.0
httpx==0.27.0
```

### Frontend (CDN — no build step, no package.json)

Load these in your HTML `<head>`:

- **Tailwind CSS:** `https://cdn.tailwindcss.com` (dev) or compiled `output.css` (prod)
- **Google Fonts:** Anton, JetBrains Mono, Inter
- **html-to-image:** `https://unpkg.com/html-to-image@1.11.11/dist/html-to-image.js`
- **Lucide Icons:** `https://unpkg.com/lucide@latest` (optional)

### System Requirements

- **Python** 3.10+
- **Google API Key** with Gemini vision model access (Gemini 1.5 Pro or Flash)

---

## 6. Development Phases

### Phase 1 — Frontend + Dummy API

**Goal:** Build the complete UI with fake data. Prove the flow works end-to-end.

**Backend:**
- Scaffold FastAPI project (`main.py`)
- Create `POST /api/analyze` endpoint
- Accept `UploadFile`, ignore the actual image
- Return hardcoded dummy JSON (matching the full schema)
- Add `GET /api/health` for sanity checks

**Frontend:**
- Create `index.html` — landing page with:
  - Hero headline ("How much AURA does your playlist have?")
  - Upload form (file input, drag-and-drop optional)
  - "Calculate Aura" button
  - Loading state (spinner + "The Vibe Bureau is analyzing...")
  - Privacy badge ("We don't store anything")
  - Example aura cards (static, 3 fake results)
- Create `result.html` — full result page matching the screenshot design:
  - Aura Badge (score / 10,000, tier title, tagline)
  - Vibe Breakdown (5 categories with scores and comments)
  - Aura Recovery Plan (3 numbered tips with +aura pills)
  - Specific Roast paragraph
  - Verdict paragraph
  - Share section ("Screenshot this. Flex it.")
  - "Try Another Playlist" button
  - Footer
- Create `js/app.js`:
  - Handle file selection and preview
  - `fetch()` POST to `/api/analyze`
  - Show loading state while waiting
  - On success: `localStorage.setItem('aura', JSON.stringify(data))`
  - Redirect to `result.html`
- Create `js/result.js`:
  - On page load: read `localStorage.getItem('aura')`
  - If empty: redirect to `index.html`
  - If data exists: render all sections dynamically
  - Handle "Try Another" click: `localStorage.removeItem('aura')` → redirect

**Test:**
- Upload any image → loading appears → result page loads → dummy data renders correctly
- Refresh result page → data still there (localStorage works)
- Click "Try Another" → back to landing page
- Screenshot badge on mobile → check if it looks good for Instagram Story

**Deliverable:** A fully designed app that looks complete but uses fake AI data.

---

### Phase 2 — Real AI Integration

**Goal:** Replace dummy JSON with real Google GenAI analysis.

**Backend:**
- Add `.env` with `GOOGLE_API_KEY`
- Install LangChain Google GenAI integration
- Build the prompt template:
  - Persona: "You are a Gen Z music critic working for the Vibe Bureau..."
  - Input: playlist screenshot image bytes
  - Task: analyze playlist name, visible songs, genre, cover art, song count
  - Output: structured JSON matching the exact schema
- Create Pydantic model for the response:
  - `score`, `max_score`, `tier`, `tier_title`, `tier_tagline`
  - `breakdown[]` — category, score, comment
  - `penalties[]` — reason, deduction, comment
  - `specific_roast` — string
  - `prescription[]` — tip, gain
  - `verdict` — string
- Wire `POST /api/analyze` to:
  1. Read uploaded image bytes
  2. Send to Gemini via LangChain with prompt
  3. Parse structured JSON response
  4. Return JSON to frontend
- Add error handling:
  - If AI fails or times out → return `{ error: "The Vibe Bureau is experiencing technical difficulties. Try again." }`
  - If file is not an image → return `{ error: "Upload a valid image (JPG or PNG)." }`
  - If AI returns malformed JSON → fallback to a generic roast + mid-tier score

**Frontend:**
- Update `app.js` to handle error responses:
  - Show inline error message instead of redirecting
  - "The Vibe Bureau rejected your file. Try again."
- Update `result.js` to handle edge cases:
  - If `score` is missing, show "Analysis failed" state

**Test:**
- Upload real Spotify playlist screenshot
- Verify score, tier, and roast make sense
- Test with bad file (PDF) → error message appears
- Test with blurry screenshot → see if AI still works

**Deliverable:** Fully functional app with real AI analysis.

---

### Phase 3 — story image downlad

**What:** A button that downloads the result badge as a 1080×1920 PNG (Instagram Story size).

**How:**
- In `result.html`, create a hidden container `#story-card`:
  - Aspect ratio: 9:16 (portrait)
  - Dimensions: 400×711px (or 1080×1920 for high-res)
  - Contains: badge, score, tier title, one roast line, and "slaylist.co" watermark
  - Styled with the same dark purple palette but optimized for vertical format
- Load `html-to-image` CDN in `result.html`
- Add "Download for Story" button at the bottom of the result page
- On click:
  ```javascript
  const node = document.getElementById('story-card');
  htmlToImage.toPng(node, { quality: 1, pixelRatio: 2 })
    .then(dataUrl => {
      const link = document.createElement('a');
      link.download = 'slaylist-aura.png';
      link.href = dataUrl;
      link.click();
    });
  ```
- Test: download the PNG → open on phone → post to Instagram Story → verify it fills the screen and text is readable


*End of Document*
