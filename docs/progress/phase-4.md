# Phase 4 — Aura Score Download Feature

**Date:** 2026-06-13

## Objective
Implement the Instagram Story download feature — convert the result page into a 9:16 PNG when the user clicks "DOWNLOAD YOUR AURA SCORE".

---

## What was implemented

### 1. html-to-image CDN
- **`static/result.html`** — Added `<script src="https://unpkg.com/html-to-image@1.11.11/dist/html-to-image.js">` before the `result.js` script tag

### 2. Hidden Story Card (`#story-card`) in `result.html`
- `<div class="story-card" id="story-card">` placed before the footer
- **Dimensions:** 360×640px (9:16 portrait, captures at `pixelRatio: 3` → 1080×1920 for Instagram Story)
- **Layout (top-to-bottom):**
  - "Slaylist" header (monospace, muted)
  - Badge card (matching the result page: neon-border, score, `/100`, divider, tier title)
  - Roast line (centered, flex-grow to center vertically)
  - "slaylist.co" watermark (subtle, low opacity)
- **Visibility:** `position: fixed; top: 0; left: 0; z-index: -9999; opacity: 0; pointer-events: none` — always rendered in DOM but invisible, avoiding blank capture issues from off-screen positioning

### 3. Styles
- `.story-card` — fixed 360×640, dark background (`#1a1025`)
- `.story-card-inner` — flex column with padding, outer glow border via `::before` pseudo-element
- `.story-badge` — matches the result page badge (`#0f0a14` background, `#724e91` border, `box-shadow` glow, rounded corners)
- `.story-score` — Anton 96px, primary purple `#dfb7ff` with text-shadow glow
- `.story-tier` — Anton 20px, uppercase, wide letter-spacing
- `.story-roast` — JetBrains Mono 13px, muted text
- `.story-watermark` — JetBrains Mono 11px, 20% opacity

### 4. Download Button Wired
- **`static/result.html`** — Changed `onclick="copyLink()"` to `id="download-btn"` (removed old `copyLink` function)
- **`static/js/result.js`** — Added `downloadAuraScore()` async function:
  1. Populates `#story-score`, `#story-max-score`, `#story-tier`, `#story-roast` from localStorage data
  2. Sets `card.style.opacity = "1"` (card is always in DOM, just invisible)
  3. Calls `htmlToImage.toPng(card, { quality: 1, pixelRatio: 3 })`
  4. Triggers download as `slaylist-aura.png`
  5. Shows "GENERATING..." → "DOWNLOADED!" (green) → resets after 2s
  6. On error: shows "FAILED" → resets after 2s
  7. Always resets card opacity to 0 in `finally`

### 5. Removed
- **`copyLink()`** — Old function that just showed "SHARED!" temporarily, no download logic

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `opacity` toggle vs `display: none` / off-screen | `html-to-image` captures rendered content reliably; `display: none` can yield blank canvas; off-screen (`left: -9999px`) can be clipped by browser |
| `pixelRatio: 3` | 360×640 × 3 = 1080×1920 — true Instagram Story resolution |
| Badge mirrors result page | User wanted the story image to look like the result page (without buttons); badge reuses same visual language |
