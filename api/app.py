"""splash-of-hue: color memory game backend. Stateless API for Vercel serverless."""

import json
import os
import secrets
import sqlite3
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Local dev: serve from public/. Vercel: public/ is CDN-served via vercel.json rewrite.
_PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
_CALIBRATION_EXPORT_DIR = _TOOLS_DIR / ".export"

# --- Database (lazy-init, append-only) ---

DB_PATH = Path("/tmp/games.db") if os.environ.get("VERCEL") else Path("data/games.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    mode TEXT,
    picker_type TEXT,
    target_colors TEXT,
    guesses TEXT,
    scores TEXT,
    total_score REAL
);
"""

_db_initialized = False


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    global _db_initialized
    if _db_initialized:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)
    _db_initialized = True


# --- Challenge DB (Turso in production, local SQLite in dev) ---

CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
CHALLENGE_MAX_ENTRIES = 20

CHALLENGE_SCHEMA = """\
CREATE TABLE IF NOT EXISTS challenges (
    code TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    target_colors TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_played_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS challenge_entries (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    guesses TEXT NOT NULL,
    scores TEXT NOT NULL,
    total_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(code, name)
);
"""

_TURSO_URL = os.environ.get('TURSO_DATABASE_URL', '')
_TURSO_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')
_USE_TURSO = bool(_TURSO_URL and _TURSO_TOKEN)

_challenge_db_path = Path("/tmp/challenges.db") if os.environ.get("VERCEL") else Path("data/challenges.db")
_challenge_db_initialized = False


def _turso_base_url():
    url = _TURSO_URL
    if url.startswith('libsql://'):
        url = 'https://' + url[len('libsql://'):]
    return url.rstrip('/')


def _turso_pipeline(statements: list[tuple[str, list]]) -> list[dict]:
    """Execute SQL statements via Turso HTTP API. Returns list of result dicts."""
    requests = []
    for sql, args in statements:
        turso_args = []
        for a in (args or []):
            if a is None:
                turso_args.append({"type": "null"})
            elif isinstance(a, int):
                turso_args.append({"type": "integer", "value": str(a)})
            elif isinstance(a, float):
                turso_args.append({"type": "float", "value": a})
            else:
                turso_args.append({"type": "text", "value": str(a)})
        requests.append({"type": "execute", "stmt": {"sql": sql, "args": turso_args}})
    requests.append({"type": "close"})

    data = json.dumps({"requests": requests}).encode()
    req = urllib.request.Request(
        f"{_turso_base_url()}/v2/pipeline",
        data=data,
        headers={
            "Authorization": f"Bearer {_TURSO_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())

    results = []
    for r in body.get("results", []):
        if r.get("type") == "error":
            msg = r.get("error", {}).get("message", "Database error")
            raise HTTPException(status_code=500, detail=msg)
        if r.get("type") == "ok" and r.get("response", {}).get("type") == "execute":
            result = r["response"]["result"]
            cols = [c["name"] for c in result.get("cols", [])]
            rows = []
            for row in result.get("rows", []):
                rows.append({
                    cols[i]: (cell.get("value") if cell.get("type") != "null" else None)
                    for i, cell in enumerate(row)
                })
            results.append({"rows": rows, "affected_row_count": result.get("affected_row_count", 0)})
        else:
            results.append({"rows": [], "affected_row_count": 0})
    return results


def _get_challenge_db():
    conn = sqlite3.connect(_challenge_db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _init_challenge_db():
    global _challenge_db_initialized
    if _challenge_db_initialized:
        return
    if _USE_TURSO:
        stmts = [(s.strip(), []) for s in CHALLENGE_SCHEMA.strip().split(';') if s.strip()]
        _turso_pipeline(stmts)
    else:
        _challenge_db_path.parent.mkdir(parents=True, exist_ok=True)
        with _get_challenge_db() as conn:
            conn.executescript(CHALLENGE_SCHEMA)
    _challenge_db_initialized = True



def _generate_code(length: int = 6) -> str:
    """Generate a Crockford Base32 challenge code. PK constraint handles the ~0% collision case."""
    return ''.join(secrets.choice(CROCKFORD) for _ in range(length))


def _normalize_code(raw: str) -> str:
    """Normalize user-typed code: uppercase, common substitutions."""
    return raw.strip().upper().replace('I', '1').replace('L', '1').replace('O', '0').replace('-', '')


# --- API Models ---


class SubmitRequest(BaseModel):
    mode: str
    picker_type: str
    target_colors: list[dict]
    guesses: list[dict]
    scores: list[float]
    total_score: float


class ChallengeCreateRequest(BaseModel):
    mode: str
    target_colors: list[dict]
    name: str = Field(min_length=1, max_length=20)
    guesses: list[dict]
    scores: list[float]
    total_score: float


class ChallengeSubmitRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    guesses: list[dict]
    scores: list[float]
    total_score: float


class SaveCalibrationExportRequest(BaseModel):
    batches: list[dict]


# --- App ---

app = FastAPI(title="splash-of-hue")


@app.post("/api/game/submit")
async def submit_game(req: SubmitRequest):
    try:
        init_db()
        game_id = str(uuid.uuid4())[:8]
        with get_db() as conn:
            conn.execute(
                "INSERT INTO games (id, created_at, mode, picker_type, target_colors, guesses, scores, total_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (game_id, datetime.now(timezone.utc).isoformat(), req.mode, req.picker_type,
                 json.dumps(req.target_colors), json.dumps(req.guesses),
                 json.dumps(req.scores), req.total_score),
            )
    except Exception as e:
        import logging
        logging.warning("Game persist failed: %s", e)
    return {"ok": True}


@app.post("/api/challenge")
def create_challenge(req: ChallengeCreateRequest):
    _init_challenge_db()
    now = datetime.now(timezone.utc).isoformat()
    code = _generate_code()
    entry_id = str(uuid.uuid4())[:8]
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    tc_json = json.dumps(req.target_colors)
    g_json = json.dumps(req.guesses)
    s_json = json.dumps(req.scores)
    stmts = [
        ("INSERT INTO challenges (code, mode, target_colors, created_at, last_played_at) VALUES (?, ?, ?, ?, ?)",
         [code, req.mode, tc_json, now, now]),
        ("INSERT INTO challenge_entries (id, code, name, guesses, scores, total_score, created_at) "
         "VALUES (?, ?, ?, ?, ?, ?, ?)",
         [entry_id, code, name, g_json, s_json, req.total_score, now]),
        ("SELECT name, total_score, scores, created_at FROM challenge_entries WHERE code = ? ORDER BY total_score DESC",
         [code]),
    ]
    if _USE_TURSO:
        results = _turso_pipeline(stmts)
        entries = results[2] if len(results) > 2 else {"rows": []}
    else:
        with _get_challenge_db() as conn:
            conn.execute(stmts[0][0], stmts[0][1])
            conn.execute(stmts[1][0], stmts[1][1])
            cursor = conn.execute(stmts[2][0], stmts[2][1])
            cols = [d[0] for d in cursor.description]
            entries = {"rows": [dict(zip(cols, row)) for row in cursor.fetchall()]}
    return {"code": code, "mode": req.mode, "target_colors": req.target_colors, "entries": entries["rows"]}


@app.get("/api/challenge/{raw_code}")
def get_challenge(raw_code: str):
    _init_challenge_db()
    code = _normalize_code(raw_code)
    stmts = [
        ("SELECT mode, target_colors FROM challenges WHERE code = ?", [code]),
        ("SELECT name, total_score, scores, created_at FROM challenge_entries WHERE code = ? ORDER BY total_score DESC", [code]),
    ]
    if _USE_TURSO:
        results = _turso_pipeline(stmts)
        challenge_result, entries = results[0], results[1]
    else:
        with _get_challenge_db() as conn:
            c1 = conn.execute(stmts[0][0], stmts[0][1])
            cols1 = [d[0] for d in c1.description]
            challenge_result = {"rows": [dict(zip(cols1, row)) for row in c1.fetchall()]}
            c2 = conn.execute(stmts[1][0], stmts[1][1])
            cols2 = [d[0] for d in c2.description]
            entries = {"rows": [dict(zip(cols2, row)) for row in c2.fetchall()]}
    if not challenge_result["rows"]:
        raise HTTPException(status_code=404, detail="Challenge not found")
    challenge = challenge_result["rows"][0]
    tc = challenge["target_colors"]
    target_colors = json.loads(tc) if isinstance(tc, str) else tc
    return {"code": code, "mode": challenge["mode"], "target_colors": target_colors, "entries": entries["rows"]}


@app.post("/api/challenge/{raw_code}")
def submit_challenge_entry(raw_code: str, req: ChallengeSubmitRequest):
    _init_challenge_db()
    code = _normalize_code(raw_code)
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    now = datetime.now(timezone.utc).isoformat()
    entry_id = str(uuid.uuid4())[:8]
    g_json, s_json = json.dumps(req.guesses), json.dumps(req.scores)

    # Pipeline 1: all reads (validate challenge, count, name uniqueness)
    read_stmts = [
        ("SELECT mode, target_colors FROM challenges WHERE code = ?", [code]),
        ("SELECT COUNT(*) as cnt FROM challenge_entries WHERE code = ?", [code]),
        ("SELECT 1 FROM challenge_entries WHERE code = ? AND name = ?", [code, name]),
    ]
    if _USE_TURSO:
        reads = _turso_pipeline(read_stmts)
        challenge_result, count_result, name_result = reads[0], reads[1], reads[2]
    else:
        with _get_challenge_db() as conn:
            c1 = conn.execute(read_stmts[0][0], read_stmts[0][1])
            cols1 = [d[0] for d in c1.description]
            challenge_result = {"rows": [dict(zip(cols1, row)) for row in c1.fetchall()]}
            c2 = conn.execute(read_stmts[1][0], read_stmts[1][1])
            cols2 = [d[0] for d in c2.description]
            count_result = {"rows": [dict(zip(cols2, row)) for row in c2.fetchall()]}
            c3 = conn.execute(read_stmts[2][0], read_stmts[2][1])
            cols3 = [d[0] for d in c3.description]
            name_result = {"rows": [dict(zip(cols3, row)) for row in c3.fetchall()]}

    if not challenge_result["rows"]:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if count_result["rows"] and int(count_result["rows"][0]["cnt"]) >= CHALLENGE_MAX_ENTRIES:
        raise HTTPException(status_code=409, detail="Challenge is full (max 20 players)")
    if name_result["rows"]:
        raise HTTPException(status_code=409, detail="Name already taken for this challenge")

    # Pipeline 2: insert + update + leaderboard
    write_stmts = [
        ("INSERT INTO challenge_entries (id, code, name, guesses, scores, total_score, created_at) "
         "VALUES (?, ?, ?, ?, ?, ?, ?)",
         [entry_id, code, name, g_json, s_json, req.total_score, now]),
        ("UPDATE challenges SET last_played_at = ? WHERE code = ?", [now, code]),
        ("SELECT name, total_score, scores, created_at FROM challenge_entries WHERE code = ? ORDER BY total_score DESC",
         [code]),
    ]
    if _USE_TURSO:
        writes = _turso_pipeline(write_stmts)
        entries = writes[2]
    else:
        with _get_challenge_db() as conn:
            conn.execute(write_stmts[0][0], write_stmts[0][1])
            conn.execute(write_stmts[1][0], write_stmts[1][1])
            c4 = conn.execute(write_stmts[2][0], write_stmts[2][1])
            cols4 = [d[0] for d in c4.description]
            entries = {"rows": [dict(zip(cols4, row)) for row in c4.fetchall()]}

    challenge = challenge_result["rows"][0]
    tc = challenge["target_colors"]
    target_colors = json.loads(tc) if isinstance(tc, str) else tc
    return {"code": code, "mode": challenge["mode"], "target_colors": target_colors, "entries": entries["rows"]}


def _require_local_dev():
    if os.environ.get("VERCEL"):
        raise HTTPException(status_code=404)


@app.get("/__dev/calibration-source", response_class=PlainTextResponse, dependencies=[Depends(_require_local_dev)])
async def calibration_source():
    return (_TOOLS_DIR / "calibration.jsx").read_text(encoding="utf-8")


@app.post("/__dev/save-calibration-export", dependencies=[Depends(_require_local_dev)])
async def save_calibration_export(req: SaveCalibrationExportRequest):

    _CALIBRATION_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"scoring-calibration-{timestamp}.json"
    path = _CALIBRATION_EXPORT_DIR / filename
    path.write_text(json.dumps(req.batches, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "filename": filename,
        "path": str(path.relative_to(_TOOLS_DIR.parent)),
    }


# --- Challenge page: OG tags for link previews, JS redirect to app ---

import html as _html
from fastapi.responses import HTMLResponse


@app.get("/c/{code}", response_class=HTMLResponse)
async def challenge_page(code: str):
    safe = _html.escape(code[:10])
    og_title = "splash of hue — can you beat my colors?"
    og_desc = "I just played a round. Same five colors, your turn."
    return (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<title>{og_title}</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta property="og:title" content="{og_title}">'
        f'<meta property="og:description" content="{og_desc}">'
        '<meta property="og:image" content="https://hue.exogradient.dev/og.png">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{og_title}">'
        f'<meta name="twitter:description" content="{og_desc}">'
        '<meta name="twitter:image" content="https://hue.exogradient.dev/og.png">'
        f"<script>window.location.replace('/?challenge={safe}');</script>"
        '</head><body style="background:#080808">'
        f'<noscript><a href="/?challenge={safe}" style="color:#ededed">Open challenge</a></noscript>'
        '</body></html>'
    )


# Local dev: serve static files from public/. On Vercel, public/ is CDN-served.
if not os.environ.get("VERCEL") and _PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_PUBLIC_DIR), html=True), name="static")
