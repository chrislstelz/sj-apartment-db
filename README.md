# Apartment Database

Internal reference library of apartment unit precedents developed across 20+ years of practice.

## Quick reference

- **Browse the library**: open `viewer.html` in a web browser
- **Edit the data**: open `database.xlsx` in Excel
- **After editing**: run `python scripts/export_json.py` to refresh the viewer
- **Add a new unit from a marked-up plan**: drop the PDF in `pdfs/`, then ask Claude

## What's in this folder

```
apartment-database/
├── CLAUDE.md          Office conventions — read this first
├── README.md          You are here
├── database.xlsx      The database (primary editable file)
├── database.json      Generated from database.xlsx for the viewer
├── viewer.html        Filterable browser-based viewer
├── pdfs/              Source archive plans, organised by project
├── thumbnails/        One thumbnail per unit, named by ID
└── scripts/
    └── export_json.py Regenerates database.json from database.xlsx
```

## First-time setup

You need Python 3 and the `openpyxl` library:

```bash
pip install openpyxl Pillow
```

Pillow is optional — it's only needed if Claude generates new thumbnails from PDFs.

## Daily use

**Office staff looking for a precedent**: open `viewer.html` in a browser. Filter by frontage type, bedroom count, width, depth. Click a card for full details. No editing happens here — it's read-only.

**Adding a new unit**: see CLAUDE.md for the markup convention. Once you've marked up a plan with a blue bounding box and dimensions, ask Claude (in Claude Code) to process it. The new row will be added to `database.xlsx`, a thumbnail will appear in `thumbnails/`, and you'll need to run the export script to refresh the viewer.

**Editing an existing unit**: open `database.xlsx`, edit the row, re-run the export script. Thumbnails are linked by the ID in column B — if you change an ID, also rename the corresponding `thumbnails/X.png` file.

## Conventions

All the rules for how the database is built — how to classify frontages, count bedrooms, count bathrooms, generate IDs, handle ambiguous cases — are in `CLAUDE.md`. That file is the source of truth. Don't make conventions up; if something isn't covered, raise it and we'll add it.

## Project history

Built in chat with Claude over several iterations, starting May 2026 with three marketing-sheet pilots. The conventions evolved as we processed archival plans of increasing complexity. Migrated to a local project at 21 units, ready for steady expansion toward full coverage of the practice's typology.
