"""
FDE · Assignment 1 · Python AI Service  (this is the real assignment)
=====================================================================
A small FastAPI service that translates English → Mexican Spanish with:
  - an LLM call            (lib/llm.py)
  - a two-tier cache       (lib/cache.py)  — memory + SQLite
  - structured logging     (lib/logger.py) — provided, wired for you

The Node gateway forwards the browser's requests here. You implement the
TODOs so the widget lights up. Run:

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # then add your API key
    uvicorn app:app --reload --port 8000
"""
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lib.cache import TwoTierCache
from lib.llm import translate_text
from lib.logger import get_logger

load_dotenv(Path(__file__).with_name(".env"))

MODEL = os.getenv("MODEL", "gpt-5.6-luna")
DB_PATH = os.getenv("TRANSLATION_DB_PATH", "translations.db")

app = FastAPI(title="FDE Live Translate — AI Service")
log = get_logger("ai-service")
cache = TwoTierCache(DB_PATH)

# request/response shapes ----------------------------------------------------
class TranslateIn(BaseModel):
    text: str
    target: str = "es-MX"

class BatchIn(BaseModel):
    texts: list[str]
    target: str = "es-MX"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "Invalid request", "detail": exc.errors()})


@app.on_event("startup")
async def startup():
    await cache.init()
    log.info("ai_service_started", extra={"model": MODEL, "db": DB_PATH})


def request_id_from(request: Request) -> str:
    return request.headers.get("x-request-id") or str(uuid.uuid4())


# --- core: translate one string --------------------------------------------
async def translate_one(text: str, target: str, request_id: str | None = None) -> dict:
    """Translate a single string, using the cache first.

    Returns a dict shaped exactly like the widget expects:
        {"translated": str, "cached": bool, "latencyMs": int, "model": str}
    """
    original_text = text or ""
    text = original_text.strip()
    if not text:
        result = {"translated": "", "cached": False, "latencyMs": 0, "model": MODEL}
        log.info(
            "translate",
            extra={"request_id": request_id, "cached": False, "latencyMs": 0, "chars": len(original_text)},
        )
        return result

    t0 = time.perf_counter()
    cached_value = await cache.get(text, target)
    if cached_value is not None:
        latency = int((time.perf_counter() - t0) * 1000)
        result = {"translated": cached_value, "cached": True, "latencyMs": latency, "model": MODEL}
        log.info(
            "translate",
            extra={"request_id": request_id, "cached": True, "latencyMs": latency, "chars": len(text)},
        )
        return result

    translated = await translate_text(text, target, model=MODEL)
    await cache.set(text, target, translated, model=MODEL)
    latency = int((time.perf_counter() - t0) * 1000)
    result = {"translated": translated, "cached": False, "latencyMs": latency, "model": MODEL}
    log.info(
        "translate",
        extra={"request_id": request_id, "cached": False, "latencyMs": latency, "chars": len(text)},
    )
    return result


@app.post("/translate")
async def translate(body: TranslateIn, request: Request):
    request_id = request_id_from(request)
    try:
        result = await translate_one(body.text, body.target, request_id=request_id)
    except Exception as exc:
        log.exception(
            "translate_error",
            extra={
                "request_id": request_id,
                "chars": len(body.text),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=502, detail="AI service error") from exc
    return JSONResponse(content=result, headers={"x-request-id": request_id})


@app.post("/translate/batch")
async def translate_batch(body: BatchIn, request: Request):
    request_id = request_id_from(request)
    t0 = time.perf_counter()
    results = []
    try:
        for t in body.texts:
            results.append(await translate_one(t, body.target, request_id=request_id))
    except Exception as exc:
        log.exception(
            "translate_batch_error",
            extra={
                "request_id": request_id,
                "count": len(body.texts),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=502, detail="AI service error") from exc
    latency = int((time.perf_counter() - t0) * 1000)
    hits = sum(1 for r in results if r["cached"])
    log.info("translate_batch", extra={"request_id": request_id, "count": len(results), "hits": hits, "latencyMs": latency})
    # widget expects {results: [{translated, cached}], latencyMs}
    data = {"results": [{"translated": r["translated"], "cached": r["cached"]} for r in results], "latencyMs": latency}
    return JSONResponse(content=data, headers={"x-request-id": request_id})


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL, "cacheSize": await cache.size()}


@app.get("/stats")
async def stats():
    return await cache.stats()
