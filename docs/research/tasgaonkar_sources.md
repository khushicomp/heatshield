# Tasgaonkar dataset: verified sources and acquisition

Checked 2026-10-09. Phase 2A only; no calibration or model validation.

- Publication: Tasgaonkar et al. (2022), *Indoor heat measurement data from low-income households in rural and urban South Asia*, Scientific Data 9, 285. https://doi.org/10.1038/s41597-022-01314-5
- Versioned dataset: https://doi.org/10.6084/m9.figshare.12546368.v1
- Metadata directly read from https://api.figshare.com/v2/articles/12546368/versions/1
- API identity verified: article 12546368, version 1, matching title and dataset DOI.
- Repository license directly observed: **CC0**, https://creativecommons.org/publicdomain/zero/1.0/ . This establishes dataset reuse permission; privacy review remains necessary. Cite the authors and both DOIs despite CC0 not requiring attribution.

The web browsing tool could not access Figshare; a standard-library HTTPS request through the approved network path succeeded. No credentials or new packages were required.

## Official version-1 inventory

The API lists 20 files: 15 CSVs, two DOCs, two DOCXs and one PDF. Its description refers to four DOCs and a separate Data Supplement.doc, but the actual manifest contains the following files. The manifest is authoritative for acquisition; do not invent an additional file.

| File | Public file ID | Bytes | Manifest MD5 | Downloaded locally |
|---|---:|---:|---|---|
| Faisalabad AWS Data.csv | 23348489 | 1282871 | a7811f7994b1470836ef3c4e2f03d29e | No |
| Jalna AWS Data.csv | 23348492 | 672682 | 180f89d47f74f23b715baeffa18068df | Yes |
| Yavatmal AWS Data.csv | 23348504 | 1472553 | eceb4e2ba3439a69ebe5d5fc0ac13b9c | No |
| Delhi AWS Data.csv | 23348507 | 1296639 | 65e611169e67cf64579c55530b5ef5ef | No |
| Dhaka AWS Data.csv | 23348513 | 738638 | c70079c64c0599f154987a6ff3d63325 | No |
| Informed Consent Form - WOTR.doc | 23348453 | 27136 | aec95212b25197ab7b16b0b238a917c5 | Yes |
| Faisalabad Housing Structure Data.csv | 34160631 | 12290 | a01be1e1a9c2f1f6b7789a0698b036ba | No |
| Jalna Housing Structure Data.csv | 34160634 | 6906 | af7e941ba8da5eb639fb4dbaac1c89c8 | Yes |
| Yavatmal Housing Structure Data.csv | 34160637 | 8370 | b3b0180b4eb81fde91d9215c67909eaf | No |
| Delhi Housing Structure Data.csv | 34160640 | 12283 | 173ae73429514d6a82f42232864191e0 | No |
| Dhaka Housing Structure Data.csv | 34160643 | 13217 | 9e2c9d748024cff28f668e13f6295d1b | No |
| Jalna Indoor Data.csv | 34160847 | 6047909 | 0fbd5fac6e72d34f2082c8bd77e5a1cd | Yes |
| Yavatmal Indoor Data.csv | 34160889 | 14437008 | c701422016e8afdd3eb25b3e0b7b5e9b | No |
| Delhi Indoor Data.csv | 34160931 | 9346430 | 52dd74ca24cec26ae6fab334891ab70b | No |
| Dhaka Indoor Data.csv | 34160976 | 9948416 | ebba72d7acc8fe4fa1b8cb69cd9030f7 | No |
| Faisalabad Indoor Data.csv | 34160994 | 9211191 | 63aad059702e0ad363cf8e9606b0be44 | No |
| README FILE 1- Housing Roofing Structure.doc | 34161102 | 79872 | 72858e3a6b4a736f41364be9a6178895 | Yes |
| README FILE  2- Indoor Data Loggers.docx | 34161105 | 14359 | e5189cfecb561078912587c0122106b9 | Yes |
| README FILE 4 -Davis Installation Manual.pdf | 34161111 | 1467349 | e6489bff0df32927571f46ff74a27322 | Yes |
| README FILE 3 - AWS Urban-Rural Area.docx | 34161114 | 21885 | 4adf3e5a340a4cff9655bea9482fad74 | Yes |

Downloaded eight files totaling 8,338,098 bytes: three Jalna CSVs plus five supporting files. Every downloaded byte count and MD5 matched the versioned manifest. MD5 here checks transfer consistency, not cryptographic authenticity. HTTPS and the official repository establish provenance.

## Documentation inspection

- README 2 (DOCX): XML text inspected with standard-library ZIP/XML tools. Describes ten-minute indoor sampling, Celsius temperature, RH, logger-to-housing references and missing markers. It labels dates day/month/year.
- README 3 (DOCX): XML text inspected. Describes hourly weather aggregation and solar radiation in W/m2. Its generic labels differ from the Jalna CSV headers. Interval-start/end convention and timezone were not established.
- README 1 (legacy DOC): best-effort printable-text inspection recovered roof descriptions, ventilation category definitions, sensor-placement fields and the NA convention. This was not a complete structured DOC conversion. In particular, ventilation codes are qualitative, not W/K.
- Consent template and installation PDF: downloaded and checksum verified. Full semantic review was not completed in this bounded audit; no completed participant consent forms were acquired. PDF extraction was unavailable through the browser, and no conversion software was installed. These documents do not resolve the observed CSV timestamp conflicts in the evidence inspected.

The publication's measurement-quality procedures are evidence about data collection, not validation of HeatShield. The repository is a verified source; a model-ready interpretation of its files remains unverified.

## Reproduction and privacy

Download only the rows marked Yes using https://ndownloader.figshare.com/files/FILE_ID, after verifying the versioned license and manifest. Keep original filenames under `data/tasgaonkar/v1/`. Check sizes and MD5 against this table before auditing. Do not silently replace version 1 with latest files.

```powershell
python -B -m scripts.audit_tasgaonkar --data-dir data/tasgaonkar/v1 --output outputs/tasgaonkar/audit.json
python -B -m unittest discover -s tests -v
```

The script does not download, modify or clean source data. It uses only the standard library. Its JSON contains logger-level profiles and must remain local under ignored `outputs/`. Raw files, metadata cache, scratch investigation scripts and supporting documents remain under ignored `data/`. The tracked report contains aggregate findings only, not logger IDs, household demographics, locations or temperature traces. Review exports separately before sharing.
