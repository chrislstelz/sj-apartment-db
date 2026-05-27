# Apartment Database

Internal reference library of apartment unit precedents developed by the practice.

## Quick reference

- **Browse the library**: https://chrislstelz.github.io/sj-apartment-db/viewer.html
- **Add a new unit**: drop the PDF in `pdfs/`, then ask Claude
- **Edit the data**: open `database.xlsx` in Excel, then run `python3 scripts/export_json.py`
- **Publish changes**: `git add database.json database.xlsx thumbnails/ floor-plans/ && git commit -m "add {ID}" && git push`

## What's in this folder

```
apartment-database/
├── CLAUDE.md           Office conventions and intake workflow — read this first
├── README.md           You are here
├── database.xlsx       The database (primary editable file)
├── database.json       Generated from database.xlsx for the viewer — do not edit by hand
├── viewer.html         Filterable browser-based viewer (also served live, see above)
├── pdfs/               Intake folder — drop new PDFs here before asking Claude to process them
├── floor-plans/        Source archive, one PDF per unit named by ID
├── thumbnails/         One PNG thumbnail per unit, named by ID
└── scripts/
    ├── export_json.py  Regenerates database.json from database.xlsx
    └── process_pdf.py  Generates thumbnails from floor plan PDFs
```

## First-time setup

Python 3 and the following libraries:

```bash
pip install openpyxl pymupdf pillow
```

## Daily use

**Looking for a precedent**: open the live viewer at https://chrislstelz.github.io/sj-apartment-db/viewer.html. Filter by frontage type, bedroom count, width, depth, area. Click any card for full details. The viewer is read-only.

**Adding a new unit**: drop the PDF in `pdfs/` with a numeric prefix (e.g. `7. SING-2B-002.pdf`), then ask Claude to process it. Claude will read the drawing, extract all fields, generate a thumbnail, and add the row to `database.xlsx`. After Claude finishes, run the git push to publish.

**Editing an existing unit**: open `database.xlsx`, edit the row, re-run `python3 scripts/export_json.py`, then push. If you change a unit ID, also rename the corresponding file in `thumbnails/` and `floor-plans/`.

**Viewing locally without an internet connection**: open `viewer.html` directly in a browser. If your browser blocks the local fetch, serve it with `python3 -m http.server` and open `http://localhost:8000/viewer.html`.

## Conventions

All rules for classifying frontages, counting bedrooms and bathrooms, generating IDs, and handling ambiguous cases are in `CLAUDE.md`. That file is the source of truth. If something isn't covered, raise it and we'll add it.

## Project history

Started May 2026 with three marketing-sheet pilot units. The intake workflow evolved through several iterations — marketing sheets, annotated archive plans, dimension-annotated bounding boxes — before settling on the current format: clean single-apartment PDFs with an embedded corner text box containing the ID and reference project. Published to GitHub Pages in May 2026.
