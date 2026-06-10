import base64
import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from starlette.staticfiles import StaticFiles

from backend.models import AuraResponse

load_dotenv()

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


async def _call_ai(image_bytes: bytes) -> AuraResponse:
    llm = _build_llm()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    message = await llm.ainvoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_b64}",
                    },
                ]
            ),
        ]
    )

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
async def analyze(file: UploadFile = File(...)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="File must be an image.")

    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 5MB.")

    try:
        result = await _call_ai(image_bytes)
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
