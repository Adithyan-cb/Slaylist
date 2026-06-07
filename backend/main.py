from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from starlette.staticfiles import StaticFiles

app = FastAPI(title="Slaylist API")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

DUMMY_RESPONSE = {
    "score": 72,
    "max_score": 100,
    "tier": "A",
    "tier_title": "Sigma Soundwave",
    "tier_tagline": "Silent but deadly. Your playlist goes hard.",
    "breakdown": [
        {
            "category": "Vibe Selection",
            "score": 85,
            "comment": "You know how to set the mood",
        },
        {
            "category": "Song Diversity",
            "score": 70,
            "comment": "Genre range is decent",
        },
        {
            "category": "Cover Art",
            "score": 60,
            "comment": "Some covers are giving high school project",
        },
        {
            "category": "Deep Cuts",
            "score": 75,
            "comment": "Scrolled past the mainstream",
        },
        {
            "category": "Overall Vibe",
            "score": 78,
            "comment": "Consistent energy throughout",
        },
    ],
    "penalties": [
        {
            "reason": "Too many mainstream hits",
            "deduction": 8,
            "comment": "Basic playlist behavior",
        },
        {
            "reason": "Song order chaos",
            "deduction": 5,
            "comment": "Mood whiplash between tracks",
        },
    ],
    "specific_roast": (
        "Your playlist is giving 'I only listen to the top 5 songs on every album"
        " and call it a personality.' The transition from lo-fi beats to death"
        " metal was... a choice."
    ),
    "prescription": [
        {
            "tip": "Add some underground artists to balance the energy",
            "gain": "+15 AURA",
        },
        {
            "tip": "Organize tracks by BPM for a smoother flow",
            "gain": "+10 AURA",
        },
        {
            "tip": "Swap 3 mainstream bangers for hidden gems",
            "gain": "+20 AURA",
        },
    ],
    "verdict": (
        "Your taste is objectively good, but dangerously close to basic. You have"
        " potential. Don't waste it."
    ),
}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "slaylist-api"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    return DUMMY_RESPONSE


app.mount("/", NoCacheStaticFiles(directory=str(STATIC_DIR), html=True), name="static")
