# Assignment 1 Live Translate Plan

## Target Result

Build and verify the backend for FDE Assignment 1 so the provided browser widget can translate English web pages into Mexican Spanish through the Node gateway and Python AI service. The frontend, loader, extension, demo pages, benchmark, and evaluator remain unmodified.

The assignment expects two services: the browser talks only to the Node gateway on `:8787`, and the gateway talks to the Python AI service on `:8000` ([README.md:32](README.md:32), [README.md:87](README.md:87)). The backend must satisfy the exact API response shapes for `/translate`, `/translate/batch`, `/health`, and `/stats` ([README.md:92](README.md:92)).

## Scope

Files to build:

- [backend/ai-service-python/lib/llm.py](backend/ai-service-python/lib/llm.py:25): implement the real LLM translation call.
- [backend/ai-service-python/lib/cache.py](backend/ai-service-python/lib/cache.py:29): implement SQLite init/get/set around the existing memory tier and stats.
- [backend/ai-service-python/app.py](backend/ai-service-python/app.py:54): implement cache -> LLM -> cache flow, validation/error behavior, and request-id logging.
- [backend/gateway-node/server.js](backend/gateway-node/server.js:32): implement request logging, request-id creation/forwarding, and AI-service proxying.
- Deployment/config files only if needed for Fly.io, such as service-local `fly.toml` or Docker-related files.

Files not to edit:

- `widget/`, `loader/`, `extension/`, `demo-pages/`, `benchmark/`.
- The README states the frontend is provided and the backend must conform to it ([README.md:71](README.md:71), [README.md:82](README.md:82)).

## Success Criteria

- `POST /translate` returns `{ "translated": string, "cached": boolean, "latencyMs": number, "model": string }` through both the AI service and the gateway ([README.md:92](README.md:92)).
- `POST /translate/batch` returns `{ "results": [{ "translated": string, "cached": boolean }], "latencyMs": number }` ([README.md:100](README.md:100)).
- `GET /health` returns status `ok`; `GET /stats` returns cache stats including hit rate ([README.md:108](README.md:108), [README.md:113](README.md:113)).
- Invalid client input returns `400`; unimplemented code paths are removed; upstream AI failures return `502` from the gateway ([README.md:118](README.md:118)).
- LLM output is Mexican Spanish (`es-MX`), translation only, with numbers, prices, and product/model codes preserved ([backend/ai-service-python/lib/llm.py:10](backend/ai-service-python/lib/llm.py:10)).
- LLM failures fail loud. Do not return the original English text as a fallback ([backend/ai-service-python/lib/llm.py:15](backend/ai-service-python/lib/llm.py:15)).
- Identical `(text, target)` never calls the LLM twice; `cached: true` is used only for cache hits; SQLite cache survives AI-service restart ([README.md:118](README.md:118), [backend/ai-service-python/lib/cache.py:4](backend/ai-service-python/lib/cache.py:4)).
- Gateway emits one structured log line per request; AI service emits one structured log line per translation using `lib/logger.py` ([backend/gateway-node/server.js:32](backend/gateway-node/server.js:32), [backend/ai-service-python/lib/logger.py:1](backend/ai-service-python/lib/logger.py:1)).
- Gateway derives or reuses `X-Request-Id`, logs it, forwards it as `x-request-id`, and AI logs the same ID for end-to-end grep.
- `python benchmark/bench.py` exits `0`; SLA targets are cache-hit p95 <= 60 ms, cache-miss p95 <= 3500 ms, hit rate >= 60%, error rate <= 1%, throughput >= 20 req/s ([benchmark/sla.json:5](benchmark/sla.json:5)).
- Hygiene check shows no `.env`, `node_modules`, `.venv`, `.db`, or `.log` committed.
- Both services are deployed to Fly.io, and the public gateway `/health` responds ([README.md:185](README.md:185)).
- Product Evaluation is generated from actual runs. The eval README says the final submission artifact is `PRODUCT_EVAL.md`, with `REPORT.md` and `report.json` as intermediate outputs ([eval/README.md:6](eval/README.md:6), [eval/README.md:20](eval/README.md:20)).

## Implementation Plan

### 1. Baseline and Setup

