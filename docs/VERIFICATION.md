# Submission verification — October 11, 2026

These checks concern software and deployment behavior, not empirical model validation. No AWS resources were created, changed or deleted during this review. The thermal engine, optimizer, synthetic inputs and Phase 2 research artifacts are unchanged.

| Check | Actual result |
|---|---|
| Python suite | 72 tests passed on Python 3.13.1 |
| Frontend suite | 16 tests across five files passed on Node 24.21.0 |
| Production build | `npm run build:deploy` passed with the existing API origin; asset verification passed |
| Build advisory | Main JS approximately 623 kB, 187 kB gzip; existing Vite chunk-size advisory, no build failure |
| Artifact packaging | Frontend ZIP path/byte checks passed; Lambda ZIP contains ten allowlisted modules |
| Local request flow | `npm run verify:local` passed through Vite port 5173 to Python port 8000; direct/proxied results reconciled, including zero budget and invalid requests |
| Public assets | Amplify HTML, referenced JS and CSS returned HTTP 200; correct content types, no HTML masquerading as an asset |
| Public API | Actual allocation returned HTTP 200 and the expected schema, totals and score; allowed-origin header matched the Amplify origin |
| Public browser | Isolated headless Chrome rendered the actual dashboard, ran both demo budgets and opened Building 01's real chart with its scientific disclosure; no runtime exceptions recorded in the successful rehearsal |
| Responsive inspection | Captures inspected at 1440 × 1000 and 390 × 844; no document-wide horizontal overflow at mobile width |
| Git safety | Pattern scan of 64 nonignored project files and 74 historical blobs found no credential patterns; ignored paths include local datasets, outputs, `.env`, `.aws`, virtual environments and build output |
| Documentation | Relative Markdown links resolved; commands matched repository entry points and were exercised where relevant |

At INR 75,000 and 30 °C, the public response reported 30 selections, 24 nonbaseline interventions, INR 74,700 spent, INR 300 remaining and score string `19380224213`. At INR 50,000, the browser displayed INR 49,900 spent, INR 100 remaining and 17 interventions. These are synthetic model outputs, not impact measurements or deployment-performance benchmarks.

The first scripted browser attempt timed out while changing the second budget through programmatic input events. Repeating with normal keyboard input and spaced requests completed both allocations. No application change was made for that automation failure. A Vite server already occupied port 5173; the integration check used that existing server without terminating it.

Screenshots and generated ZIPs remain in ignored `outputs/`, outside Git. Component tests mock charts and native dialog methods. The browser rehearsal is a focused smoke check, not a complete accessibility audit, mobile-device test or coverage of every tooltip/keyboard interaction. Secret scans are pattern-based and cannot guarantee that every form of sensitive information is detectable.

No authenticated AWS configuration audit was available: runtime, IAM, throttling, concurrency and log settings remain outside this verification. The owner reports the working Lambda/API Gateway deployment; public responses verify observable behavior. GitHub-connected Amplify builds are prepared but not independently established as enabled.

Before submission, record and review the final video, confirm judge access to GitHub and the video, replace the [submission placeholder](HACKATHON_SUBMISSION.md), and complete the official form.
