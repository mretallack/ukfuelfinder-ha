# HACS Publishing Design

## Overview

This document describes the technical changes required to make the UK Fuel Finder integration fully compliant with HACS publishing requirements.

## Component Diagram

```
ukfuelfinder-ha/
├── .github/
│   └── workflows/
│       └── validate.yml          # Updated: add HACS validation job
├── custom_components/
│   └── ukfuelfinder/
│       ├── brand/                 # NEW: brand assets directory
│       │   └── icon.png           # NEW: fuel pump icon (256x256+)
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── manifest.json          # No changes needed
│       ├── sensor.py
│       ├── strings.json
│       └── translations/
│           └── en.json
├── hacs.json                      # No changes needed
├── README.md                      # Updated: add icon attribution + screenshots
└── ...
```

## Changes Required

### 1. Brand Assets

**Directory**: `custom_components/ukfuelfinder/brand/`

**Files**:
- `icon.png` — Square PNG, minimum 256x256. Source: Flaticon fuel pump icon (ID 3815878).

Custom integrations serve brand images locally via the HA API endpoint `/api/brands/integration/ukfuelfinder/icon.png`. The `brand/` directory inside the integration folder is the correct location for custom components (as opposed to the central brands repository used by core integrations).

**Icon source and license**:
- URL: https://www.flaticon.com/free-icon/fuel-pump_3815878
- License: Free for personal and commercial use
- Requirement: Attribution must be included
- Flaticon requires login to download — the developer must download the PNG manually

### 2. GitHub Actions — HACS Validation

**File**: `.github/workflows/validate.yml`

Add a new job `validate-hacs` alongside the existing `validate` job:

```yaml
  validate-hacs:
    runs-on: "ubuntu-latest"
    steps:
      - uses: actions/checkout@v3
      - name: HACS validation
        uses: "hacs/action@main"
        with:
          category: "integration"
```

Also add `schedule` and `workflow_dispatch` triggers so validation runs daily and can be triggered manually:

```yaml
on:
  push:
    branches:
      - dev
      - main
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:
```

The HACS action checks:
- Repository is not archived
- Brand assets exist
- Repository has a description
- `hacs.json` exists and is valid
- Info file (README) has images
- Issues are enabled
- Repository has topics

### 3. README Updates

**Icon attribution** — Add to the Acknowledgments section at the bottom of README.md:

```markdown
- Fuel pump icon by [Freepik - Flaticon](https://www.flaticon.com/free-icon/fuel-pump_3815878)
```

**Screenshots** — Add at least one screenshot showing the integration in Home Assistant. Suggested screenshots:
- Integration config flow
- Sensor entities list
- Map view with fuel stations
- Price history graph

Screenshots should be stored in a `docs/images/` directory or hosted externally (e.g. GitHub issue attachments). The HACS validation action checks for image references in the README.

**HACS badge** — Already present in README ✅

### 4. GitHub Repository Settings (Manual)

These must be done via the GitHub web UI or API:

**Description** (required):
```
A Home Assistant custom component for UK Government Fuel Finder API — monitor fuel prices at nearby petrol stations
```

**Topics** (required):
```
home-assistant, hacs, custom-component, fuel-prices, uk, home-assistant-custom-component, petrol, diesel
```

### 5. GitHub Releases (Manual)

Current state: Git tags v1.1.0, v1.2.0, v1.4.0 exist but may not have corresponding GitHub Releases.

For each tag (or at minimum v1.4.0), create a GitHub Release:
1. Go to repository → Releases → Draft a new release
2. Select the existing tag
3. Add release title (e.g. "v1.4.0")
4. Copy relevant CHANGELOG.md section into release notes
5. Publish

HACS uses GitHub Releases (not just tags) to present version selection to users.

## Sequence: HACS Repository Validation

```
Developer                GitHub Actions              HACS Action
   |                          |                          |
   |-- push/PR -------------->|                          |
   |                          |-- checkout repo -------->|
   |                          |                          |-- check archived
   |                          |                          |-- check description
   |                          |                          |-- check topics
   |                          |                          |-- check hacs.json
   |                          |                          |-- check manifest.json
   |                          |                          |-- check brand/icon.png
   |                          |                          |-- check README images
   |                          |                          |-- check issues enabled
   |                          |<-- pass/fail ------------|
   |<-- status report --------|                          |
```

## Sequence: User Installs via HACS

```
User                    HACS                     GitHub
  |                       |                        |
  |-- add custom repo --->|                        |
  |                       |-- validate repo ------>|
  |                       |<-- repo metadata ------|
  |                       |                        |
  |<-- show integration --|                        |
  |    (name, icon, desc) |                        |
  |                       |                        |
  |-- click download ---->|                        |
  |                       |-- fetch release ------>|
  |                       |<-- files --------------|
  |                       |                        |
  |<-- install complete --|                        |
  |    (restart required) |                        |
```

## Error Handling

| Scenario | Impact | Mitigation |
|---|---|---|
| Missing brand icon | HACS validation fails | Add `icon.png` to `brand/` directory |
| No GitHub description | HACS validation fails | Set description in repo settings |
| No GitHub topics | HACS validation fails | Add topics in repo settings |
| No images in README | HACS validation warns | Add screenshots |
| No GitHub Releases | HACS shows commit hash instead of version | Create releases from existing tags |

## Implementation Considerations

- The icon PNG must be downloaded manually from Flaticon (requires login)
- Screenshots require a running Home Assistant instance with the integration configured
- GitHub repo settings (description, topics) cannot be set from the local repo — must use GitHub UI or API
- The HACS validation action should be added as a separate job so it doesn't block the existing test workflow
