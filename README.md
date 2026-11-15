# A.R.T.E.M.I.S. · Aerospace Resilience, Telemetry, and Evaluation of Medical and Internal Stress

> **Developed by [LABQUIP](https://www.spaceappschallenge.org/2026/find-a-team/labquip/) — NASA Space Apps Challenge**  
> *Autonomous biomedical evaluation agent, multiparametric telemetry console, and predictive life-support system for long-duration spaceflight and vulnerable populations on Earth.*

---

## NASA Data, Protocols & Space Agency Resources Utilized

To ensure immediate clinical and operational validity for deep-space missions, **A.R.T.E.M.I.S.** integrates official NASA telemetry datasets, human factors instruments, countermeasure guidelines, and imagery:

| NASA Resource / Protocol | Integration in A.R.T.E.M.I.S. | Module / Source |
| :--- | :--- | :--- |
| **ISS TEPC Radiation Telemetry** *(Tissue Equivalent Proportional Counter)* | Real 1-minute resolution orbital dosimetry dataset (`1,441` samples, CDF ASCII export) used to build P50/P95/P99 reference strata across GCR and South Atlantic Anomaly (SAA) passes, plus NASA 30-day (`250 mSv`) and career (`600 mSv`) exposure limits. | **Radiation Module** (`_local/data_radiacion.csv`) |
| **NASA-TLX** *(NASA Task Load Index — Ames Research Center)* | Full 6-dimension subjective workload assessment (Mental, Physical, Temporal Demand, Performance, Effort, Frustration) + 15 pairwise comparisons integrated into the daily Allostatic Load Index (ALI). | **Mental Health Module** (`TlxForm.tsx`) |
| **SCAN Confocal Ultrasound & NASA Bone Research** | Non-invasive acoustic bone demineralization tracking (BUA, UV/SOS, ATT) and trabecular bone volume fraction (`BV/TV`) regression modeling for microgravity environments. | **Bone Density Module** (`bone.py`) |
| **NASA ISS Countermeasure Protocols (ARED / EVA)** | Automated clinical triage prescriptions referencing the **Advanced Resistive Exercise Device (ARED)**, mission radiation shelter protocols, and **EVA / Robotics** operational restrictions. | **Autonomous Triage Engine** |
| **ISS Earth Observation Imagery** | Public-domain orbital photography from the International Space Station (*"In Darkness viewing Jakarta | ISS"*, NASA / Friends of NASA) powering the console's orbital viewport. | **UI Viewport** (`space-bg.jpg`) |

---

## Executive Summary & Value Proposition

In deep-space missions (Artemis program and Martian transit), communication latency and high cognitive load prevent crews from manually interpreting raw clinical tables. **A.R.T.E.M.I.S.** transforms scattered physiological inputs into an autonomous triage workflow:

```
plan -> measure -> evaluate -> predict -> prescribe -> export
```

1. **Integrated Multiparametric Monitoring (4 Active Nodes):** Real-time evaluation of **bone demineralization** (SCAN confocal acoustic method: BUA, UV/SOS, ATT, and predicted BV/TV), **neuroendocrine stress** (circadian salivary cortisol via CLIA/ECLIA), **dosimetric stress** (environmental radiation via TEPC across Layers A/B/C), and **allostatic load / mental health** (NASA-TLX, DMRS/CDA, sleep architecture, and PVT-B).
2. **Biomimetic Interface & Empathetic Triage:** A.R.T.E.M.I.S. (embodied by our spacefaring sea turtle agent) acts as an early-warning co-pilot that translates complex mathematical deviations into immediate operational statuses (`NOMINAL`, `CAUTION`, `WARNING`, `CRITICAL`), minimizing decision fatigue for both astronauts and flight surgeons.
3. **Dual Impact (Spaceflight + Terrestrial Extrapolation):**
   - **Scientific Research (Big Data):** Standardized massive data export (long-format `CSV`, `JSON`, `PDF`, and `HTML`) ready to feed bioinformatic pipelines and longitudinal studies.
   - **Clinical Deployment on Earth:** The built-in predictive engine and normative population tables allow immediate deployment in terrestrial geriatric and hospital settings for preventive screening of **osteopenia, osteoporosis, and frailty syndrome** in older adults.

---

## Tech Stack

| Layer | Technology | Rationale |
| --- | --- | --- |
| Toolchain | **mise** (node 24, python 3.13, uv, bun) | Single reproducible environment, no admin privileges required |
| Backend | **FastAPI + SQLModel + SQLite** | Strict schema validation, OpenAPI specs, and local `.db` persistence |
| Science Core | **Pure Python** (zero heavy dependencies) | Testable, auditable, and 100% deterministic biomedical domain |
| Frontend | **React 19 + TypeScript + Vite** | Domain-driven modular components with strict static typing |
| Remote State | **TanStack Query** | Reactive caching, automatic invalidation, and loading states |
| i18n | **react-i18next** + backend catalogs | Real-time bilingual support (`en` and `es`) |
| Dev Runtime | **bun** | Ultra-fast dependency installation and concurrent `bun run dev` |

Zero mandatory cloud dependencies or heavy containers: the entire telemetry stack runs locally with zero latency, engineered for isolated orbital habitats or rural clinics on Earth.

---

## Quick Start (Step-by-Step Execution Guide for Judges)

Tested on **Windows 10/11** via **Visual Studio Code** and **PowerShell**.

### 1. Initial Environment Setup (First-Time Only)

Open **Visual Studio Code**, press `Ctrl + Shift + P`, select **`Terminal: Create New Terminal`**, and run the following commands in **PowerShell** to enable script execution and install the required toolchain:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

winget install --id Git.Git -e --source winget
winget install --id jdx.mise -e --source winget
winget install --id Cloudflare.cloudflared -e --source winget
```

### 2. Clone, Build, Seed & Launch

**Restart Visual Studio Code**, open a new **PowerShell** terminal, and execute:

```powershell
mise activate pwsh | Out-String | Invoke-Expression
git clone [https://github.com/Celeste-abigail/nasa](https://github.com/Celeste-abigail/nasa) nasa-space
cd nasa-space

mise trust
mise install
mise exec -- bun run setup

# Load simulated telemetry and sample astronaut profiles (AST-01, AST-02, AST-03)
mise run seed

# Launch FastAPI backend + Vite web console with live reload
mise run dev
```

- **Web Console (`A.R.T.E.M.I.S.`)**: <http://127.0.0.1:5173>
- **API / Swagger Docs**: <http://127.0.0.1:8000/docs>
- **Healthcheck**: <http://127.0.0.1:8000/api/health>

### 3. Live Remote Sharing via Cloudflare Tunnel (Optional)

To expose your local instance via a temporary public HTTPS link for remote testing or live demonstrations, open a second **PowerShell** terminal and run:

```powershell
cloudflared tunnel --url [http://127.0.0.1:5173](http://127.0.0.1:5173)
```

---

## User Experience & Biomimetic UI (`A.R.T.E.M.I.S.`)

Launching the platform opens the **Overview** command center, consolidating the active astronaut's status alongside the **A.R.T.E.M.I.S.** agent and four telemetry cards (Bone Density, Cortisol, Radiation, and Mental Health) displaying operational severity, primary metrics, secondary indicators, last timestamp, and trend sparklines.

- **Quick Node Filters**: Interactive filter chips persisted in `localStorage["nasa-space-summary"]`.
- **General Status HUD**: Summarizes critical counters for the active subject, the number of modules requiring intervention, and A.R.T.E.M.I.S.'s contextual clinical note.
- **Cache Synchronization**: TanStack Query reuses `monitoring`, `cortisol`, `radiation`, and `mental` queries when drilling down into detailed module views.
- **Fault Isolation**: If a sensor or module has no recorded readings or experiences an API failure, its card reports the state independently without blocking the rest of the console.

### Visual Identity & Biomimetic Design

- **Voronoi Tessellated Armor (Biomimicry)**: Primary containers feature a custom vector pattern in the top-right corner inspired by the shedding cranial scutes of a sea turtle (*Chelonia mydas*), paired with 45° beveled octagonal geometry across cards, navigation tabs, and controls.
- **Abyssal-Nebula Palette**: Deep space gradients (`#050a14` → `#0b1225` → `#160e2a`) with technical cyan borders (`rgba(56, 189, 248, 0.26)`) and top laser status bars driven by clinical severity (`NOMINAL`, `CAUTION`, `WARNING`, `CRITICAL`).
- **Aerospace Typography**: **Chakra Petch** (technical headers and primary metrics), **Space Grotesk** (clinical body copy), and **JetBrains Mono** (numerical telemetry, badges, and chart axes) via Google Fonts.
- **Operational Standardization**: Top-left **LABQUIP** emblem linked directly to the official NASA Space Apps team profile, top-right language switcher (`ES | EN`), contextual anatomical site selector embedded inside the Bone Density module, and unified data-capture panels (`// RECORD DATA` and `IMPORT DATA +`).
- **Orbital Imagery**: Smooth orbital pan over the nighttime photograph *"In Darkness viewing Jakarta | International Space Station"*, credited with a direct link to [Friends of NASA](https://www.friendsofnasa.org/search?updated-max=2024-07-31T12:43:00-07:00&max-results=16&reverse-paginate=true&m=0&hl=es-ES).

### Crew Management & Scientific Data Export

- **Crew Roster**: Header controls to register new astronauts (code, name, sex, date of birth) and archive them reversibly without losing historical time series.
- **Research Exports**:
  - Clinical reports: `summary.html` (printable), `summary.pdf` (generated via ReportLab), and `summary.json`.
  - Raw datasets for data science: `data.json` and a unified long-format `data.csv` (`module,recorded_at,metric,value,unit,flags,notes`).

---

## System Architecture

Built on **Screaming Architecture** principles with strict four-layer separation and unidirectional dependencies:

```
api (HTTP) → modules (use cases) → domain (pure biomedical rules) ← infrastructure (SQLite, file I/O)
```

```
backend/
  app/
    core/            configuration, in-process event bus, i18n, shared dependencies
    domain/          SQLModel entities, Pydantic schemas, mathematical engines (bone.py, etc.)
    infrastructure/  SQLite engine, repositories, file parsers
    modules/
      astronauts/    crew profile management
      measurements/  data entry, domain validation, and bulk CSV/XLSX/JSON import
      monitoring/    longitudinal evaluation, loss rates, and clinical triage
    api/v1/          FastAPI routers (HTTP contracts)
    i18n/            es.json / en.json catalogs (backend clinical messages)
    scripts/         reference builders and sample data seeding
  tests/             pytest suite: pure mathematical domain + full HTTP integration
frontend/
  src/
    lib/             typed API client, severity calculators, number/date formatters
    i18n/            es/en catalogs and react-i18next setup
    modules/
      shell/         unified Header, language switcher, and navigation
      overview/      main HUD, interactive A.R.T.E.M.I.S. agent, and SummaryCards
      measurements/  3-step data recording wizard and bulk import
      monitoring/    KPIs, custom SVG vector charts, and history tables
```

### Event-Driven Bus

`app/core/events.py` implements an in-process event bus that decouples data ingestion from evaluation caches:

| Topic | Triggered When | Immediate Effect |
| --- | --- | --- |
| `measurement.created` | A new measurement is recorded | Invalidates the astronaut's evaluation cache |
| `measurement.imported` | A bulk file import completes | Recomputes series and invalidates evaluation cache |
| `astronaut.created` | A new crew member is registered | Initializes context and invalidates cache |

### Database

- Local file: `backend/data/nasa_space.db` (git-ignored), automatically initialized by FastAPI/Uvicorn's lifespan manager.
- Configurable via `NASA_DATABASE_URL` to support any SQLAlchemy-compatible engine (including PostgreSQL in production).

---

## Scientific Foundation & Clinical Rules by Module

### 1. Bone Density Module (SCAN Confocal Acoustic Method)

Captures **BUA** (Broadband Ultrasound Attenuation), **UV/SOS** (Ultrasound Velocity / Speed of Sound), and **ATT**, estimates trabecular bone volume fraction (**BV/TV**) using published regression models, and evaluates demineralization velocity against baseline:

| Concept | Mathematical Rule / Threshold |
| --- | --- |
| **Predicted BV/TV** | `3.89e-4 · UV − 9e-4 · BUA − 0.456` |
| **Baseline** | First historical measurement for each astronaut **per anatomical site** (`calcaneus` / `femoral_neck`) |
| **Cumulative Loss** | `(BUA_base − BUA_current) / BUA_base · 100` |
| **Monthly Loss Rate** | `cumulative_loss / months_since_baseline` (minimum 0.1 months) |
| **Level 1 · Nominal** | Rate `< 0.8 %/month` |
| **Level 2 · Caution / Risk** | `0.8 ≤ rate ≤ 1.5 %/month` |
| **Level 3 · Critical Alert** | Rate `> 1.5 %/month` **or** cumulative loss `> 3 %` |

- **Strict Domain Validation** (rejects physically impossible inputs rather than extrapolating): `0 < BUA < 200 dB/MHz`, `1200 ≤ UV ≤ 2000 m/s`, `0 < ATT < 200 dB/cm`. Session dates must be subsequent to baseline.
- **Scientific References (DOI)**: [10.1117/12.810048](https://doi.org/10.1117/12.810048) · [10.1016/j.actaastro.2012.08.032](https://doi.org/10.1016/j.actaastro.2012.08.032) · [10.1121/1.4784949](https://doi.org/10.1121/1.4784949).

#### Normative Population Reference & Geriatric Extrapolation (Shin et al., 2005)

Matches the subject's sex and exact age on the measurement date against 12 normative cohorts (n = 3,053 adults):

| Sex | Age Group | n | BUA Mean ± SD (dB/MHz) | SOS Mean ± SD (m/s) |
|---|---|---:|---|---|
| Male | 20-29 | 50 | 121.4 ± 15.6 | 1556.1 ± 47.7 |
| Male | 30-39 | 77 | 121.2 ± 15.7 | 1554.6 ± 40.2 |
| Male | 40-49 | 137 | 119.2 ± 13.9 | 1548.7 ± 40.7 |
| Male | 50-59 | 327 | 114.2 ± 13.1 | 1545.0 ± 35.0 |
| Male | 60-69 | 506 | 111.6 ± 13.8 | 1541.0 ± 32.4 |
| Male | 70-74 | 128 | 108.7 ± 16.0 | 1527.3 ± 30.8 |
| Female | 20-29 | 55 | 113.2 ± 13.6 | 1556.1 ± 28.2 |
| Female | 30-39 | 109 | 113.9 ± 13.9 | 1548.5 ± 29.4 |
| Female | 40-49 | 228 | 111.1 ± 13.8 | 1547.3 ± 32.1 |
| Female | 50-59 | 519 | 105.2 ± 12.9 | 1537.3 ± 28.0 |
| Female | 60-69 | 756 | 95.4 ± 11.7 | 1520.8 ± 23.0 |
| Female | 70-74 | 161 | 90.2 ± 11.7 | 1507.6 ± 20.5 |

Automatically computes **Z-scores** (age- and sex-adjusted) and **T-scores** (compared against young adults aged 20–29 of the same sex):

```
Z = (value − age_group_mean) / age_group_SD
T = (value − young_adult_mean_20_29) / young_adult_SD_20_29
```

- **WHO Classification on T-score**: `T > -1.0` Nominal · `-2.5 < T ≤ -1.0` Osteopenia · `T ≤ -2.5` Osteoporosis.

### 2. Salivary Cortisol Module (Circadian CLIA/ECLIA)

Evaluates salivary cortisol samples by dynamically interpolating the expected median for the **exact timestamp** of collection:

```
z = (ln(value) − ln(median(hour))) / σ_ln        Nominal |z| ≤ 1.28 · Caution ≤ 1.96 · Critical > 1.96
```

- Combined morning anchor (n = 56): median `0.474 µg/dL` (`σ_ln = 0.511`); nighttime anchor `0.155 µg/dL` with log-linear interpolation between 07:30 and 21:30.
- Automatic unit conversion between **µg/dL** and **nmol/L** (`÷ 27.59`).
- Additional clinical rules: post-11:00 assay floor check, manufacturer p95 external control (Roche Cortisol II), evening/night ratio (15:30/21:00), personal baseline computation (≥ 3 samples), and cross-module bone loss flag. Full details in [docs/cortisol-spec.md](docs/cortisol-spec.md).
- **Scientific References (DOI)**: [10.1016/j.psyneuen.2012.04.019](https://doi.org/10.1016/j.psyneuen.2012.04.019) · [10.1515/cclm-2006-0458](https://doi.org/10.1515/cclm-2006-0458) · [10.1038/s41526-018-0041-4](https://doi.org/10.1038/s41526-018-0041-4).

### 3. Space Radiation Module (TEPC Dosimetry)

Built upon real Tissue Equivalent Proportional Counter telemetry (`_local/data_radiacion.csv`, 1,441 one-minute samples). Evaluates exposure across three hierarchical layers (overall severity equals the worst layer):

- **Layer A · Instantaneous**: `≤ P95` Nominal · `P95–P99` Caution · `> P99` Critical (requires 3 consecutive readings to prevent false positives from transient spikes).
- **Layer B · Daily**: 24-hour cumulative dose against daily reference.
- **Layer C · Cumulative Mission & Career**: Computes `F30 = H30 / 250 mSv` (30-day limit) and `F_career = (prior_dose + mission_dose + projected_dose) / 600 mSv`. Full details in [docs/radiation-spec.md](docs/radiation-spec.md).
- **Scientific References (DOI)**: [10.1016/j.lssr.2020.04.001](https://doi.org/10.1016/j.lssr.2020.04.001) · [10.1667/RR1889.1](https://doi.org/10.1667/RR1889.1) · [10.1029/2009SW000492](https://doi.org/10.1029/2009SW000492).

### 4. Mental Health & Allostatic Load Module (ALI)

Non-invasive psychometric and neurobehavioral screening battery:

- **Post-Task NASA-TLX**: 6-dimension subjective workload scale + 15 pairwise comparisons, tracking EWMA curves against Grier's global reference and personal baselines.
- **Daily Mood Check (CDA / DMRS)**: 10 affective items with a 14-day rolling baseline.
- **Personalized Sleep Architecture**: Morning log tracking TIB/TST/SE, Sleep Regularity Index (SRI), and 7-day cumulative sleep debt.
- **Interactive PVT-B**: 60/180 s psychomotor vigilance task quantifying attentional lapses, false starts, response speed, and objective vs. subjective fatigue discrepancy. Full details in [docs/mental-spec.md](docs/mental-spec.md).
- **Scientific References (DOI)**: [10.1016/S0166-4115(08)62386-9](https://doi.org/10.1016/S0166-4115(08)62386-9) · [10.1177/1541931215591373](https://doi.org/10.1177/1541931215591373) · [10.5665/sleep.1158](https://doi.org/10.5665/sleep.1158).

---

## REST API Contracts

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Service health status and database connection |
| GET | `/api/v1/meta` | Model metadata, thresholds, units, anatomical sites, and languages |
| GET | `/api/v1/astronauts` | List active and archived astronauts |
| POST | `/api/v1/astronauts` | Register crew member (`{"code","name","sex","birth_date"}`) |
| PATCH | `/api/v1/astronauts/{code}` | Update demographic profile |
| GET | `/api/v1/astronauts/{code}/measurements?site=` | List ultrasonic bone sessions |
| POST | `/api/v1/astronauts/{code}/measurements` | Record new bone measurement |
| POST | `/api/v1/astronauts/{code}/preview` | Evaluate measurement without saving (wizard step 3) |
| POST | `/api/v1/astronauts/{code}/measurements/import` | Bulk file import (CSV/XLSX/JSON) |
| GET | `/api/v1/astronauts/{code}/monitoring?site=&window=&lang=` | Evaluated series, BV/TV, Z/T-scores, and triage level |
| POST | `/api/v1/astronauts/{code}/cortisol` | Record and evaluate circadian salivary cortisol sample |
| GET | `/api/v1/astronauts/{code}/cortisol?days=` | Cortisol time series, evening/night ratio, and baseline |
| POST | `/api/v1/astronauts/{code}/cortisol/import` | Bulk import cortisol samples |
| GET | `/api/v1/astronauts/{code}/radiation` | TEPC readings + Layers A/B/C evaluation + career projection |
| POST | `/api/v1/astronauts/{code}/radiation` | Record dosimetric reading (UTC) |
| GET | `/api/v1/astronauts/{code}/mental?days=` | Daily EWMA series, Allostatic Load Index (ALI), and zone |
| PUT | `/api/v1/astronauts/{code}/mental/{date}` | Save/replace daily cognitive and mood assessment |

---

## Bulk Data Import Format

Supports **CSV**, **XLSX**, and **JSON** files with row-by-row validation (malformed rows are reported with line numbers without aborting valid rows):

```csv
date,bua,uv,att,site
2026-07-01,118.0,1552,52,calcaneus
2026-07-31,77.5,1556,51.6,calcaneus
```

- Accepted date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYY/MM/DD`, `DD-MM-YYYY`, `MM/DD/YYYY`.
- Accepted sites: `calcaneus` and `femoral_neck`.
- Ready-to-use sample files are available in the `examples/` directory.

---

## Quality Assurance & Project Status

- **127 automated backend tests** (domain rules, normative references, cortisol, radiation, mental health, and HTTP endpoints) and **4 frontend test suites** passing in green.
- Clean **Ruff** linting, strict **TypeScript** type-checking, and verified production build.

See [DEV.md](DEV.md) for daily development workflows and maintenance commands.