- Read current git status and confirm no unrelated working-tree changes.
- Install dependencies only as needed:
  - Python service uses FastAPI, uvicorn, python-dotenv, aiosqlite, and the OpenAI Python SDK for the selected provider path ([backend/ai-service-python/requirements.txt:1](backend/ai-service-python/requirements.txt:1)).
  - Gateway uses Node 18+, Express, CORS, and dotenv ([backend/gateway-node/package.json:6](backend/gateway-node/package.json:6)).
- Copy `.env.example` files to local `.env` only if missing; never commit them.
- Confirm required credentials:
  - OpenAI API key from local environment or `.env` as `OPENAI_API_KEY`; never commit it ([backend/ai-service-python/.env.example:1](backend/ai-service-python/.env.example:1)).
  - Fly.io auth and app names for deployment.

### 2. Python SQLite Cache

- Implement `TwoTierCache.init()` in [backend/ai-service-python/lib/cache.py](backend/ai-service-python/lib/cache.py:29):
  - Create the `translations` table with `key`, `source`, `target`, `translated`, `model`, `access_count`, and `created_at`.
  - Ensure `key` is primary and indexed.
- Implement `TwoTierCache.get()`:
  - Increment `requests`.
  - Check memory first.
  - On SQLite hit, warm memory, increment `db_hits`, bump `access_count`, and return translation.
  - On miss, increment `misses` and return `None`.
- Implement `TwoTierCache.set()`:
  - Write to memory and SQLite with upsert by SHA-256 key.
  - Preserve the existing `_key(text, target)` format unless tests/eval prove it incompatible ([backend/ai-service-python/lib/cache.py:19](backend/ai-service-python/lib/cache.py:19)).

### 3. Python LLM Adapter

- Implement `translate_text()` in [backend/ai-service-python/lib/llm.py](backend/ai-service-python/lib/llm.py:25).
- Use the OpenAI Python SDK; uncomment/add the `openai` dependency in `requirements.txt` if it is not already active.
- Read credentials from environment only; no hard-coded keys.
- Prompt requirements:
  - Translate English to natural Mexican Spanish (`es-MX`).
  - Return only the translated string.
  - Preserve numbers, `$` prices, SKUs, model names, and product codes verbatim.
- Strip whitespace/wrapping quotes from the model response.
- Let provider errors propagate so the API can surface failure instead of silently returning English.

### 4. Python API Flow, Errors, and Trace Logging

- Implement `translate_one()` in [backend/ai-service-python/app.py](backend/ai-service-python/app.py:54):
  - Normalize empty text to the existing empty response.
  - Measure `latencyMs` with `time.perf_counter()` on both hit and miss paths.
  - Cache-hit path returns `{ translated, cached: true, latencyMs, model }` without calling the LLM.
  - Cache-miss path calls `translate_text()`, stores the result, and returns `{ translated, cached: false, latencyMs, model }`.
- Add explicit HTTP error handling:
  - Invalid body/target/text -> `400` where Pydantic does not already cover it.
  - Provider/cache failures -> service should not pretend success. The gateway will convert upstream failures to `502`; if needed, AI service can return `502` directly for direct benchmark/eval clarity.
- Add request-id support:
  - Accept `x-request-id` from headers.
  - Include it in each `translate` and `translate_batch` log line alongside `cached`, `latencyMs`, and `chars` ([backend/ai-service-python/app.py:86](backend/ai-service-python/app.py:86)).

### 5. Node Gateway Logging and Proxy

- Implement logging middleware in [backend/gateway-node/server.js](backend/gateway-node/server.js:32):
  - Derive request ID from inbound `X-Request-Id`, or generate one.
  - Attach it to the request and response header.
  - Log JSON or structured key/value after `finish` with method, url, status, duration ms, and request ID.
- Implement `callAiService()` in [backend/gateway-node/server.js](backend/gateway-node/server.js:61):
  - POST JSON to `${AI_SERVICE_URL}${path}`.
  - Forward `x-request-id`.
  - Parse JSON response.
  - Throw on non-2xx and include status/body context without leaking secrets.
- Keep existing validation on `/translate` and `/translate/batch`, and make sure failed upstream calls return `502`.
- Consider forwarding request ID for `/health` and `/stats` too for consistent observability.

### 6. Local Verification

Run these checks with both services up:

```bash
curl -sf localhost:8000/health
curl -sf localhost:8787/health
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'
curl -s localhost:8787/stats
```

Expected proof:

