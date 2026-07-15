# Product Evaluation — Live Translate

- **Student:** Oktavianus Ludiro
- **Date:** 2026-07-15
- **Video demo:** https://www.loom.com/share/cad45ddd1261432588899bb0d653ee05
- **LLM provider / model:** OpenAI-compatible provider / `gpt-5.6-luna` (reported by `/health`)
- **Backend target:** `http://localhost:8787`

## Verdict

The local backend passed every automated rubric criterion (**70 / 70 auto points**) and the benchmark SLA gate. It returned fluent Mexican-Spanish product UI strings and preserved the tested prices and product codes. This is not yet a complete shipping evaluation: a real-site Chrome-extension test could not be run in this environment because the browser-control bridge was unavailable, and no public Fly.io gateway was supplied or verified. Those two checks must be completed before submission.

**Rubric score (from `eval/report.json`):** **70 / 70** auto (+ 30 manual)

## 1. Performance & cost (from `benchmark/bench.py`)

| Metric | Result | SLA | Pass? |
|---|---:|---:|---|
| Cache hit p95 | 4.5 ms | <= 60 ms | Yes |
| Cache miss p95 | 0.0 ms | <= 3500 ms | Gate passed; see note |
| Cache hit rate | 100.0% | >= 60% | Yes |
| Throughput | 2095.9 req/s | >= 20 | Yes |
| Error rate | 0.0% | <= 1% | Yes |
| Cost per miss | $0.000000 | — | — |
| Monthly savings from cache | $0.00 | — | — |

The SLA gate exited successfully. The benchmark's reported miss p95 was `0.0 ms`, indicating that the benchmark workload was already warm; it is not evidence of a real cache-miss latency measurement.

## 2. Live-website test

- **Site tested:** Not completed. The prescribed Home Depot/Chrome-extension test could not run because the available browser-control bridge failed during initialization.
- **Translated whole page?** Not observed.
- **Coverage gaps:** Not observed.
- **Cache on re-translate:** Direct gateway batch evidence: first run was 8,037 ms with six misses; the identical second run was 0 ms and all eight results had `cached: true`.
- **Resilience:** CSP, console errors, and layout integrity were not observed in a live page.
- **Screenshots:** None captured.

### Sample translations (direct gateway batch test; not a live-page observation)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| Add to cart | Agregar al carrito | N/A | Yes |
| Free delivery on orders over $45 | Envío gratis en pedidos de más de $45 | `$45` preserved | Yes |
| Model ABC-123 is in stock | El modelo ABC-123 está disponible en inventario | `ABC-123` preserved | Yes |
| Save 20% on select appliances | Ahorra 20% en electrodomésticos seleccionados | `20%` preserved | Yes |
| Choose a store for pickup | Elige una tienda para recoger tu pedido | N/A | Yes |
| Was $199.99, now $149.99 | Antes $199.99, ahora $149.99 | Both prices preserved | Yes |
| SKU 1001234567 | SKU 1001234567 | SKU preserved | Yes |
| Good morning, welcome! | ¡Buenos días, bienvenido! | N/A | Yes |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | Pass | Eight direct gateway samples were fluent and semantically correct. |
| Mexican-Spanish register (es-MX) | Pass | Samples use natural LatAm/Mexican-neutral wording such as “carrito”, “Envío gratis”, and “Elige”. |
| Numbers / prices / codes preserved | Pass | `$45`, `$199.99`, `$149.99`, `ABC-123`, and SKU `1001234567` were unchanged. |
| Page coverage | Partial | Not measured on a real page. |
| Cache effectiveness | Pass | Direct repeat batch: 8,037 ms with misses, then 0 ms with all results cached; automated cache test also passed. |
| Latency vs SLA | Partial | SLA gate passed, but its miss p95 was 0.0 ms because the benchmark was already warm. |
| Error handling (no silent English) | Partial | Automated contract/error checks passed; an upstream-provider failure was not induced in this run. |
| Resilience on a real site | Partial | Not tested: browser-control bridge was unavailable. |
| UX polish | Partial | Not observed through the extension on a real page. |

## 4. Top fixes before shipping

1. Run the extension on `https://www.homedepot.com` (or another site the student does not control), capture before/after screenshots, and record coverage, CSP behavior, and cache badges.
2. Deploy both services to Fly.io and add the public gateway URL plus a successful `/health` check to this report.
3. Clear the cache before one benchmark run so cache-miss latency is measured rather than reported as `0.0 ms` from a warm workload.
