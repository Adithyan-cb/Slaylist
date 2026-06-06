from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Slaylist API")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "slaylist-api"}


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
