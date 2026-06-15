import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from backend.models import AuraResponse

load_dotenv()

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

from sqlalchemy import create_engine
from langchain_core.globals import set_llm_cache
from backend.cache import TTLSQLAlchemyCache

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "86400"))
_cache_engine = create_engine(f"sqlite:///{CACHE_DIR / 'llm_cache.db'}")

set_llm_cache(TTLSQLAlchemyCache(engine=_cache_engine, ttl_seconds=CACHE_TTL))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("slaylist")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

LLM_MODEL = os.getenv("LLM_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

app = FastAPI(title="Slaylist API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Slaylist is experiencing technical difficulties. Try again."},
    )


with open("backend/sysPrompt.md") as f:
    PROMPT = f.read()

with open("backend/verifyPrompt.md") as f:
    VERIFY_PROMPT = f.read()


def _sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/:"*?<>|]', "_", filename)


def _build_llm() -> ChatOpenAI:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "your_key_here":
        raise HTTPException(
            status_code=500,
            detail="AI service not configured. Set OPENROUTER_API_KEY in .env",
        )
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=SecretStr(key),
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )


async def _verify_is_playlist(images_bytes: list[bytes]) -> bool:
    llm = _build_llm()
    content: list = [{"type": "text", "text": VERIFY_PROMPT}]
    for img_bytes in images_bytes:
        image_b64 = base64.b64encode(img_bytes).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{image_b64}",
            }
        )
    message = await llm.ainvoke([HumanMessage(content=content)])
    text = message.content
    if isinstance(text, list):
        text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in text
        )
    return text.strip().upper() == "YES"


VALID_TIERS = {
    "AURA GOD PLAYLIST",
    "SIGMA SOUNDWAVE",
    "MID RIZZ RADIO",
    "ALMOST COOKED PLAYLIST",
    "COOKED PLAYLIST",
    "NEGATIVE AURA",
}

TIER_RANGES: dict[str, tuple[int, int]] = {
    "AURA GOD PLAYLIST": (90, 100),
    "SIGMA SOUNDWAVE": (70, 89),
    "MID RIZZ RADIO": (50, 69),
    "ALMOST COOKED PLAYLIST": (30, 49),
    "COOKED PLAYLIST": (10, 29),
    "NEGATIVE AURA": (0, 9),
}


def _validate_response(parsed: dict) -> None:
    tier = parsed.get("tier")
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    score = parsed.get("score")
    if not isinstance(score, int) or score < 0 or score > 100:
        raise ValueError(f"Score out of range: {score}")

    lo, hi = TIER_RANGES[tier]
    if not (lo <= score <= hi):
        raise ValueError(
            f"Score {score} does not match tier '{tier}' (expected {lo}-{hi})"
        )


def _extract_json(raw: str) -> str:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)
    return raw.strip()


async def _call_ai(images_bytes: list[bytes]) -> AuraResponse:
    llm = _build_llm()

    content: list = [{"type": "text", "text": PROMPT}]
    for img_bytes in images_bytes:
        image_b64 = base64.b64encode(img_bytes).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{image_b64}",
            }
        )

    message = await llm.ainvoke([HumanMessage(content=content)])

    content = message.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    raw = _extract_json(content)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("AI returned invalid JSON.\nRAW: %s", raw)
        raise HTTPException(
            status_code=500,
            detail="AI returned an invalid response. Try a different screenshot.",
        )

    try:
        _validate_response(parsed)
        return AuraResponse(**parsed)
    except Exception:
        logger.exception(
            "Pydantic validation failed.\nPARSED: %s\nRAW: %s", parsed, raw
        )
        raise HTTPException(
            status_code=500,
            detail="AI returned an invalid response. Try a different screenshot.",
        )


@app.get("/api/health")
async def health():
    api_key = os.getenv("OPENROUTER_API_KEY")
    ai_configured = bool(api_key) and api_key != "your_key_here"
    cache_exists = (CACHE_DIR / "llm_cache.db").exists()
    return {
        "status": "ok",
        "service": "slaylist-api",
        "ai_configured": ai_configured,
        "cache_active": cache_exists,
    }


@app.post("/api/analyze")
@limiter.limit("15/minute")
async def analyze(request: Request, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    images_bytes: list[bytes] = []
    total_size = 0

    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

        safe_name = _sanitize_filename(file.filename)

        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=422, detail="All files must be images.")

        data = await file.read()

        if len(data) == 0:
            raise HTTPException(
                status_code=400, detail=f"File '{safe_name}' is empty."
            )

        total_size += len(data)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Total upload size exceeds 50MB limit.",
            )

        images_bytes.append(data)

    try:
        is_playlist = await _verify_is_playlist(images_bytes)
        if not is_playlist:
            raise HTTPException(
                status_code=422,
                detail="The uploaded image is not a songs playlist screenshot.",
            )

        result = await _call_ai(images_bytes)
        return result.model_dump()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /api/analyze")
        raise HTTPException(
            status_code=500,
            detail="Slaylist is experiencing technical difficulties. Try again.",
        )


app.mount("/", NoCacheStaticFiles(directory=str(STATIC_DIR), html=True), name="static")
