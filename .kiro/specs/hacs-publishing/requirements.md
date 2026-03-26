# HACS Publishing Requirements

## Overview

Publish the UK Fuel Finder Home Assistant integration to the HACS (Home Assistant Community Store) so users can discover, install, and update the integration directly from the HACS UI.

Reference: https://www.hacs.xyz/docs/publish/integration

## User Stories

### US-1: HACS Discovery

As a Home Assistant user,
I want to find UK Fuel Finder in the HACS store,
So that I can install it without manual file copying.

**Acceptance Criteria:**
- The repository passes HACS validation action
- The repository can be added as a custom repository in HACS
- The integration appears with correct name, description, and icon

### US-2: Brand Identity

As a Home Assistant user,
I want to see a recognisable fuel pump icon for the integration,
So that I can easily identify it in the HACS store and integrations list.

**Acceptance Criteria:**
- A `brand/` directory exists inside `custom_components/ukfuelfinder/`
- Contains at least `icon.png` (square, 256x256 or 512x512 PNG)
- Icon is properly licensed for commercial use with attribution
- Attribution is documented in README.md

### US-3: Repository Metadata

As a HACS user browsing the store,
I want to see a clear description, topics, and screenshots,
So that I can understand what the integration does before installing.

**Acceptance Criteria:**
- GitHub repository has a description set
- GitHub repository has relevant topics assigned
- README contains at least one screenshot/image of the integration in use

### US-4: Version Management

As a user with the integration installed,
I want to receive update notifications when new versions are released,
So that I can keep the integration up to date.

**Acceptance Criteria:**
- GitHub Releases exist (not just git tags)
- Release tags match the version in `manifest.json`
- HACS can detect and present available versions to the user

### US-5: Automated Validation

As a developer,
I want CI to validate HACS compatibility on every push and PR,
So that I catch publishing issues before they reach users.

**Acceptance Criteria:**
- GitHub Actions workflow includes the official `hacs/action` validation
- Validation runs on push, PR, and on a daily schedule
- Validation passes with category set to `integration`

## EARS Requirements

### Repository Structure

WHEN HACS scans the repository
THE SYSTEM SHALL find a single integration under `custom_components/ukfuelfinder/`

WHEN HACS reads `custom_components/ukfuelfinder/manifest.json`
THE SYSTEM SHALL find all required keys: `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`

WHEN HACS reads `hacs.json` in the repository root
THE SYSTEM SHALL find at minimum the `name` key

### Brand Assets

WHEN Home Assistant loads the integration
THE SYSTEM SHALL serve the brand icon from `custom_components/ukfuelfinder/brand/icon.png`

### GitHub Metadata

WHEN HACS indexes the repository
THE SYSTEM SHALL find a non-empty repository description

WHEN HACS indexes the repository
THE SYSTEM SHALL find at least one repository topic

### Validation

WHEN code is pushed to main or a PR is opened
THE SYSTEM SHALL run the HACS validation action and report pass/fail

## Current State Assessment

### Already Complete ✅

| Requirement | Status | Details |
|---|---|---|
| Repository structure | ✅ | `custom_components/ukfuelfinder/` with single integration |
| manifest.json | ✅ | All required keys present, version 1.4.0 |
| hacs.json | ✅ | Present in root with `name` and `homeassistant` keys |
| README.md | ✅ | Comprehensive documentation |
| Git tags | ✅ | v1.1.0, v1.2.0, v1.4.0 exist |

### Still Needed ❌

| Requirement | Status | Details |
|---|---|---|
| Brand icon | ❌ | Need `brand/icon.png` — using Flaticon fuel pump icon (ID 3815878) with attribution |
| GitHub description | ❌ | Must be set on GitHub repo settings |
| GitHub topics | ❌ | Must be set on GitHub repo settings |
| Screenshots in README | ❌ | HACS action checks for images in info file |
| HACS validation action | ❌ | Need to add `hacs/action` to CI workflow |
| GitHub Releases | ❌ | Tags exist but need actual GitHub Releases created |

## Icon Licensing

- **Source**: https://www.flaticon.com/free-icon/fuel-pump_3815878
- **License**: Free for personal and commercial use with attribution
- **Attribution**: `Icon by [Freepik - Flaticon](https://www.flaticon.com/free-icon/fuel-pump_3815878)`
- **Placement**: README.md acknowledgments section
