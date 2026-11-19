#!/usr/bin/env python3
"""Exports pixel-exact PNGs.

    python3 tools/export_png.py            # sprites only (needs Pillow)
    python3 tools/export_png.py --renders  # also PNG renders of every asset (needs Playwright + Chromium)

Sprites come straight from tools/sprites.py (the original Chromium dino pixels), drawn on
the original frame size, transparent background, nearest-neighbour scaled 1x/2x/4x.
  assets/png/sprites/night/     light ink (#e6e6e6) for dark backgrounds, the profile's look
  assets/png/sprites/original/  Chrome's own #535353 for light backgrounds
"""
import os
import sys

from PIL import Image

from sprites import SPRITES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "png")
FRAMES = {  # original frame sizes in the game's sprite sheet
    "trex_stand": (44, 47), "trex_run1": (44, 47), "trex_run2": (44, 47),
    "trex_duck1": (59, 47), "trex_duck2": (59, 47),
    "cactus_cs1": (17, 35), "cactus_cs2": (34, 35), "cactus_cs3": (51, 35),
    "cactus_cl1": (25, 50), "cactus_cl2": (50, 50), "cactus_cl3": (75, 50),
    "ptero1": (46, 40), "ptero2": (46, 40), "cloud": (46, 14), "restart": (36, 32),
    "star1": (9, 9), "moon1": (20, 40),
}
PALETTES = {"night": (230, 230, 230), "original": (83, 83, 83)}


def render(name, colour):
    x0, y0, rows = SPRITES[name]
    w, h = FRAMES.get(name, (x0 + len(rows[0]), y0 + len(rows)))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "#":
                px[x0 + c, y0 + r] = colour + (255,)
    return im


def sprites():
    for pal, colour in PALETTES.items():
        d = os.path.join(OUT, "sprites", pal)
        os.makedirs(d, exist_ok=True)
        names = [n for n in SPRITES if n in FRAMES] + [n for n in SPRITES if n.startswith("d") and n not in FRAMES]
        for name in names:
            im = render(name, colour)
            for k in (1, 2, 4):
                out = im if k == 1 else im.resize((im.width * k, im.height * k), Image.NEAREST)
                out.save(os.path.join(d, f"{name}@{k}x.png" if k > 1 else f"{name}.png"), optimize=True)
        # contact sheet of the T-Rex frames at 4x
        t = [render(n, colour) for n in ("trex_stand", "trex_run1", "trex_run2", "trex_duck1", "trex_duck2")]
        sheet = Image.new("RGBA", (sum(i.width for i in t) + 8 * 6, 47 + 16), (0, 0, 0, 0))
        x = 8
        for i in t:
            sheet.paste(i, (x, 8)); x += i.width + 8
        sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(d, "trex-frames-sheet@4x.png"))
    print("sprites ->", os.path.relpath(OUT))


def renders():
    from playwright.sync_api import sync_playwright
    assets = os.path.abspath(os.path.join(HERE, "..", "assets"))
    d = os.path.join(OUT, "renders")
    os.makedirs(d, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for f in sorted(os.listdir(assets)):
            if not f.endswith(".svg"):
                continue
            src = os.path.join(assets, "static", f)
            src = src if os.path.exists(src) else os.path.join(assets, f)
            pg = b.new_page(viewport={"width": 900, "height": 400}, device_scale_factor=2)
            pg.goto("file://" + src)
            el = pg.query_selector("svg")
            el.screenshot(path=os.path.join(d, f[:-4] + "@2x.png"))
            pg.close()
        b.close()
    print("renders ->", os.path.relpath(d))


if __name__ == "__main__":
    sprites()
    if "--renders" in sys.argv:
        renders()
