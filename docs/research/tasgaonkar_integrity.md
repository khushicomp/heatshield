# Phase 2B: Jalna data integrity investigation

**Overall: PARTIALLY RESOLVED. Keep the Phase 2A MODIFY decision.**

Date: 2026-10-09. Scope: original version-1 Jalna CSVs and already-downloaded documentation only. No corrected dataset, parameter calibration, model validation or additional dataset acquisition. See [source inventory](tasgaonkar_sources.md) and [Phase 2A report](tasgaonkar_feasibility.md).

## Evidence and resolution

| Issue | Status | Evidence and remaining limit |
|---|---|---|
| Indoor calendar syntax | RESOLVED for file interpretation | MDY parses all 52,704 rows and agrees with all 52,704 Month/year labels. DMY fails on 31,968 rows and disagrees on 18,865 of 20,736 comparable labels. README 2's DMY description conflicts with the actual file. This establishes a reproducible interpretation, not an independent guarantee of historical clock correctness. |
| Weather calendar syntax | RESOLVED for file interpretation | Leading `DD/MM/YYYY` parsed DMY and trailing `Date` parsed MDY agree on all 4,888 nonblank rows. The reverse pairing agrees only on the 1,918 rows where both parse; it cannot explain the remaining rows. Redundant fields may share a source, so this is consistency evidence, not independent timestamp verification. |
| 148 Month-label disagreements | PARTIALLY RESOLVED | One April-boundary row retains March-18; one contiguous 147-row September block retains Aug-18. No year disagreements among 4,888 comparable weather rows. Cause and authoritative correction remain unverified. |
| Sampling cadence | PARTIALLY RESOLVED | README 2 specifies ten-minute indoor sampling; README 3 describes minute measurements aggregated hourly. Duplicate/backward records and weather second-level jitter remain. |
| Duplicate classification | RESOLVED for the stated payloads; adjudication BLOCKED | Counts below distinguish numeric payload equality from exact raw-row equality. No records were merged or removed. |
| Logger-to-housing joins | PARTIALLY RESOLVED | 15 exact matches, one temperature-only ID, two housing-only IDs. No documented alternative crosswalk found in accessible material. |
| Independent household grouping | BLOCKED | Logger IDs identify sensors, not proven unique households/deployments. No accessible grouping or replacement history establishes independence. |
| Timezone and hourly interval boundaries | BLOCKED | No study-specific clock configuration or start/end convention established. Location alone does not establish logger timezone. |

## Month-label investigation

The disputed fields are the leading observation date and separate `Month` label, not two disagreeing observation dates. Leading DMY and trailing MDY dates agree even on disputed rows.

| Original CSV rows, header counted as row 1 | Parsed observation dates | Raw Month label | Rows |
|---|---|---|---:|
| 745 | 2018-04-01, 00:00:18 | March-18 | 1 |
| 4166-4312 | 2018-09-01 through 2018-09-06 | Aug-18 | 147 |

The April record is preceded by 31 March at 23:00:14 and followed by 1 April at 01:00:14 labelled April. A previous-hour reporting label or stale label could explain this boundary case, but neither is confirmed.

The September block follows 31 August at 23:00:15. All 147 rows retain August despite both date fields indicating September. The next row is dated 7 September at 01:00:18 and labelled September. The block also contains a backward midnight entry at its end; file adjacency must not be mistaken for clean chronological continuity.

A fixed civil timezone conversion alone cannot explain labels lagging across six days. A copied/section label or assembly issue is plausible, but original logs or author clarification would be needed to establish the cause. Dates and labels are preserved; no field was silently selected for correction.

`ReceiveDate` parsed MDY equals the observation date on 3,972 rows and is later on 916 rows, by 1-17 days. This is evidence that reception and observation date fields are not interchangeable; it does not prove the transmission-delay mechanism. The second `Time` column has a `DD:DD.D` textual shape on all 4,888 nonblank rows, unlike the leading full AM/PM clock. Its complete clock meaning cannot be reconstructed from that display alone. `Hours` also does not have a single consistent offset from the leading hour and is not used to repair it.

## Duplicate evidence

Duplicate groups use indoor MDY and weather leading DMY. Classification compares finite numeric values and missing markers; it does not compare temperatures against a model.

