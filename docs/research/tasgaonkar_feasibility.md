# Phase 2A: Jalna feasibility decision

**Decision: MODIFY. Not ready for model validation.**

Audit date: 2026-10-09. Source: Figshare article 12546368, version 1, CC0. See [provenance and complete inventory](tasgaonkar_sources.md). Findings below are directly calculated from the downloaded Jalna files unless identified as documentation, hypothesis or unknown. This is a one-site feasibility audit, not calibration, accuracy evaluation or intervention assessment.

## Directly observed structure and coverage

| Item | Observation |
|---|---|
| Indoor CSV | 52,704 rows; 24 columns; 16 temperature logger columns and one RH column |
| Weather CSV | 5,599 rows; 20 columns; 711 entirely blank rows |
| Housing CSV | 17 records; 76 columns; unique Logger ID values |
| File structure | Consistent row widths; CP1252 reading required for weather header byte 0xA0; duplicate header labels require positional handling |
| Indoor numeric cells | 586,090 finite values, 257,174 missing markers, zero invalid nonmissing numeric tokens across 16 temperature columns |
| Indoor per-logger counts | 21,371 to 52,340 finite readings; observed numeric range 12.9 to 47.8 degrees Celsius |
| Outdoor temperature | 4,888 finite values; 711 missing; range 0 to 39.5; 74 zero-temperature rows need investigation |
| Solar radiation | 4,888 finite values; 711 missing; range 0 to 961.5; W/m2 supported by README 3, not encoded in the CSV header |
| Logger-to-housing join | 15 exact ID matches; one temperature column without housing metadata; two housing IDs without a temperature column |
| Housing missingness | 432 of 1,292 cells match the audit's missing-marker rules; includes potentially inapplicable fields, not necessarily recording failures |

Finite numeric values are not necessarily valid measurements. No values were deleted, imputed, smoothed or deduplicated. No claim of spike, flatline or complete sensor-QC assessment is made. The overall missing-cell count is not a matched-hour coverage rate.

## Timestamp evidence: unresolved mixed conventions

README 2 describes day/month/year. Actual indoor files support a different interpretation:

| Diagnostic | Indoor MDY hypothesis | Indoor DMY hypothesis | Weather DMY hypothesis |
|---|---:|---:|---:|
| Parse failures | 0 | 31,968 | 711 (blank rows) |
| Month-label disagreements | 0 / 52,704 | 18,865 / 20,736 comparable rows | 148 / 4,888 |
| Duplicate timestamp rows beyond first | 577 | 289 | 45 |
| Backward steps in file order | 5 | 12 | 26 |

Under indoor MDY, timestamps span 2018-03-01 through 2019-02-28, with 52,127 unique timestamps and four gaps exceeding ten minutes; the largest gap between recorded timestamps is 1,450 minutes. Per-logger missingness creates additional gaps. Fourteen temperature loggers have conflicting finite values at duplicate timestamps under this hypothesis.

Under weather DMY, nonblank timestamps span 2018-03-01 through 2018-09-30; 4,843 unique timestamps remain. Three duplicate timestamps have conflicting outdoor temperatures. All 4,888 nonblank weather rows have nonzero seconds. Exact 60-minute cadence diagnostics are consequently affected by second-level jitter; they must not be interpreted as counts of missing hourly observations.

The mixed hypothesis (indoor MDY, weather DMY) yields 4,819 shared naive hour bins after weather timestamps are floored to the hour. There are 45 duplicate weather bins; the longest sequence of consecutive weather bins is 2,319 hours. These figures ignore interval labeling, timezone uncertainty, contradictory duplicates, zero-temperature flags and logger-specific missingness. They are **potential overlap, not verified aligned usable data**. Same-order alternatives are retained in the local JSON for comparison and are not recommended joins.

The Month column is an internal consistency clue, not independent ground truth. Its 148 weather disagreements prevent treating date-order selection as a complete resolution. The script checks the month component only, not the label's year. Civil timezone, station clock settings, interval start/end labels and the meaning of weather timestamp seconds remain unverified. No UTC conversion or timestamp correction was applied.

## Roof metadata and physical-model suitability

Direct roof-structure labels: 10 `Tin roof`, 6 `Cement`, 1 `Tatch`. There is one disagreement between `Roof` and `Roof structure` after explicitly normalizing Tin/Tin roof and Tatch/Thatch. Geometry labels are 12 single-sloped and 5 flat. Evaporative coolers are marked Yes in three records, No in eleven, and unavailable in three. This is equipment presence, not an operating schedule.

