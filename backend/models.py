from pydantic import BaseModel


class AuraResponse(BaseModel):
    score: int = 50
    max_score: int = 100
    tier: str = "NO AURA AVAILABLE"
    tier_title: str = "Mysterious Stranger"
    tagline: str = "We couldn't read your aura"
    specific_roast: str = "No roast available."