| Timestamp groups | Identical measurement payload | Conflicting measurement payload | Complementary missingness | Excess rows |
|---|---:|---:|---:|---:|
| Indoor, 16 temperature columns | 144 | 433 | 0 | 577 |
| Weather, temperature/solar/humidity/pressure | 42 | 3 | 0 | 45 |

No duplicate group has all raw fields identical. Equal measurements can coexist with different metadata; therefore these are not automatically disposable exact-record copies. RH is excluded from indoor payload classification, and other weather variables are excluded from weather payload classification. Equality for the selected payload does not establish equality for every sensor field.

Existing gaps, conflicting values and 74 outdoor zero-temperature rows remain quality concerns. No averaging, preference for first/last row, time shifting or automatic removal was applied. Identical payloads and conflicts are classified, not scientifically adjudicated.

## Deterministic mapping

All 17 housing IDs are eight-digit strings and unique. The matching rule is exact string equality after stripping only boundary whitespace. Leading zeros are retained. A documented RH suffix identifies a separate channel of the same logger; it does not identify another household. Neither housing-only ID is rescued by an exact RH-base match.

The local output retains original headers, channel positions, exact matched IDs and unmatched IDs. Normalization collisions and repeated temperature-channel IDs raise errors. No padding, digit correction, row-position join, fuzzy similarity or temperature-pattern matching is permitted. Fifteen exact logger matches do not prove fifteen independent households. Unmatched records remain unmatched pending explicit original deployment/crosswalk evidence.

## Documentation checkpoint and stopping decision

The investigation stopped open-ended documentation troubleshooting before the 45-minute checkpoint; there was no need to consume the remaining 90-minute allowance.

- README 2 and README 3 DOCXs were reinspected as structured XML tables. They establish nominal sampling and generic field meanings, but no explicit timezone, household grouping or replacement history was found. README 3's generic fields do not define the extra Jalna reception columns or archive interval labels.
- README 1 legacy DOC had best-effort text available from Phase 2A; it describes logger serials and housing variables, not an established household deployment crosswalk. Complete table-aware inspection remains unavailable.
- Installed Word was detected, and one hidden, macro-disabled, read-only COM extraction attempt was made for the legacy DOC/PDF files. Word activation failed with 'Server execution failed' before opening any document. No converted files were produced and no reader was installed.
- The consent DOC and Davis PDF therefore remain incompletely inspected. Even a generic manual's timezone options would not prove the settings used in this study. Missing evidence remains BLOCKED, rather than assumed absent from every uninspected page.

Original file sizes and manifest MD5s were verified before and after the investigation. All eight acquired dataset/documentation files still match version 1. Phase 1 source and tests are unchanged. The metadata cache and all detailed outputs remain local and ignored.

## Implementation and verification

Extended only `scripts/audit_tasgaonkar.py` and its synthetic test file. Existing metrics remain, with additive year-label, redundant-date, discrepancy-block, duplicate-payload and identifier diagnostics. Output records source row numbers and raw timestamp fields by position. Candidate parsed values are naive diagnostics, not corrected or aligned data. No UTC conversion, timestamp rounding or model-ready file is produced.

```powershell
python -B -m scripts.audit_tasgaonkar --data-dir data/tasgaonkar/v1 --output outputs/tasgaonkar/integrity.json
python -B -m unittest discover -s tests -v
```

The complete suite passed **31 tests** on Python 3.13: 12 original thermal tests, 10 Phase 2A audit tests and 9 new integrity tests. New coverage includes year labels, exact channel mapping, normalization collisions, leading zeros, duplicate categories, raw-row distinctions, redundant date formats, reception dates, contiguous blocks and positional Time fields. Tests use synthetic records and do not validate empirical data quality. The real-data audit also completed successfully. Detailed outputs contain logger identifiers and must not be committed. This report contains aggregate counts and weather-only source references.

## Recommendation requiring review

Do not proceed to calibrated or household-held-out model validation. Seek explicit study clock/deployment clarification through a separately authorized request, or approve an alternative data strategy. If clarification is unavailable, preserve these blocked findings and keep Jalna limited to descriptive exploration with declared clock assumptions. New physical parameter evidence and a revised sample-size/validation design would still be needed even if these integrity questions were resolved. No author messages were sent and no next phase was started.
