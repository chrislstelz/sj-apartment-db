"""Convert a source PDF floor plan into a clean thumbnail PNG.

Run from the project root:
    python3 scripts/process_pdf.py SING-2B-001

Reads:  floor-plans/{ID}.pdf
Writes: thumbnails/{ID}.png  (1000×1000px square, white background, black lines)

Dependencies: pip install pymupdf pillow
"""
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Missing PyMuPDF. Install with: pip install pymupdf")

try:
    from PIL import Image, ImageChops, ImageOps
except ImportError:
    sys.exit("Missing Pillow. Install with: pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
FLOOR_PLANS = ROOT / "floor-plans"
THUMBS = ROOT / "thumbnails"
TARGET_SIZE = 1000  # output is a square canvas, 1000×1000px
MARGIN_PX = 60      # whitespace margin around plan content before padding to square
RENDER_SCALE = 8    # render at 8× for high-fidelity source before downscale
# 3-zone tone mapping (see THUMBNAIL REFERENCE STYLE GUIDE/STYLE_GUIDE.md):
#   0–DARK_THRESHOLD    → black  (wall lines, strong outlines)
#   DARK–LIGHT_THRESHOLD → light grey (furniture, joinery, floor patterns)
#   LIGHT_THRESHOLD+    → white  (background, coloured fills)
DARK_THRESHOLD = 80    # below this → black
LIGHT_THRESHOLD = 200  # above this → white
MID_GREY = 210         # value assigned to the middle zone


def process(unit_id: str) -> None:
    src = FLOOR_PLANS / f"{unit_id}.pdf"
    if not src.exists():
        sys.exit(f"Not found: {src}")

    THUMBS.mkdir(exist_ok=True)
    dst = THUMBS / f"{unit_id}.png"

    doc = fitz.open(src)
    page = doc[0]

    # Collect text block bounding boxes before rendering (PDF coordinate space)
    text_blocks = page.get_text("blocks")

    # Collect PDF-coordinate regions to erase in pixel space after rendering.
    # Two classes of artifact:
    #   (a) Drawings completely outside the apartment wall boundary — annotation
    #       frames, title blocks, reference label boxes.  Wall boundary is derived
    #       from thick-stroke elements (stroke width ≥ 0.5 pt = actual walls).
    #   (b) Crosshair × marks — small diagonal line segments (bbox ≤ 6 pt) that are
    #       within 20 pt of a wall corner.  Furniture diagonals are larger and interior.
    CROSSHAIR_MAX_SIZE = 6   # PDF points; the × marks are ~5.7 pt
    CORNER_DISTANCE = 20     # pt; crosshairs sit at the corner of the wall frame
    OUTSIDE_MARGIN = 5       # element must be this far fully outside walls
    ERASE_PAD = 4            # extra PDF-point padding when erasing
    erase_regions = []       # (x0, y0, x1, y1) in PDF points, converted to px later
    drawings = page.get_drawings()
    thick = [d for d in drawings if (d.get("width") or 0) >= 0.5 and d.get("rect")]
    wall_corners = []
    if thick:
        wx0 = min(d["rect"].x0 for d in thick)
        wy0 = min(d["rect"].y0 for d in thick)
        wx1 = max(d["rect"].x1 for d in thick)
        wy1 = max(d["rect"].y1 for d in thick)
        wall_corners = [(wx0, wy0), (wx1, wy0), (wx0, wy1), (wx1, wy1)]
        for d in drawings:
            r = d.get("rect")
            if not r:
                continue
            if (r.x1 < wx0 - OUTSIDE_MARGIN or r.x0 > wx1 + OUTSIDE_MARGIN or
                    r.y1 < wy0 - OUTSIDE_MARGIN or r.y0 > wy1 + OUTSIDE_MARGIN):
                erase_regions.append((r.x0 - ERASE_PAD, r.y0 - ERASE_PAD,
                                      r.x1 + ERASE_PAD, r.y1 + ERASE_PAD))
    for d in drawings:
        r = d.get("rect")
        if not r or r.width > CROSSHAIR_MAX_SIZE or r.height > CROSSHAIR_MAX_SIZE:
            continue
        # Must be near a wall face (within CORNER_DISTANCE of the left, right, top, or
        # bottom wall boundary).  Crosshairs appear along all four wall faces at grid
        # intersections; furniture diagonals are in the interior, away from all faces.
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if not wall_corners:
            continue
        wx0_, wy0_ = wall_corners[0]
        wx1_, wy1_ = wall_corners[3]
        near_face = (abs(cx - wx0_) < CORNER_DISTANCE or
                     abs(cx - wx1_) < CORNER_DISTANCE or
                     abs(cy - wy0_) < CORNER_DISTANCE or
                     abs(cy - wy1_) < CORNER_DISTANCE)
        if not near_face:
            continue
        for item in d.get("items", []):
            if item[0] == "l":
                p1, p2 = item[1], item[2]
                if abs(p2.x - p1.x) > 1.0 and abs(p2.y - p1.y) > 1.0:
                    erase_regions.append((r.x0 - ERASE_PAD, r.y0 - ERASE_PAD,
                                          r.x1 + ERASE_PAD, r.y1 + ERASE_PAD))
                    break

    mat = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    doc.close()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img = ImageOps.grayscale(img)

    # 3-zone tone mapping: dark → black, mid → light grey, light → white
    img = img.point(lambda p: 0 if p < DARK_THRESHOLD else (255 if p >= LIGHT_THRESHOLD else MID_GREY))
    img = img.convert("RGB")

    # White out annotation artifacts and text regions identified before rendering
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    s = RENDER_SCALE
    for (x0, y0, x1, y1) in erase_regions:
        draw.rectangle([int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s)],
                       fill=(255, 255, 255))
    for block in text_blocks:
        x0, y0, x1, y1 = block[:4]
        draw.rectangle([int(x0 * s) - 2, int(y0 * s) - 2,
                        int(x1 * s) + 2, int(y1 * s) + 2], fill=(255, 255, 255))

    # Crop to content bounding box
    white = Image.new("RGB", img.size, (255, 255, 255))
    diff = ImageChops.difference(img, white)
    bbox = diff.getbbox()
    if bbox:
        x0 = max(0, bbox[0] - MARGIN_PX)
        y0 = max(0, bbox[1] - MARGIN_PX)
        x1 = min(img.width, bbox[2] + MARGIN_PX)
        y1 = min(img.height, bbox[3] + MARGIN_PX)
        img = img.crop((x0, y0, x1, y1))

    # Pad to square canvas then resize to TARGET_SIZE × TARGET_SIZE
    w, h = img.size
    side = max(w, h)
    square = Image.new("RGB", (side, side), (255, 255, 255))
    square.paste(img, ((side - w) // 2, (side - h) // 2))
    square = square.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

    square.save(dst)
    print(f"Saved {dst}  ({TARGET_SIZE}×{TARGET_SIZE}px)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/process_pdf.py {UNIT-ID}")
    process(sys.argv[1])
