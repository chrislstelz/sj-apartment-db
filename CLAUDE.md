# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Copy new PDF from intake folder and generate thumbnail:
```bash
cp "pdfs/N. {ID}.pdf" "floor-plans/{ID}.pdf"
python3 scripts/process_pdf.py {ID}
```
Reads `floor-plans/{ID}.pdf`, writes `thumbnails/{ID}.png` (1000×1000px square, white background, greyscale linework).

Export spreadsheet to JSON (required after any edit to `database.xlsx`):
```bash
python3 scripts/export_json.py
```

Publish updates to the live viewer (run after adding units):
```bash
git add database.json database.xlsx thumbnails/ floor-plans/
git commit -m "add {ID}"
git push
```
Live URL: https://chrislstelz.github.io/sj-apartment-db/viewer.html

View the database locally: open `viewer.html` directly in a browser (no server needed — it uses `fetch` on a local file, so serve with `python -m http.server` if your browser blocks local fetch).

Dependencies: `pip install openpyxl pymupdf pillow`

## Architecture

Static stack — no build process, no backend:

```
database.xlsx  →  scripts/export_json.py  →  database.json  →  viewer.html
```

- **database.xlsx** — source of truth; one sheet "Apartments", columns A–K
- **export_json.py** — reads xlsx with openpyxl, writes JSON array to `database.json`; checks `thumbnails/` for matching PNGs
- **process_pdf.py** — converts `floor-plans/{ID}.pdf` → `thumbnails/{ID}.png`; renders at 8×, applies 3-zone greyscale tone mapping, erases artifacts and text, crops to content, pads to 1000×1000px square
- **database.json** — generated; do not edit by hand
- **viewer.html** — standalone HTML+JS; fetches `database.json`, renders a filterable card grid with modal detail view
- **pdfs/** — intake folder for new PDFs from the user; filenames have a numeric prefix (`1. SING-2B-001.pdf`); copy to `floor-plans/` with clean name before processing
- **floor-plans/** — one PDF per unit, named `{ID}.pdf` (e.g. `floor-plans/SING-2B-001.pdf`)
- **thumbnails/** — processed PNG thumbnails, named `{ID}.png`, 1000×1000px square
- **THUMBNAIL REFERENCE STYLE GUIDE/** — reference images and `STYLE_GUIDE.md` describing the target thumbnail aesthetic

---

# Apartment Database — Studio Johnston

This project maintains a database of typical apartment units developed by the practice. The goal is to make our accumulated typology searchable so we can pull relevant precedents quickly when working on new projects.

## What the database is for

Primary use: filtering precedents by criteria. Example query: "show me all corner 3-bed apartments with approximate dimensions 9m × 12.5m."

Secondary use (future): cross-referencing against feasibility plates to find which existing units could fit a given footprint.

The database is read-mostly. Adding new units is occasional; querying is daily.

## How to read this document

When working on this project, read this file first, then check `database.xlsx` for the current state of the data. Every convention below has been worked out in practice and should be followed exactly. If something seems wrong or incomplete, ask before changing it — the conventions encode decisions that look arbitrary in isolation but matter for consistency.

## Database schema

`database.xlsx` has one sheet, `Apartments`, with these columns:

1. **Thumbnail Image** — embedded image of the unit plan (200px tall)
2. **Unique Apartment ID** — see ID format below
3. **Number of Bedrooms** — integer; studies do not count
4. **Number of Bathrooms** — integer; includes bathrooms, ensuites, and powder rooms
5. **Frontage Type** — one of: Single aspect, Corner, Cross-through, Other
6. **Dimension Width (m)** — decimal metres; for standard units this is the frontage width
7. **Dimension Width 2 (m)** — decimal metres; only used for cross-through units with differing frontage widths (wedge units)
8. **Dimension Depth (m)** — decimal metres; perpendicular to the frontage
9. **Reference Project** — project name, suburb, unit number, level
10. **Area (m²)** — internal floor area of the apartment; integer or one decimal
11. **Study** — "Yes" or "No"; whether the unit contains a study (does not affect bedroom count)

The spreadsheet is grouped by frontage type, then sorted by bedroom count, then by sequence number. Each frontage group has a subtle background tint for visual scanning.

## ID format

`{FRONTAGE}-{N}B-{NNN}`

- `FRONTAGE` is one of: `SING`, `COR`, `XTHR`, `OTH`
- `N` is the bedroom count
- `NNN` is a zero-padded sequence number within the (frontage, bedrooms) group

Examples: `SING-2B-004`, `COR-3B-002`, `XTHR-2B-001`, `OTH-3B-001`

Important: `XTHR` is used (not `CRO`) for cross-through, because `CRO` is visually too close to `COR`.

When adding a new unit, find the highest existing number in its (frontage, bedrooms) group and increment. If a unit is later reclassified between frontage types, all downstream IDs in both affected groups need to be re-derived to keep the sequence clean.

## Frontage taxonomy

Four categories:

**Single aspect** — exactly one external face. The unit is bounded on three sides by party walls or internal building elements (lift cores, circulation, stair cores, service risers). The single external face is the frontage.

**Corner** — two external faces meeting at a corner (perpendicular). The other two faces are internal. If a unit happens to have three external faces (e.g. at the end of a wing facing a courtyard), it is still recorded as Corner — the category is defined by the perpendicular pair, not the count of external faces.

**Cross-through** — two external faces on opposite sides of the unit. The unit has frontages at front and back, with party walls on the two short ends. Wedge-shaped cross-through units (where the two frontages have different widths) use the Width 2 field.

**Other** — last resort. Used for units that genuinely do not fit the three standard typologies. The clearest example is a full-floor luxury apartment with zero party walls and external faces on all sides. Three-aspect units bounded by a courtyard on one side are NOT Other — they are Corner. Use Other sparingly; it should remain a small fraction of the database.

## The party-wall test (frontage diagnostic)

For each of the unit's four edges, trace what is on the other side:

- **Another unit (party wall)** → internal edge
- **Internal circulation, lobby, corridor** → internal edge
- **Stair core, lift core, service riser** → internal edge
- **Outside air, street, garden, balcony beyond, light court** → external edge

Count only the external edges. One = Single aspect. Two perpendicular = Corner. Two opposite = Cross-through. Anything else = Other.

The default assumption when an edge is ambiguous is internal. Do not infer external faces from:
- Trellis planting, greenery, or landscape on the other side of a crop boundary (this could be a courtyard, balcony, or light well — not necessarily an external wall)
- The unit's apparent position at the edge of a wing (the wing may extend further in plan than the cropped view shows)
- Curved corners or feature geometry (these are often internal architectural treatment, not external)

Confirm an external face by seeing actual window or door symbols on that wall, or by verifying the absence of a neighbouring unit on the other side.

## Bedroom and bathroom counting

**Bedrooms**: count rooms labelled "BED", "BEDROOM", "Bed 1", "Bed 2", etc. Do not count: studies, media rooms, libraries, dens, sitting rooms, or any room labelled with anything other than a bedroom designator. A unit labelled "2 Bed +" on the source drawing is recorded as 2 bedrooms — the "+" denotes a study which does not count.

**Bathrooms**: count all wet rooms. This includes rooms labelled BATH, BATHROOM, ENS, ENSUITE, PWD, POWDER, or any similar designator. A unit with one main bathroom + one ensuite + one powder room = 3.

## Dimensions

Width and depth are recorded in metres to one decimal place (occasionally two for unusual dimensions).

For standard units (Single, Corner, Cross-through):
- **Width** = the frontage dimension (the wall containing the primary external face)
- **Depth** = the dimension perpendicular to the width

For corner units where there are two frontages, either dimension can be width — be consistent within the project.

For cross-through units with differing frontage widths (wedge units), record the larger as Width, the smaller as Width 2, and the depth between them as Depth.

For Other units, Width and Depth describe the bounding box rather than a frontage and a depth. Width by convention is the longer dimension.

## Adding new units

The current intake workflow uses clean single-apartment PDFs:

**What the user provides:**
- A PDF of a single floor plan dropped into the `pdfs/` folder, named with a numeric prefix (e.g. `3. SING-1B-001.pdf`)
- A text box embedded in the corner of the PDF containing the apartment ID and reference project (e.g. `SING-2B-005 / Amara Alexandria APT 403 L4`); "TYPICAL" is used when there is no specific reference project
- Area (m²) labelled on the drawing itself (room schedule label or title block)

**What Claude interprets from the drawing:**
1. **Frontage type** — apply the party-wall test (see below). Default to Single aspect when in doubt.
2. **Dimensions** — read width and depth from dimension annotations on the drawing.
3. **Bedrooms** — count rooms labelled BED / BEDROOM / Bed N (per rules below). Do not count study.
4. **Bathrooms** — count all wet rooms (BATH, ENS, PWD, etc.).
5. **Study** — record "Yes" if any room is labelled STUDY or similar; otherwise "No".
6. **Area** — read from the drawing label; record as integer or one decimal.

**Steps:**
1. Copy the PDF from `pdfs/` to `floor-plans/`, stripping the numeric prefix: `cp "pdfs/N. {ID}.pdf" "floor-plans/{ID}.pdf"`
2. Read the PDF. Confirm the apartment ID and reference from the corner text box.
3. Interpret the six fields above from the drawing.
4. Run `python3 scripts/process_pdf.py {ID}` to generate the thumbnail.
5. Insert a new row in `database.xlsx` in the correct sorted position (frontage group → bedroom count → sequence number).
6. Run `python3 scripts/export_json.py` to regenerate `database.json`.
7. Re-derive downstream IDs in any affected group if a reclassification occurred.

If anything is ambiguous, ask before recording. Common ambiguities:
- Party wall positions when adjacent units share similar layouts
- Whether a dimension spans two units rather than just the subject unit
- Whether an external wall counts as a frontage when no window/door is shown
- Unlabelled rooms that could be a study or a bedroom

## Querying the database

The primary interface is `viewer.html` — open it in a browser. It loads `database.json` and provides filters for frontage type, bedrooms, bathrooms, width range, depth range, area range, and a "Has study" toggle, with thumbnails displayed in a grid.

To regenerate `database.json` after editing the spreadsheet:
```bash
python3 scripts/export_json.py
```

The viewer is read-only. Edits to the database are made directly in `database.xlsx` (in Excel) or via Claude in this project.

## Source archive

Single-apartment floor plan PDFs are stored in `floor-plans/`, named `{ID}.pdf`. The Reference Project column in the database identifies the source building, unit number, and level.

## Project history

The database started in May 2026 with three marketing-sheet pilot units (Amara, Rochford, Redfern). The workflow progressed from marketing sheets → annotated archive plans with red clouds → blue clouds → blue rectangular bounding boxes with explicit dimensions → the current convention of clean single-apartment PDFs with an embedded corner text box.

Area (m²) and Study fields were added when the PDF workflow was adopted. Conventions for the "Other" category, the inclusion of powder rooms in bathroom counts, the `XTHR` code, and the party-wall diagnostic were all added based on cases that exposed gaps in earlier rules. New conventions should be documented in this file when they're decided.

As of May 2026 the database contains 3 units: SING-1B-001, SING-2B-001, XTHR-2B-001. Earlier entries from archival multi-unit PDFs were removed; the database now reflects only units with clean single-apartment source PDFs.

## Thumbnail processing notes

The `process_pdf.py` pipeline uses a **3-zone greyscale tone mapping** (not a binary threshold):
- Pixels 0–80 → black (wall lines, strong outlines)
- Pixels 80–200 → light grey / `MID_GREY=210` (furniture, joinery, floor textures)
- Pixels 200+ → white (background, coloured fills)

The target aesthetic is described in `THUMBNAIL REFERENCE STYLE GUIDE/STYLE_GUIDE.md`. In short: plain white background, walls as the dominant element, furniture and fixtures as very light grey linework, no labels or annotations.

The main remaining gap between current output and the reference style is **wall poche rendering**: the reference shows white-filled wall sections with a black outline; the current source PDFs use solid dark wall fills which render as grey in the mid-zone. Achieving true white poche requires the source PDFs to be prepared with wall hatching as white fill + black outline stroke.
