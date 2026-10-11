# HeatShield demo video — approximately 2 minutes 40 seconds

Record the working [public dashboard](https://staging.d22u8i6a71q15e.amplifyapp.com/), not a local mock. Keep the synthetic disclosure visible. Use readable desktop zoom and a clean browser window. Avoid showing AWS account details, credentials or private dataset files. Rehearse once and check the final video's playback.

| Time | Exact action | Suggested narration |
|---|---|---|
| 0:00–0:20 | Show header, synthetic notice and controls. | “HeatShield — Cooling Where It Counts. How could a municipality compare cooling options when its budget cannot cover every building? We built a transparent simulation and allocation tool to explore that decision.” |
| 0:20–0:40 | Set **Municipal budget (INR)** to `75000` and **Overheating threshold (°C)** to `30`. Keep the notice visible. | “This uses 30 hypothetical buildings and seven days of synthetic weather. Thermal properties and installation costs are provisional, not validated predictions for real households.” |
| 0:40–1:05 | Click **Run allocation**, wait, then show summary and distribution. | “The Python backend compares baseline, cool-roof, insulation and shading options. An exact multiple-choice optimizer selects at most one intervention per building within the budget. These are backend-computed totals.” |
| 1:05–1:35 | Click **Building 01**. Show the chart, threshold, interpretation notice and options table. | “Inspect hourly trajectories and every option's cost and signed benefit. This is a roof-dominated stress scenario: large differences depend on supplied assumptions. Walls, windows, floors and variable ventilation are not represented.” |
| 1:35–1:55 | Expand **Physical inputs, assumptions and provenance**, then close details. | “Avoided overheating is kelvin-hours: temperature exceedance accumulated over time. It is not degrees Celsius of cooling or a health outcome. Negative benefits remain visible and cannot increase the optimization score.” |
| 1:55–2:15 | Change budget to `50000`, show stale-results notice, click **Run allocation**, then show updated results. | “Changing the budget reruns the actual API. Allocations stay budget-feasible with reproducible tie-breaking. Exactness applies to rounded model scores; uncertain physics and costs can change rankings.” |
| 2:15–2:40 | Show the diagram in `docs/ARCHITECTURE.md`, then dashboard or GitHub README. | “React runs on AWS Amplify. API Gateway connects it to Python Lambda, with science separated from cloud transport. HeatShield demonstrates an auditable route from assumptions to allocation. Next are sensitivity analysis and defensible empirical validation before real municipal recommendations.” |

## Rehearsal checks

- At INR 75,000 and 30 °C, the synthetic reference spends INR 74,700, leaves INR 300 and assigns 24 interventions. Score: `19380224213` micro-K·h; displayed avoided overheating: approximately 19,380.22 K·h. These are **model outputs**, not measured impact or validation statistics.
- Do not describe chart peak differences as demonstrated real-world cooling, or claim lives saved, emissions reduced or energy savings.
- Confirm both allocations, chart rendering and video playback. Do not conceal scientific limitations.
- Upload the recording, verify viewing permissions and replace the video placeholder in [the submission draft](HACKATHON_SUBMISSION.md).
