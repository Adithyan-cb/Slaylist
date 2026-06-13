import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from starlette.staticfiles import StaticFiles

from backend.models import AuraResponse

load_dotenv()

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path=str(CACHE_DIR / "llm_cache.db")))

app = FastAPI(title="Slaylist API")

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("slaylist")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


with open("backend/sysPrompt.md") as f:
    PROMPT = f.read()

with open("backend/verifyPrompt.md") as f:
    VERIFY_PROMPT = f.read()


def _build_llm() -> ChatOpenAI:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "your_key_here":
        raise HTTPException(
            status_code=500,
            detail="AI service not configured. Set OPENROUTER_API_KEY in .env",
        )
    return ChatOpenAI(
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        api_key=SecretStr(key),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
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
    return {"status": "ok", "service": "slaylist-api"}


@app.post("/api/analyze")
async def analyze(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    images_bytes: list[bytes] = []
    total_size = 0
    MAX_TOTAL = 50 * 1024 * 1024

    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=422, detail="All files must be images.")

        data = await file.read()

        if len(data) == 0:
            raise HTTPException(
                status_code=400, detail=f"File '{file.filename}' is empty."
            )

        total_size += len(data)
        if total_size > MAX_TOTAL:
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
