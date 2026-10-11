# Phase 5 local deployment preparation

> Historical preparation record. The public deployment is now working, as reported
> by the project owner; October 11 submission checks confirm public frontend assets.
> See [current architecture](ARCHITECTURE.md). Settings below are preparation
> recommendations, not an authenticated audit of the deployed AWS configuration.

No AWS resources are created by these files. Cloud deployment requires separate
approval, authenticated access and inspection of existing resources.

## Prepared code and artifacts

`heatshield.api.lambda_handler.handler` accepts API Gateway HTTP API **payload
version 2.0** events. It checks the exact POST path `/api/allocations`, JSON media
type and plain/base64 bodies, then calls the unchanged allocation service. The
4096-byte limit applies to decoded UTF-8 bytes. Responses use strict compact JSON,
no-store caching and the existing versioned schema. Errors never contain partial
allocations. API Gateway owns CORS and preflight; the handler adds no CORS headers.
REST API payload v1 and arbitrary direct invocation formats are not supported.

Run from the repository root:

```powershell
python -B -m unittest discover -s tests
python -B scripts/package_lambda.py
```

The generated `outputs/heatshield-lambda.zip` contains exactly ten allowlisted
application modules, with `heatshield/` at the archive root. No Python dependencies,
AWS SDK, datasets, credentials, research artifacts or local server are packaged.
Packaging is deterministic for identical source bytes. A test imports and invokes
the ZIP from an isolated Python process.

## Frontend build

`VITE_API_BASE_URL` is a public HTTPS origin, not a secret. Use an API Gateway
default stage so that no stage path is needed. A trailing slash is accepted;
paths, credentials, queries, fragments and HTTP origins are rejected. Omit the
setting for the existing local Vite proxy. It is compiled into the build; changing
it requires rebuilding. `.env.example` is a template, not an active configuration.

```powershell
cd frontend
npm ci
npm test
$env:VITE_API_BASE_URL = 'https://REPLACE_API_ID.execute-api.ap-southeast-2.amazonaws.com'
npm run build
# Restore the local proxy setting for later builds:
Remove-Item Env:VITE_API_BASE_URL
```

After substituting a verified API origin, package the *contents* of `dist`, with
index.html at the ZIP root:

```powershell
cd ..
python -B scripts/package_frontend.py
```

Never publish the placeholder-origin verification build. A standalone static host
does not provide Vite's local proxy; it needs this configured HTTPS API origin.

Use the Python packager above instead of Compress-Archive: the latter produced
backslashes in ZIP local headers despite a forward-slash directory listing. See
[the verified Amplify diagnosis and repair](amplify_frontend.md).

## Required AWS configuration (not provisioned)

| Resource | Configuration |
|---|---|
| Lambda | Inspect/reuse `heatshield-api` only if dedicated; region ap-southeast-2; Python 3.13; x86_64; ZIP; handler `heatshield.api.lambda_handler.handler`; 512 MB; 10 s timeout; no VPC/layers/environment secrets required |
| Execution role | Lambda service trust; permissions for its CloudWatch log group only; no dataset, database or S3 permissions |
| Version/alias | Publish a version; dedicated `demo` alias points to the verified version; retain previous version for rollback |
| Concurrency | Reserved concurrency 2 if account quota permits; no provisioned concurrency |
| HTTP API | API Gateway HTTP API in ap-southeast-2; Lambda proxy integration targeting the demo alias; payload 2.0; route POST /api/allocations; default stage with auto deployment |
| Invocation policy | Allow apigateway.amazonaws.com to invoke the alias, scoped to this API's POST /api/allocations source ARN |
| CORS | Exact Amplify HTTPS origin; POST; Content-Type; no credentials or wildcard; managed by API Gateway |
| Throttling | Target rate 1 request/s and burst 2 at stage/route; best-effort, not a spending cap |
| Static hosting | Amplify Hosting WEB app and `demo` branch; manual dist ZIP deployment; AWS-provided HTTPS domain; no SSR or cloud builds required |
| Logs | CloudWatch Lambda log group with short retention, e.g. 3 days; no full request/result logging |