- First translation is `cached: false`.
- Second identical translation is `cached: true` with much lower `latencyMs`.
- `/stats` shows request count, hits, misses, and hit rate.
- Logs contain the same request ID in gateway and AI-service output.

Then verify persistence:

- Stop and restart only the Python AI service.
- Repeat the same `Good morning` request through the gateway.
- Confirm it is still `cached: true`, proving SQLite survived process restart.

### 7. SLA and Regression Gates

- Run direct AI-service benchmark:

```bash
python benchmark/bench.py --direct
```

- Run end-to-end gateway benchmark:

```bash
python benchmark/bench.py
```

- Fix backend until both relevant gates pass, especially the default end-to-end gate. The benchmark checks health, cold misses, warm hits, latency, throughput, hit rate, and error rate ([benchmark/bench.py:122](benchmark/bench.py:122), [benchmark/bench.py:184](benchmark/bench.py:184)).
- Run hygiene checks:

```bash
git status --porcelain | grep -E '\.env$|node_modules|\.venv|\.db$|\.log$' && echo "FAIL" || echo "clean"
git diff --stat -- widget extension loader demo-pages benchmark
```

Expected proof:

- Hygiene prints `clean`.
- Protected path diff is empty.

### 8. Widget Smoke Test

- Use the extension path for real sites because the README says strict-CSP sites block console injection and the extension is required for real-site testing ([README.md:165](README.md:165)).
- Configure the extension popup backend URL to the local gateway for local smoke testing.
- On a real page, click `Translate page`, then restore and translate again.
- Confirm visible translations, cache-hit badges on repeat, and no frontend modifications.

### 9. Fly.io Deployment

- Deploy one Fly app for the AI service and one for the gateway as required ([README.md:185](README.md:185)).
- Set secrets rather than baking credentials into code:

```bash
cd backend/ai-service-python
fly launch --no-deploy
fly secrets set OPENAI_API_KEY=...
fly deploy

cd ../gateway-node
fly launch --no-deploy
fly secrets set AI_SERVICE_URL=https://<ai-app>.fly.dev
fly deploy
```

- Prefer private Fly networking for AI service if practical, but the required public proof is that the gateway answers:

```bash
curl -sf https://<gateway-app>.fly.dev/health
```

- Point the extension popup at the deployed gateway and repeat the live-site widget test.

### 10. Product Evaluation and Submission Evidence

- Run the bundled `/fde-live-translate-eval` workflow if available in the active environment, because the eval README says it runs the rubric, benchmark, live-website test, and writes `PRODUCT_EVAL.md` ([eval/README.md:6](eval/README.md:6)).
- If that workflow is unavailable in this Codex surface, run the underlying commands directly and document the gap:

```bash
python eval/eval.py --student "Oktavianus Ludiro" --video "<video-url>"
python benchmark/bench.py --json benchmark-results.json
```

- Final submitted evidence should include:
  - `PRODUCT_EVAL.md` generated from actual runs.
  - A 60-90 second screen recording: fresh page, widget translating live, whole-page translate, cache hit shown on repeat ([eval/README.md:39](eval/README.md:39)).

## Risks and Mitigations

- Missing or invalid LLM key: local API calls will fail. Mitigation: fail loud, verify `.env` locally, and set Fly secrets before deploy.
- LLM latency exceeds cache-miss SLA: mitigation is not to fake translations; use concise prompts, batch only where contract already allows it, and rely on cache for repeated workload.
- SQLite write contention under benchmark concurrency: use short-lived aiosqlite connections, commits, and simple upserts; re-run benchmark after any cache change.
- Trace correlation missing from one service: make one request with a known `X-Request-Id` and grep both logs before claiming completion.
- Accidental frontend/benchmark edits: run protected-path diff before final report.
- Fly deployment config drift: keep local env and Fly secrets aligned (`MODEL`, provider key, `AI_SERVICE_URL`, `TRANSLATION_DB_PATH`).

## Stop Condition

Implementation is ready to call complete only after:

- Local AI and gateway health checks pass.
- Contract curl checks pass through the gateway.
- Cache hit and SQLite persistence are proven.
- Trace ID appears in both gateway and AI logs for one request.
- `python benchmark/bench.py` exits `0`.
- Hygiene/protected-path checks are clean.
- Deployed Fly gateway `/health` passes.
- Live-site widget test succeeds against the deployed gateway.
- `PRODUCT_EVAL.md` is generated from actual eval/benchmark/live-site evidence.
