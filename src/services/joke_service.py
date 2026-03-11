import random
from pathlib import Path

JOKES_FILE = Path(__file__).parent.parent.parent / "jokes.md"
SEPARATOR = "ILOVEPIZZA" # Nice, isn't it?

def get_random_joke() -> str:
    text = JOKES_FILE.read_text(encoding="utf-8")
    jokes = [j.strip() for j in text.split(SEPARATOR) if j.strip()]
    if not jokes:
        return "No jokes available right now."
    return random.choice(jokes)
