# Phase 4: local API and dashboard

This application uses **synthetic, unvalidated scenarios** only. It does not
predict actual household temperatures, establish intervention effects or estimate
public-health outcomes. No AWS resources, dataset uploads or sensitivity analysis
are included.

## Start locally

From the repository root, in terminal 1:

```powershell
python -B -m heatshield.api.server
```

In terminal 2:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The Python API listens at http://127.0.0.1:8000.
Use Node 22 or 24 supported by the locked test tooling. The development machine's
Node 23.7.0 executed tests/build successfully, but npm reports it outside Vitest's
supported engine range.
Vite proxies `/api` to Python; direct cross-origin browser requests are unnecessary.
Both servers bind only to loopback. Stop each with Ctrl+C.

For a production frontend build and local preview (Python still running):

```powershell
cd frontend
npm run build
npm run preview
```

Open http://127.0.0.1:4173. This preview also proxies `/api`; serving `dist` through
an unrelated static server requires its own API routing configuration. The local
Python HTTP server is a demonstration adapter, not a production web server.

## Architecture and contract

`heatshield.presets` owns the shared author-selected 30-building, 168-hour preset.
The municipal CLI imports the same factory. The scientific engine, optimizer and
research artifacts are unchanged.

`heatshield.api.allocations.allocate_request(dict)` returns `(status, payload)`
without HTTP, cloud or filesystem dependencies. `handle_json(bytes)` adds bounded,
strict JSON parsing. A later Lambda adapter can call these functions.
`heatshield.api.server` supplies the local HTTP transport only.

`POST /api/allocations`, with Content-Type application/json:

```json
{"preset_id":"synthetic_municipal_v1","budget_minor":7500000,"threshold_c":30}
```

Exactly these keys are accepted. Budget is integer paise, 0–100,000,000 inclusive
(INR 0–1,000,000). Threshold is a finite number, 15–45 degrees Celsius inclusive.
These are software bounds, not health standards. Booleans are not numbers.
Maximum body: 4096 bytes. Duplicate JSON keys and nonstandard NaN/Infinity literals
are rejected. Only the allowlisted preset is constructed; arbitrary building
parameters and datasets are not accepted. Server guards limit presets to 50
buildings, 168 hours per building and three nonbaseline options. Optimizer state
limit is fixed at 50,000 distinct candidate costs before pruning.

Success retains the `heatshield.phase3a.v1` shape, with additive `preset_id`,
`units`, `assumptions` and `limitations` fields. Every option has one indoor and
sol-air trajectory; selections reference options, without repeating trajectories.
Unique weather is returned once. Compact transport JSON avoids indentation
overhead. All option trajectories remain available for later comparison needs.
Infinite time constants are null with an explicit flag. Score integers remain
strings; financial totals remain backend integers. Strict serialization rejects
nonfinite output. Responses are not cached.

Errors use `{"error":{"code":"...","message":"...","fields":{}}}`:

| Status | Meaning |
|---|---|
| 400 | Malformed JSON or incomplete/invalid HTTP body framing |
| 404 / 405 | Unknown endpoint / unsupported GET on allocation endpoint |
| 413 / 415 | Oversized body / unsupported content type |
| 422 | Request validation or OPTIMIZATION_STATE_LIMIT |
| 500 | Internal preset/computation failure, without tracebacks |

No failure returns a partial allocation. Concurrent local requests are supported,
but there is no production concurrency/rate limit or hard computation timeout.
Other unsupported HTTP methods use the standard-library server's default response.

## Frontend behavior

React calls the actual API through relative `/api/allocations`. The INR control
uses decimal text and BigInt to convert to paise, then converts the bounded integer
to Number for JSON. No floating-point money multiplication or addition is used.
Budget, spending, remainder, summary benefits and score strings come from the
backend; the UI only formats them. Individual display rounding is not a change to
the optimization precision rule. Building count is derived from selected IDs.

Results are explicitly tied to their submitted controls. Changed controls mark
results stale; a failed subsequent run keeps the previous result labelled as such.
The building dialog uses native modal focus containment and Escape dismissal,
restores focus to its opener, and includes an accessible hourly table alongside the
chart. Temperature arrays are end-of-hour values, plotted at relative hours 1–168.
No fabricated civil dates are assigned. Baseline-only selections are identified.

K.h is accumulated exceedance above a threshold over time, not degrees Celsius of
cooling, a health outcome or measured exposure. Negative option benefits remain
visible. Provisional costs and thermal inputs can change rankings; allocation is
exact only for the supplied rounded scores, with no equity/population model.

## Verification

```powershell
python -B -m unittest discover -s tests -v
python -B -m examples.municipal_demo --budget 75000
cd frontend
npm test
npm run build
```

Backend tests cover bounds, strict types/parsing, resource guards, no partial
results, serialization, authoritative reconciliation and real local HTTP requests.
Frontend tests cover exact money, API request/error handling, loading, summary
totals, stale controls and building details. jsdom dialog methods and chart drawing
are mocked in component tests; these tests do not prove browser layout, native
focus behavior or chart rendering. Browser checks must be reported separately.

With both servers running, `npm run verify:local` from `frontend/` exercises the
actual frontend API client through the Vite proxy and compares with the direct API,
including zero budget and errors. For the built preview, use
`npm run verify:local -- http://127.0.0.1:4173`. No browser clicks are automated.

No authentication, persistent storage, production hosting, AWS deployment or
real-data validation is provided in this phase.

## Observed local verification

On the implementation machine (Python 3.13.1, Node 23.7.0), all 63 Python tests
passed, as did eight frontend tests across three files. The production build
completed successfully. An initial two component-test failures exposed input
labels including helper text; explicit accessible names corrected them. The
initial sandbox blocked esbuild subprocesses; tests/build passed when execution
permissions were available. Locked dependencies audited with zero reported
vulnerabilities after updating Vitest to 4.1.11.

The actual frontend API client passed live checks through both the development
proxy (5173) and built preview proxy (4173), including zero budget, invalid input
and malformed JSON. Proxied and direct allocation payloads matched. Default
results: INR 74,700 spent, INR 300 remaining, 24 interventions, signed avoided
19,380.22421365878 K.h, score string `19380224213`. Compact response: 800,939 bytes.
The unchanged CLI produced the same allocation after preset extraction.

Nonblocking limitations: the main built JS bundle is approximately 619 kB
(186 kB gzip), producing Vite's chunk-size advisory. Node 23 is outside the test
tool's declared engine range, despite successful execution here. No real-browser
automation was available: native focus trapping/Escape behavior, tooltip drawing,
visual layout and responsive breakpoints require manual browser review. Component
and proxy tests do not establish those browser interactions or scientific validity.

## Synthetic stress-scenario interpretation

The municipal preset is a **Roof-dominated synthetic stress scenario**. Large
simulated temperature differences depend on provisional roof, ventilation, solar
and effective-capacitance assumptions. Walls, windows, floors and variable
ventilation are not represented by this reduced-order model. The preset is not
representative housing evidence or an empirically established intervention effect.
This transparency update preserves every numerical input, equation, trajectory,
cost and optimization result; it does not tune temperatures or add model physics.
