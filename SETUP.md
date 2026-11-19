# Dino Runner GitHub Profile

Powers the profile README for [@mohd-junaid-05](https://github.com/mohd-junaid-05).

## Structure

- `README.md` – the profile page. All meaningful content lives in Markdown, not only in artwork.
- `assets/dino-world.svg` – animated hero: cozy night-mode scene with a pixel T-Rex sitting comfortably by a burning, crackling campfire.
- `assets/checkpoint-panel.svg` – Checkpoint HUD panel with loading animation and running T-Rex.
- `assets/static/` – animation-free twins of the animated assets, served to visitors who prefer reduced motion.
- `tools/build_assets.py` – generates every SVG. **Edit this, not the SVGs.**
- `tools/sprites.py` – the pixel art (editable ASCII bitmaps).
- `tools/export_png.py` – exports PNGs into `assets/png/` (see below).
- `assets/png/sprites/` – every game sprite as a transparent, pixel-exact PNG at 1x/2x/4x, in `night` (profile look) and `original` (Chrome's #535353) palettes.
- `assets/png/renders/` – 2x PNG renders of each asset (static pose), for social cards or places that can't show SVG.

## Regenerating

    python3 tools/build_assets.py                 # SVGs (standard library only)
    python3 tools/export_png.py [--renders]       # PNGs (Pillow; --renders also needs Playwright + Chromium)

## Design system

- Monochrome: `#0b0b0b` background, `#e6e6e6` ink, greys for secondary text and decoration.
- One pixel scale: sprites are drawn at 2 units per sprite pixel using the original game's world coordinates (ground line y=131, T-Rex y=93, small cactus y=105, large cactus y=90, pterodactyl y=50/75/100).
- Text is outlined 5x7 pixel-font paths (upper and lower case; sentence case for labels, capitals only for the name and HI score), so it looks the same on every device and needs no web fonts. The game's own digit sprites are used for scores and numerals.
- Every panel shares one frame (stepped corners, title row, header rule) and sits on the game's ground line.
- All assets are 900 units wide so type scale is consistent. Smallest text is 3 units per font pixel (about 8px cap height on a phone).
- Motion is CSS only. Timing matches the original: run legs swap every 83.3 ms, pterodactyl wings every 166.7 ms, clouds drift at 20% of ground speed. World scroll is slowed to about 40% of the game's opening speed, and jumps are lengthened to match, so the hero stays readable.

## Reduced motion

`prefers-reduced-motion` inside an SVG shown via `<img>` is not reliable across browsers. The README therefore uses
`<picture><source media="(prefers-reduced-motion: reduce)">` to swap in the `assets/static/` twin. Keep that pattern for any new animated asset.

## GitHub rendering notes

- GitHub shows SVGs through `<img>`: no JavaScript, no external fonts or images, CSS animation works.
- The pixel grid is crisp at about 888px width; at other widths scaling is not an integer, so pixels vary slightly in size.
- The stats cards and skill icons come from external services and may be rate-limited or briefly unavailable.
- The hero shows light panels on GitHub's light theme as dark panels by design; there are no per-theme variants.

## Credits

Sprite pixels are extracted from the Chrome offline "Dino Runner" game
(Chromium, BSD-3-Clause, Copyright The Chromium Authors).
