# Deployment and packaging

The working application uses Amplify Hosting, API Gateway and Lambda. See [architecture](ARCHITECTURE.md) for responsibilities and [verification](VERIFICATION.md) for observed public behavior. These instructions prepare artifacts; they do not provision or update AWS resources. Inspect existing cloud settings before any separately approved deployment.

## Lambda artifact

From the repository root:

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/package_lambda.py
```

`outputs/heatshield-lambda.zip` contains ten allowlisted application modules with `heatshield/` at its root. The standard-library runtime needs no dependency layer, AWS SDK or dataset. Packaging is deterministic for identical source bytes; tests import and invoke the ZIP in isolation.

Handler: `heatshield.api.lambda_handler.handler`. Integration requires API Gateway **HTTP API payload v2**, route `POST /api/allocations`. REST API v1 is unsupported. The adapter checks path, method, JSON media type and decoded body size, then delegates to the same service as local HTTP. Errors contain no partial allocation. API Gateway owns preflight and CORS.

Private AWS configuration, including runtime, IAM, concurrency and throttling, was not independently audited during documentation preparation. The API is unauthenticated; CORS is not access control. Request/state bounds limit individual computations, not total cloud spending.

## Frontend artifact

From the repository root, after installing dependencies with `npm ci` in `frontend/`:

```powershell
cd frontend
npm test
$env:VITE_API_BASE_URL = 'https://hdt6pym543.execute-api.ap-southeast-2.amazonaws.com'
npm run build:deploy
cd ..
python -B scripts/package_frontend.py
```

The API origin is public build-time configuration, not a credential. It must be HTTPS without a path, credentials, query or fragment. Deployment builds reject missing or placeholder origins. Changing this setting requires rebuilding. Omit it for local Vite proxy use; `.env.example` is only a template.

The verified ZIP is `outputs/heatshield-frontend.zip`. It contains `index.html` at its root and preserves `assets/`. Use the Python packager, which checks paths and exact file bytes; do not recreate this ZIP with Windows `Compress-Archive`.

The existing public app is `d22u8i6a71q15e`, branch `staging`. A manual ZIP upload does not execute `amplify.yml`. Preserve its hostname and the working API's CORS origin. No new upload is needed for documentation-only changes.

## Optional GitHub builds

Root `amplify.yml` prepares monorepo builds with:

- App root `frontend`; branch setting `AMPLIFY_MONOREPO_APP_ROOT=frontend`.
- Node 24, `npm ci`, frontend tests and `npm run build:deploy`.
- Artifact directory `dist` relative to `frontend`, including `**/*` without flattening.
- `VITE_API_BASE_URL` set to the existing API origin above.

This configuration does not prove a GitHub-connected pipeline is enabled. Repository connection or a different hosting origin needs separate approval and inspection; a different origin may require a CORS change. The frontend configuration does not deploy the Python backend.

## Public verification and asset incident

```powershell
cd frontend
npm run verify:public -- https://staging.d22u8i6a71q15e.amplifyapp.com/
```

The check requires HTTP 200, correct content types and non-HTML JS/CSS bodies. Follow it with a real browser allocation and chart check. Build success alone does not prove the site works.

The earlier blank-screen incident had a verified ZIP-header mismatch: central directory paths used `assets/file.js`, while local headers used `assets\file.js`. Amplify served encoded-backslash URLs but returned 404 for the correct slash paths. The Python packager checks both headers, and a regression test reproduces the defect. Public slash-path assets subsequently passed verification. Vite's root-relative asset base was correct; rewriting missing JavaScript to `index.html` would conceal the problem.

The dashboard has no client-side routes and does not require a broad SPA catch-all. Never rewrite asset requests to HTML.

For a separately approved release, retain the previous verified frontend artifact and Lambda version for rollback. Inspect existing version/alias use before changing routing. Resource cleanup also requires separate approval; preserve unrelated infrastructure.

References: [AWS monorepo configuration](https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html), [manual deployments](https://docs.aws.amazon.com/amplify/latest/userguide/manual-deploys.html), [rewrite examples](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html).