Disable any public Function URL bypass only after inspecting existing usage and
obtaining deployment approval. CORS is not authentication. The public demo has no
user authentication; bounded requests, throttling and concurrency reduce resource
exposure but do not guarantee a cost ceiling. Unknown account quotas and IAM
permissions must be checked before deployment.

## Deployment sequence after approval

1. Authenticate through the normal AWS browser/SSO flow. Verify caller identity,
   function configuration, policy, concurrency, versions/aliases and integrations.
   Do not overwrite an unrelated function or existing working routing.
2. Create/identify the Amplify app and branch to obtain its origin.
3. Upload the Lambda ZIP; wait for a successful update, publish a version and
   update the dedicated alias. Configure the HTTP API, narrow invocation permission,
   CORS and throttling. Verify the endpoint before publishing the frontend.
4. Build with the verified API origin, ZIP dist contents, create an Amplify manual
   deployment, PUT the ZIP to the returned temporary upload URL and start deployment.
   Keep temporary upload URLs out of source control and chat.
5. Test the public origin, preflight, actual allocation, zero budget, invalid inputs,
   413/415 handling, charts, mobile layout and authoritative totals. Gateway-level
   errors may use AWS's own envelope. Check logs for unexpected failures.

Representative commands; placeholders require inspected resource values:

```powershell
aws lambda update-function-code --function-name heatshield-api --zip-file fileb://outputs/heatshield-lambda.zip --publish --region ap-southeast-2
aws lambda wait function-updated --function-name heatshield-api --region ap-southeast-2
aws apigatewayv2 create-api --name heatshield-http --protocol-type HTTP --region ap-southeast-2
aws amplify create-app --name heatshield-dashboard --platform WEB --region ap-southeast-2
aws amplify create-branch --app-id APP_ID --branch-name demo --region ap-southeast-2
aws amplify create-deployment --app-id APP_ID --branch-name demo --region ap-southeast-2
aws amplify start-deployment --app-id APP_ID --branch-name demo --job-id JOB_ID --region ap-southeast-2
```

These are not a complete provisioning script: configure the Lambda handler/runtime,
role, alias, API integration/route/stage, permission, CORS and upload before exposing
the app. Needed deployer permissions include scoped Lambda, API Gateway, Amplify,
CloudWatch Logs and iam:PassRole; IAM role creation is needed only if no suitable
role exists. Use a browser console fallback if CLI access is unavailable. No local
preparation command above establishes that cloud deployment or permissions work.

Rollback moves the alias to the previous verified version and redeploys the saved
frontend ZIP. Cleanup deletes only newly created project resources after approval;
preserve pre-existing infrastructure. No deployment, cleanup or AWS writes happen
as part of this preparation.

Scientific assumptions, default allocations and the roof-dominated synthetic stress
scenario remain unchanged. Local tests verify adapters and packaging, not empirical
accuracy, AWS latency, cloud CORS or public endpoint availability.

## Local verification record

Preparation passed 69 Python tests and 12 frontend tests. The normal production
build succeeded. A separate ignored build using `https://phase5-verification.invalid`
confirmed the configured origin is compiled into the bundle; it is not a deployment
artifact. The normal local-proxy build was preserved. Vite's existing large-chunk
advisory remains. The initial ZIP test hit sandbox filesystem restrictions; the
complete Python suite passed with the necessary execution permissions, including
the isolated ZIP import/invocation and byte-for-byte packaging determinism check.

The generated Lambda ZIP contains ten modules and is 14,615 bytes. No credentials
or cloud resources were created, changed or deleted. Existing UI polish remains
uncommitted alongside this preparation. Public AWS behavior is not verified yet.