| Input or interpretation | Evidence status |
|---|---|
| Indoor/outdoor temperatures and solar field | Directly observed; clock alignment and measurement quality unresolved |
| Sensor/logger identity | Directly observed; exact joins are incomplete |
| Independent household identity | Not established by Logger ID alone; repeated rooms/deployments require confirmation |
| Roof type, geometry, colour, coatings, shading, room and ventilation categories | Direct fields; completeness and coding require further interpretation |
| Metal-roof archetype mapping | Plausible inference from Tin roof; not a measured assembly specification |
| Uninsulated concrete mapping | Not established by Cement alone; conflicting roof field must be resolved |
| Roof area and slope angle/azimuth | No quantitative fields identified in the inspected housing header |
| Roof U and solar absorptance | Unavailable as quantitative measured inputs; material/colour do not identify them |
| Effective zone C, ventilation W/K and internal gains W | Unavailable as physical model inputs; qualitative categories are not substitutes |
| Exterior coefficient and longwave correction | Unavailable |
| Initial temperature | Could be selected from an eligible observed endpoint after timestamp/QC resolution |

The engine expects roof-plane irradiance; a weather solar field does not establish that geometry. Twelve sloped-roof records make direct substitution particularly uncertain. Roof area and effective parameters would need traceable assumptions/ranges or a separately approved model formulation. The Phase 1 synthetic demonstration defaults must not be presented as measured Jalna parameters.

## Decision gates and scientific risks

- Access/reuse: PASS. Official versioned metadata declares CC0; eight acquired files passed manifest checks.
- Documentation/schema: PARTIAL. Actual schemas inspected; two DOCXs read structurally, legacy DOC inspected partially, installation PDF and consent template not fully reviewed.
- IDs: NOT READY. Fifteen exact logger matches are not proof of fifteen independent households; unmatched records remain.
- Time/quality: NOT READY. Conflicting duplicates, differing date conventions, month-label disagreements, clock semantics and weather zeros require adjudication.
- Proposed sample gate: NOT MET. Seventeen housing records cannot meet the proposed minimum of twenty eligible independent households. Eligibility for a seven-day >=90% matched window and <=2-hour forcing gaps was not established because alignment is unresolved.
- Physical parameters: NOT READY for direct 1R1C evaluation; several required quantities are missing.

MODIFY means retain the dataset as a candidate for a narrower, explicitly uncertain study, not approve Phase 2B. NO-GO would be appropriate for the current one-site validation design if household grouping, timing or defensible physical assumptions cannot be resolved. This audit does not establish that another site solves those problems.

Station weather may differ from roof-level conditions; housing selection is not representative of all households; active cooling and multiroom configurations violate simple free-running assumptions. Parameter non-identifiability and omitted heat-transfer paths remain. Cross-sectional roof differences cannot establish cool-roof causal effects. Sensor checks in the publication do not establish model accuracy.

## Tooling, tests and bounded scope

Added `scripts/audit_tasgaonkar.py`, a read-only CSV auditor with explicit DMY/MDY hypotheses, positional headers, missing-value classification, ID joins, roof conflict counts and local logger-level diagnostics. It deliberately produces no model-ready weather, parameter estimates or validation metrics. Exact-hour flooring is only a diagnostic. Duplicate values are flagged, never averaged. Six-distinct-sample bins are not a general completeness guarantee.

Added ten focused synthetic tests in `tests/test_dataset_audit.py`: numeric classification; ambiguous dates; slash/invalid dates; cadence/duplicates/backward steps; empty input; repeated headers; CP1252-reader configuration/ragged rows; value summaries; named-month consistency; conflicting duplicates. Tests do not yet cover the entire real-data pipeline, timezone conversion, field-year consistency, sensor drift or seven-day eligibility. Tests use no real household records. One first-run test failed because the sandbox denied temporary-directory access; it was changed to an in-memory mocked CSV stream.

Final command: `python -B -m unittest discover -s tests -v`. **22 tests passed** on Python 3.13: 12 unchanged thermal tests plus 10 audit tests. Tests verify implementation behavior, not empirical validity. No packages were installed. Investigation was bounded to one site's three CSVs and five supporting files; no prolonged legacy-document conversion, second-site download or external-weather acquisition was attempted.

## Next decision requiring approval

Resolve documented date/clock discrepancies and household grouping, review duplicate/sentinel provenance, then decide whether to approve a smaller exploratory scope or inspect another site. Author clarification may be needed; no messages were sent to authors. Do not fit physical parameters or evaluate held-out performance until that design is separately approved. Keep all household-level files local and privacy-review any future exports.
