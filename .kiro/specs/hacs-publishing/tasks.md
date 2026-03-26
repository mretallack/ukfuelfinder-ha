# HACS Publishing Tasks

## Tasks

- [x] Task 1: Create `brand/` directory with icon
  - Create `custom_components/ukfuelfinder/brand/`
  - Copy fuel-pump.png as `icon.png` (512x512 RGBA PNG)
  - Source: Flaticon fuel pump icon (ID 3815878)

- [x] Task 2: Add HACS validation GitHub Action
  - Added `validate-hacs` job to `.github/workflows/validate.yml`
  - Uses `hacs/action@main` with category `integration`
  - Added `schedule` and `workflow_dispatch` triggers

- [x] Task 3: Add icon attribution to README
  - Added Flaticon attribution to Acknowledgments section

- [x] Task 4: Add image to README
  - Added brand icon to README header

- [x] Task 5: Bump version to 1.5.0
  - Updated `manifest.json` version
  - Updated CHANGELOG.md

- [x] Task 6: Set GitHub repo description and topics (manual)
  - Description set ✅
  - Topics set ✅

- [ ] Task 7: Create GitHub Release v1.5.0 (manual, after merge)
  - Merge feature branch to main
  - Tag v1.5.0
  - Create GitHub Release with changelog
