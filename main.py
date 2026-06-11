from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json, os, time, subprocess

app = FastAPI(title="Draw Guess Game")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_FILE     = "leaderboard.json"
PLAYER_FILE = "current_player.json"

# *** SET THIS TO YOUR GAME FOLDER PATH ***
GAME_DIR    = r"E:\draw_guess_2hands"


# ---------- helpers ----------

def load_db() -> list:
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r") as f:
            content = f.read().strip()

            if not content:
                return []

            return json.loads(content)

    except json.JSONDecodeError:
        # auto-repair corrupted/empty file
        with open(DB_FILE, "w") as f:
            json.dump([], f)
        return []

def save_db(data: list):
    tmp_file = DB_FILE + ".tmp"

    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=2)

    os.replace(tmp_file, DB_FILE)  # atomic replace

def get_current_player() -> str:
    try:
        if not os.path.exists(PLAYER_FILE):
            return "Anonymous"

        with open(PLAYER_FILE, "r") as f:
            data = json.load(f)

        name = data.get("name", "").strip()
        return name if name else "Anonymous"

    except:
        return "Anonymous"


# ---------- schemas ----------

class ScoreIn(BaseModel):
    name: str
    time_seconds: float

class PlayerIn(BaseModel):
    name: str


# ---------- routes ----------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/launch")
async def launch_game(player: PlayerIn):
    name = player.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    # save player name
    with open(PLAYER_FILE, "w") as f:
        json.dump({"name": name}, f)

    # launch game in NEW console from another folder
    try:
        subprocess.Popen(
            # ["python", "main.py"],
            ["cmd", "/k", "python main.py"],
            cwd=GAME_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
             
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not launch game: {e}")

    return {"status": "ok", "name": name}


@app.get("/api/current_player")
async def current_player():
    """Game calls this to find out who is playing."""
    return {"name": get_current_player()}


@app.get("/api/leaderboard")
async def get_leaderboard():
    data = load_db()
    data.sort(key=lambda x: float(x.get("best_time", 1e9)))
    return data[:10]


@app.post("/api/score")
async def post_score(score: ScoreIn):
    # ignore client name if empty / fake
    name = score.name.strip()

    if not name or name.lower() in ["player", "anonymous"]:
        name = get_current_player()

    if not name:
        name = "Anonymous"

    data = load_db()
    existing = next((p for p in data if p["name"].lower() == name.lower()), None)

    if existing:
        if score.time_seconds < existing["best_time"]:
            existing["best_time"]     = round(score.time_seconds, 2)
            existing["best_time_str"] = f"{score.time_seconds:.1f}s"
            existing["updated_at"]    = time.time()
    else:
        data.append({
            "name":          name,
            "best_time":     round(score.time_seconds, 2),
            "best_time_str": f"{score.time_seconds:.1f}s",
            "created_at":    time.time(),
            "updated_at":    time.time(),
        })

    save_db(data)
    return {"status": "ok"}