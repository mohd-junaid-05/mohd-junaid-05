#!/usr/bin/env python3
"""Builds every SVG in ../assets from one shared design system.

    python3 tools/build_assets.py

Design rules (see SETUP.md):
  * Monochrome, dark. One "ink" colour for sprites and primary text.
  * Sprites are the real Dino Runner pixels (tools/sprites.py) drawn at 2 units
    per sprite pixel, using the game's own world coordinates (ground line y=131,
    T-Rex at y=93, small cactus y=105, large cactus y=90, pterodactyl y=50/75/100).
  * All text is outlined pixel-font paths (5x7), so it renders identically on
    every OS and inside GitHub's <img> sandbox, where web fonts are unavailable.
  * All motion is CSS and is switched off by prefers-reduced-motion. Without
    animation each scene falls back to a deliberate static composition.
  * All assets are 900 units wide so the type scale is identical everywhere.
"""
import math
import os

from sprites import HORIZON, SPRITES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
W = 900

BG, INK, SOFT, DIM, EDGE, CELL, RULE = (
    "#0b0b0b", "#e6e6e6", "#9c9c9c", "#5b5b5b", "#444444", "#121212", "#2a2a2a")

# --------------------------------------------------------------------------- #
# Pixel helpers
# --------------------------------------------------------------------------- #


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if float(v).is_integer() else ("%g" % v)


def pix(name):
    x0, y0, rows = SPRITES[name]
    return {(x0 + c, y0 + r) for r, row in enumerate(rows)
            for c, ch in enumerate(row) if ch == "#"}


def bbox(p):
    xs = [x for x, _ in p]
    ys = [y for _, y in p]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def rects(p):
    """Merge a pixel set into few rectangles (horizontal runs, stacked vertically)."""
    rows = {}
    for x, y in p:
        rows.setdefault(y, []).append(x)
    runs = {}
    for y, xs in rows.items():
        xs.sort()
        s = prev = xs[0]
        out = []
        for x in xs[1:]:
            if x != prev + 1:
                out.append((s, prev - s + 1))
                s = x
            prev = x
        out.append((s, prev - s + 1))
        runs[y] = out
    done, opened = [], {}
    for y in sorted(runs):
        cur = set(runs[y])
        for key in list(opened):
            y0, h = opened[key]
            if key in cur and y0 + h == y:
                opened[key][1] += 1
                cur.discard(key)
            else:
                done.append((key[0], y0, key[1], h))
                del opened[key]
        for key in cur:
            opened[key] = [y, 1]
    for key, (y0, h) in opened.items():
        done.append((key[0], y0, key[1], h))
    return done


def path_d(rs):
    rs = sorted(rs, key=lambda r: (r[1], r[0]))
    px = py = 0
    out = []
    for x, y, w, h in rs:
        out.append(f"m{x - px} {y - py}h{w}v{h}h-{w}z")
        px, py = x, y
    return "".join(out)


def sprite_path(pid, p, extra=""):
    return f'<path id="{pid}" d="{path_d(rects(p))}"{extra}/>'


# --------------------------------------------------------------------------- #
# 5x7 pixel font (uppercase only, matches the blocky look of the game's digits)
# --------------------------------------------------------------------------- #

_F = {
    "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "B": "####./#...#/#...#/####./#...#/#...#/####.",
    "C": ".###./#...#/#..../#..../#..../#...#/.###.",
    "D": "####./#...#/#...#/#...#/#...#/#...#/####.",
    "E": "#####/#..../#..../####./#..../#..../#####",
    "F": "#####/#..../#..../####./#..../#..../#....",
    "G": ".###./#...#/#..../#.###/#...#/#...#/.###.",
    "H": "#...#/#...#/#...#/#####/#...#/#...#/#...#",
    "I": ".###./..#../..#../..#../..#../..#../.###.",
    "J": "..###/...#./...#./...#./...#./#..#./.##..",
    "K": "#...#/#..#./#.#../##.../#.#../#..#./#...#",
    "L": "#..../#..../#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#",
    "N": "#...#/##..#/#.#.#/#..##/#...#/#...#/#...#",
    "O": ".###./#...#/#...#/#...#/#...#/#...#/.###.",
    "P": "####./#...#/#...#/####./#..../#..../#....",
    "Q": ".###./#...#/#...#/#...#/#.#.#/#..#./.##.#",
    "R": "####./#...#/#...#/####./#.#../#..#./#...#",
    "S": ".####/#..../#..../.###./....#/....#/####.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/#...#/#...#/.###.",
    "V": "#...#/#...#/#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#",
    "X": "#...#/#...#/.#.#./..#../.#.#./#...#/#...#",
    "Y": "#...#/#...#/.#.#./..#../..#../..#../..#..",
    "Z": "#####/....#/...#./..#../.#.../#..../#####",
    "0": ".###./#...#/#..##/#.#.#/##..#/#...#/.###.",
    "1": "..#../.##../..#../..#../..#../..#../.###.",
    "2": ".###./#...#/....#/...#./..#../.#.../#####",
    "3": "####./....#/....#/.###./....#/....#/####.",
    "4": "...#./..##./.#.#./#..#./#####/...#./...#.",
    "5": "#####/#..../####./....#/....#/#...#/.###.",
    "6": ".###./#..../#..../####./#...#/#...#/.###.",
    "7": "#####/....#/...#./..#../.#.../.#.../.#...",
    "8": ".###./#...#/#...#/.###./#...#/#...#/.###.",
    "9": ".###./#...#/#...#/.####/....#/....#/.###.",
    "a": "...../...../.###./....#/.####/#...#/.####",
    "b": "#..../#..../####./#...#/#...#/#...#/####.",
    "c": "...../...../.###./#..../#..../#...#/.###.",
    "d": "....#/....#/.####/#...#/#...#/#...#/.####",
    "e": "...../...../.###./#...#/#####/#..../.###.",
    "f": "..##./.#.../####./.#.../.#.../.#.../.#...",
    "g": "...../...../.####/#...#/#...#/.####/....#/#...#/.###.",
    "h": "#..../#..../####./#...#/#...#/#...#/#...#",
    "i": "..#../...../.##../..#../..#../..#../.###.",
    "j": "...#./...../..##./...#./...#./...#./...#./#..#./.##..",
    "k": "#..../#..../#..#./#.#../##.../#.#../#..#.",
    "l": ".##../..#../..#../..#../..#../..#../.###.",
    "m": "...../...../##.#./#.#.#/#.#.#/#...#/#...#",
    "n": "...../...../####./#...#/#...#/#...#/#...#",
    "o": "...../...../.###./#...#/#...#/#...#/.###.",
    "p": "...../...../####./#...#/#...#/####./#..../#..../#....",
    "q": "...../...../.####/#...#/#...#/.####/....#/....#/....#",
    "r": "...../...../#.##./##..#/#..../#..../#....",
    "s": "...../...../.####/#..../.###./....#/####.",
    "t": ".#.../.#.../####./.#.../.#.../.#..#/..##.",
    "u": "...../...../#...#/#...#/#...#/#...#/.####",
    "v": "...../...../#...#/#...#/#...#/.#.#./..#..",
    "w": "...../...../#...#/#...#/#.#.#/##.##/#...#",
    "x": "...../...../#...#/.#.#./..#../.#.#./#...#",
    "y": "...../...../#...#/#...#/#...#/.####/....#/#...#/.###.",
    "z": "...../...../#####/...#./..#../.#.../#####",
    " ": ".../.../.../.../.../.../...",
    ".": "./././././#/#",
    ",": "../../../../../.#/#.",
    ":": "././#/./#/./.",
    "-": "..../..../..../####/..../..../....",
    "/": "....#/....#/...#./..#../.#.../#..../#....",
    "+": "...../..#../..#../#####/..#../..#../.....",
    "(": "..#/.#./#../#../#../.#./..#",
    ")": "#../.#./..#/..#/..#/.#./#..",
    "{": "..#/.#./.#./#../.#./.#./..#",
    "}": "#../.#./.#./..#/.#./.#./#..",
    "<": "...#/..#./.#../#.../.#../..#./...#",
    ">": "#.../.#../..#./...#/..#./.#../#...",
    "_": "...../...../...../...../...../...../#####",
    "!": "#/#/#/#/#/./#",
    "'": "#/#/././././.",
    '"': "#.#/#.#/././././.",
    "&": ".##./#..#/.##./.#.#/#..#/#..#/.##.#",
    ";": "././#/././.#/#.",
    "—": "..../..../..../######/..../..../....",
}
FONT = {k: v.split("/") for k, v in _F.items()}


def text_pixels(s):
    p, x = set(), 0
    for ch in s:
        if ch not in FONT:
            if ch == "’":
                ch = "'"
            elif ch in "“”":
                ch = '"'
            elif ch in "–—":
                ch = "-"
            else:
                ch = " "
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == "#":
                    p.add((x + c, r))
        x += len(g[0]) + 1
    return p, x - 1


def text_w(s, px):
    return text_pixels(s)[1] * px


def text(s, x, y, px, fill=INK, anchor="s", extra=""):
    """Pixel text. (x, y) is the top-left of the cap height; anchor s/m/e."""
    p, cols = text_pixels(s)
    wd = cols * px
    tx = x if anchor == "s" else (x - wd / 2 if anchor == "m" else x - wd)
    return (f'<path transform="translate({fmt(tx)} {fmt(y)}) scale({fmt(px)})" '
            f'fill="{fill}"{extra} d="{path_d(rects(p))}"/>')


# --------------------------------------------------------------------------- #
# Shared pieces
# --------------------------------------------------------------------------- #

REDUCE = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(h, title, desc, css, defs, body, w=W):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-labelledby="t d" shape-rendering="crispEdges">'
            f'<title id="t">{title}</title><desc id="d">{desc}</desc>'
            f"<style>{css}{REDUCE}</style><defs>{defs}</defs>{body}</svg>\n")


def notch(x, y, w, h, n=4):
    """Rectangle outline with one-pixel stepped corners (the game's rounded look)."""
    return (f"M{x + n} {y}h{w - 2 * n}v{n}h{n}v{h - 2 * n}h-{n}v{n}h-{w - 2 * n}"
            f"v-{n}h-{n}v-{h - 2 * n}h{n}z")


def box(x, y, w, h, fill=CELL, stroke=RULE, cls="", n=4, style=""):
    c = (f' class="{cls}"' if cls else "") + (f' style="{style}"' if style else "")
    return (f'<path{c} d="{notch(x, y, w, h, n)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="2"/>')


def digit_defs(chars="0123456789HI"):
    out = []
    for ch in chars:
        name = "d" + ch
        out.append(sprite_path("n" + ch, pix(name)))
    return "".join(out)


def digits(s, x, y, scale=2, fill=INK):
    """Game-font score digits (10x13 sprites, 11px advance). Needs digit_defs()."""
    out = [f'<g transform="translate({fmt(x)} {fmt(y)}) scale({scale})" fill="{fill}">']
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        out.append(f'<use href="#n{ch}" x="{i * 11}"/>')
    out.append("</g>")
    return "".join(out)


def horizon_bumps(seg, x0, x1):
    """Ground bump pixels of a horizon segment as a pixel set (y=0 is the line)."""
    p = set()
    for x, y, w in HORIZON[seg]:
        for i in range(w):
            if x0 <= x + i < x1:
                p.add((x + i - x0, y))
    return p


def chrome(h, title, tag):
    """Common HUD frame: stepped border, title row, header rule."""
    return [
        f'<path d="{notch(1, 1, W - 2, h - 2, 6)}" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>',
        text(title, 24, 16, 3, INK),
        text(tag, W - 24, 16, 3, SOFT, "e"),
        f'<rect x="12" y="50" width="{W - 24}" height="2" fill="{RULE}"/>',
    ]


def ground_footer(y, scroll=False):
    """The game's ground line with real bump pixels, used as every panel's floor."""
    line = f'<rect x="12" y="{y}" width="{W - 24}" height="2" fill="#6e6e6e"/>'
    d = path_d(rects(horizon_bumps(0, 6, 6 + (W - 24) // 2)))
    return line + f'<path transform="translate(12 {y}) scale(2)" fill="#505050" d="{d}"/>'


# --------------------------------------------------------------------------- #
# World engine (hero + track): game coordinates, scaled x2
# --------------------------------------------------------------------------- #

LINE_Y = 131      # ground line in game coordinates
DINO_Y = 93       # T-Rex top in game coordinates
JUMP_TIME = 1.0   # seconds airborne (slowed from the game's ~0.55s with the scroll speed)
EPS = 0.001


def kf(name, pts):
    """pts: [(seconds, 'css declaration')], period is read from kf.P."""
    out = [f"@keyframes {name}{{"]
    merged = []
    for t, decl in pts:
        p = fmt(100 * t / kf.P)
        if merged and merged[-1][1] == decl and merged[-1][2] == p:
            continue
        merged.append([p, decl, p])
    for p, decl, _ in merged:
        out.append(f"{p}%{{{decl}}}")
    out.append("}")
    return "".join(out)


def window_kf(name, wins, inside, outside):
    pts = [(0, outside)]
    for a, b in wins:
        pts += [(a - EPS, outside), (a, inside), (b, inside), (b + EPS, outside)]
    pts.append((kf.P, outside))
    return kf(name, pts)


def build_world(cfg):
    """Returns dict(defs, sky, front, css). cfg describes one scene."""
    width, v, P = cfg["w"], cfg["v"], cfg["P"]
    kf.P = P
    oy = cfg["line_y"] - 2 * LINE_Y
    xw = width // 2                 # visible world width in game pixels
    xs = xw + 14                    # spawn x (just off the right edge)
    dino_x = cfg.get("dino_x", 40)
    css = [".fb,.db,.pb,.pj,.pd{opacity:0}",
           ".fa{animation:fa .1667s steps(1,end) infinite}.fb{animation:fb .1667s steps(1,end) infinite}"
           "@keyframes fa{0%{opacity:1}50%{opacity:0}}@keyframes fb{0%{opacity:0}50%{opacity:1}}",
           ".da{animation:fa .25s steps(1,end) infinite}.db{animation:fb .25s steps(1,end) infinite}",
           ".pa{animation:fa .3333s steps(1,end) infinite}.pb{animation:fb .3333s steps(1,end) infinite}"]
    defs = []

    # --- sprite defs -------------------------------------------------------
    S, R1, R2 = pix("trex_stand"), pix("trex_run1"), pix("trex_run2")
    body = S & R1 & R2
    defs += [sprite_path("tb", body), sprite_path("ts", S - body),
             sprite_path("t1", R1 - body), sprite_path("t2", R2 - body)]
    D1, D2 = pix("trex_duck1"), pix("trex_duck2")
    dbody = D1 & D2
    defs += [sprite_path("db0", dbody), sprite_path("da1", D1 - dbody), sprite_path("da2", D2 - dbody)]
    dl, dt, dr, dbm = bbox(S | R1 | R2)
    ddx, dtop = dl, dt
    d_xl, d_xr = dino_x + dl, dino_x + dr          # dino ink extents (game x)
    feet = DINO_Y + dbm                              # dino feet bottom (game y)
    used = set()
    for e in cfg["events"]:
        if e["kind"] == "cactus":
            used.add(e["sprite"])
    for n in sorted(used):
        defs.append(sprite_path(n, pix("cactus_" + n)))
    if any(e["kind"] == "ptero" for e in cfg["events"]):
        defs += [sprite_path("p1", pix("ptero1")), sprite_path("p2", pix("ptero2"))]
    pt_l, _, pt_r, _ = bbox(pix("ptero1") | pix("ptero2"))
    defs.append(sprite_path("cloud", pix("cloud")))
    if cfg.get("moon"):
        defs.append(sprite_path("moon", pix("moon1")))
        defs.append(sprite_path("star", pix("star1")))

    # --- obstacles + choreography ----------------------------------------------
    obst, jumps, ducks = [], [], []
    for i, e in enumerate(cfg["events"]):
        vo = e.get("speed", v)
        if e["kind"] == "cactus":
            p = pix("cactus_" + e["sprite"])
            il, it, ir, ib = bbox(p)
            wd = ir - il
            top = e["y"] + it
            if e.get("act") == "jump":
                lead = vo * JUMP_TIME / 2 - (wd + (d_xr - d_xl)) / 2
                tj = e["spawn"] + (xs + il - d_xr - lead) / vo
                apex = (feet - top) + cfg["clear"]
                jumps.append((tj, apex))
            node = f'<use href="#{e["sprite"]}"/>'
            oy_ = e["y"]
            end = -ir - 8
        else:
            il, ir = pt_l, pt_r
            wd = ir - il
            if e.get("act") == "duck":
                t1 = e["spawn"] + (xs + il - d_xr - 26) / vo
                t2 = e["spawn"] + (xs + il - (d_xl - 10 - wd)) / vo
                ducks.append((t1, t2))
            node = '<use href="#p1" class="pa"/><use href="#p2" class="pb"/>'
            oy_ = e["y"]
            end = -ir - 8
        dur = (xs - end) / vo
        base = e["base"]
        a, b = e["spawn"], e["spawn"] + dur
        assert b < P, f"obstacle {i} outlives period ({b:.2f}s >= {P}s)"
        pts = [(0, f"transform:translateX({fmt(xs - base)}px)"),
               (a, f"transform:translateX({fmt(xs - base)}px)"),
               (b, f"transform:translateX({fmt(end - base)}px)"),
               (P, f"transform:translateX({fmt(end - base)}px)")]
        css.append(kf(f"o{i}", pts))
        css.append(f".o{i}{{animation:o{i} {fmt(P)}s linear infinite}}")
        obst.append(f'<g transform="translate({base} {oy_})"><g class="o{i}">{node}</g></g>')

    jumps.sort()
    ducks.sort()
    # dino pose windows
    jw = [(t, t + JUMP_TIME) for t, _ in jumps]
    css.append(window_kf("pr", sorted(jw + ducks), "opacity:0", "opacity:1"))
    css.append(window_kf("pj", jw, "opacity:1", "opacity:0"))
    css.append(window_kf("pd", ducks, "opacity:1", "opacity:0"))
    css.append(f".pose-r{{animation:pr {fmt(P)}s linear infinite}}"
               f".pose-j{{animation:pj {fmt(P)}s linear infinite}}"
               f".pose-d{{animation:pd {fmt(P)}s linear infinite}}")
    ypts = [(0, "transform:translateY(0)")]
    for tj, apex in jumps:
        for k in range(0, 17):
            u = k / 16
            ypts.append((tj + JUMP_TIME * u, f"transform:translateY({fmt(-4 * apex * u * (1 - u))}px)"))
    ypts.append((P, "transform:translateY(0)"))
    css.append(kf("jy", ypts))
    css.append(f".jy{{animation:jy {fmt(P)}s linear infinite}}")

    # ground scroll (period = one 1200px double segment)
    css.append("@keyframes gs{to{transform:translateX(-1200px)}}")
    css.append(f".gs{{animation:gs {fmt(1200 / v)}s linear infinite}}")

    # clouds drift at 20% of ground speed (BG_CLOUD_SPEED)
    vc, cw = 0.2 * v, 46
    total = xw + cw
    clouds = []
    for i, (cx, cy) in enumerate(cfg["clouds"]):
        a = (cx + cw) / total * 100
        css.append(f"@keyframes c{i}{{0%{{transform:translateX(0)}}{fmt(a)}%{{transform:translateX({-(cx + cw)}px)}}"
                   f"{fmt(a + 0.01)}%{{transform:translateX({xw - cx}px)}}100%{{transform:translateX(0)}}}}")
        css.append(f".c{i}{{animation:c{i} {fmt(total / vc)}s linear infinite}}")
        clouds.append(f'<g transform="translate({cx} {cy})"><use href="#cloud" class="c{i}"/></g>')

    # --- layers ---------------------------------------------------------------
    sky = []
    if cfg.get("moon"):
        mx, my = cfg["moon"]
        sky.append(f'<use href="#moon" x="{mx}" y="{my}" fill="#6f6f6f"/>')
        for sx, sy in cfg["stars"]:
            sky.append(f'<use href="#star" x="{sx}" y="{sy}" fill="#5f5f5f"/>')
    sky.append(f'<g fill="{DIM}">{"".join(clouds)}</g>')

    bump = []
    for i, seg in enumerate((0, 1, 0)):
        d = path_d(rects(horizon_bumps(seg, 0, 600)))
        bump.append(f'<path transform="translate({600 * i} {LINE_Y})" d="{d}"/>')
    ground = (f'<rect x="0" y="{LINE_Y}" width="{xw}" height="1" fill="#b4b4b4"/>'
              f'<g fill="#8a8a8a"><g class="gs">{"".join(bump)}</g></g>')
    dino = (f'<g transform="translate({dino_x} {DINO_Y})" fill="{INK}">'
            '<g class="pose-r"><use href="#tb"/><use href="#t1" class="fa"/><use href="#t2" class="fb"/></g>'
            '<g class="pose-j pj"><g class="jy"><use href="#tb"/><use href="#ts"/></g></g>'
            '<g class="pose-d pd"><use href="#db0"/><use href="#da1" class="da"/><use href="#da2" class="db"/></g>'
            "</g>")
    front = (f'<g fill="#cfcfcf">{"".join(obst)}</g>')
    wrap = f'<g transform="translate(0 {oy}) scale(2)">'
    return {
        "defs": "".join(defs),
        "sky": wrap + "".join(sky) + "</g>",
        "front": wrap + ground + front + dino + "</g>",
        "css": "".join(css),
    }


SIT_ROWS = [
    "                 ###########. ",
    "               ####.######### ",
    "               ####.######### ",
    "               ############## ",
    "               ############## ",
    "               ############## ",
    "               #############. ",
    "               #######....... ",
    "               #######....... ",
    "               ############.. ",
    "  #............############.. ",
    "  #...........#######........ ",
    "  #..........########........ ",
    "  ##.......#############..... ",
    "  ###.....###########.##..... ",
    "  ####...############.##..... ",
    "  ###################........ ",
    "  ###################........ ",
    "  ###################........ ",
    "   ##################........ ",
    "    ################......... ",
    "     ##############.......... ",
    "###   ############   #  ##### ",
]

SAGUARO_ROWS = [
    "        ####          ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######   ####  ",
    "       ######  ###### ",
    "       ######  ###### ",
    "       ######  ###### ",
    " ####  ######  ###### ",
    "###### ######  ###### ",
    "###### ######  ###### ",
    "###### ######  ###### ",
    "###### ######  ###### ",
    "###### ############## ",
    "###### #############  ",
    "###### ######         ",
    "#############         ",
    " ############         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
    "       ######         ",
]

CAMPFIRE_LOGS = [
    "   ######      ######   ",
    "  ########    ########  ",
    " ###################### ",
    "########################",
    " ###################### ",
    "   ####          ####   ",
]

FLAME_1 = [
    "           ##           ",
    "          ####          ",
    "          ####   ##     ",
    "         ###### ####    ",
    "         ###########    ",
    "        #############   ",
    "        #############   ",
    "       ###############  ",
    "       ###############  ",
    "      ################# ",
    "      ################# ",
    "     ################## ",
    "     ################## ",
    "    ####################",
    "    ####################",
    "   ######################",
]

FLAME_2 = [
    "           ####         ",
    "          ######        ",
    "    ##   ########       ",
    "   ####  ########       ",
    "   ##############       ",
    "   ##############       ",
    "  ################      ",
    "  ################      ",
    " ##################     ",
    " ##################     ",
    " ##################     ",
    " ###################    ",
    " ###################    ",
    "####################    ",
    "####################    ",
    "######################  ",
]

FLAME_3 = [
    "         ######         ",
    "        ########        ",
    "       ##########       ",
    "       ##########       ",
    "      ############      ",
    "      ############      ",
    "     ##############     ",
    "     ##############     ",
    "     ##############     ",
    "    ################    ",
    "    ################    ",
    "   ##################   ",
    "   ##################   ",
    "  ####################  ",
    "  ####################  ",
    " ###################### ",
]

CORE_1 = [
    "                        ",
    "                        ",
    "                        ",
    "          ####          ",
    "         ######         ",
    "         ######         ",
    "        ########        ",
    "        ########        ",
    "       ##########       ",
    "       ##########       ",
    "       ##########       ",
    "      ############      ",
    "      ############      ",
    "     ##############     ",
    "     ##############     ",
    "    ################    ",
]

CORE_2 = [
    "                        ",
    "                        ",
    "                        ",
    "           ####         ",
    "          ######        ",
    "          ######        ",
    "         ########       ",
    "         ########       ",
    "        ##########      ",
    "        ##########      ",
    "        ##########      ",
    "       ############     ",
    "       ############     ",
    "      ##############    ",
    "      ##############    ",
    "     ################   ",
]

CORE_3 = [
    "                        ",
    "                        ",
    "                        ",
    "         ####           ",
    "        ######          ",
    "        ######          ",
    "       ########         ",
    "       ########         ",
    "      ##########        ",
    "      ##########        ",
    "      ##########        ",
    "     ############       ",
    "     ############       ",
    "    ##############      ",
    "    ##############      ",
    "   ################     ",
]


def hero():
    H = 330
    line_y = 282
    oy = line_y - 2 * LINE_Y
    xw = W // 2

    p_sit = {(c, r) for r, row in enumerate(SIT_ROWS) for c, ch in enumerate(row) if ch == '#'}
    p_saguaro = {(c, r) for r, row in enumerate(SAGUARO_ROWS) for c, ch in enumerate(row) if ch == '#'}
    p_logs = {(c, r) for r, row in enumerate(CAMPFIRE_LOGS) for c, ch in enumerate(row) if ch == '#'}
    p_f1 = {(c, r) for r, row in enumerate(FLAME_1) for c, ch in enumerate(row) if ch == '#'}
    p_f2 = {(c, r) for r, row in enumerate(FLAME_2) for c, ch in enumerate(row) if ch == '#'}
    p_f3 = {(c, r) for r, row in enumerate(FLAME_3) for c, ch in enumerate(row) if ch == '#'}
    p_c1 = {(c, r) for r, row in enumerate(CORE_1) for c, ch in enumerate(row) if ch == '#'}
    p_c2 = {(c, r) for r, row in enumerate(CORE_2) for c, ch in enumerate(row) if ch == '#'}
    p_c3 = {(c, r) for r, row in enumerate(CORE_3) for c, ch in enumerate(row) if ch == '#'}

    defs = [
        sprite_path("dino_sit", p_sit),
        sprite_path("saguaro", p_saguaro),
        sprite_path("cactus_small", pix("cactus_cs1")),
        sprite_path("fire_logs", p_logs),
        sprite_path("fl1", p_f1),
        sprite_path("fl2", p_f2),
        sprite_path("fl3", p_f3),
        sprite_path("fc1", p_c1),
        sprite_path("fc2", p_c2),
        sprite_path("fc3", p_c3),
        sprite_path("ptero1", pix("ptero1")),
        sprite_path("ptero2", pix("ptero2")),
        sprite_path("cloud", pix("cloud")),
        sprite_path("moon", pix("moon1")),
        sprite_path("star", pix("star1")),
    ]

    css = [
        ".fl1{animation:fl1 .42s linear infinite}",
        ".fl2{opacity:0;animation:fl2 .42s linear infinite}",
        ".fl3{opacity:0;animation:fl3 .42s linear infinite}",
        "@keyframes fl1{0%,33.2%{opacity:1}33.3%,100%{opacity:0}}",
        "@keyframes fl2{0%,33.2%{opacity:0}33.3%,66.5%{opacity:1}66.6%,100%{opacity:0}}",
        "@keyframes fl3{0%,66.5%{opacity:0}66.6%,100%{opacity:1}}",
        "@keyframes sp1{0%{transform:translate(0,0);opacity:1}100%{transform:translate(-3px,-24px);opacity:0}}",
        "@keyframes sp2{0%{transform:translate(0,0);opacity:1}100%{transform:translate(4px,-28px);opacity:0}}",
        "@keyframes sp3{0%{transform:translate(0,0);opacity:1}100%{transform:translate(1px,-32px);opacity:0}}",
        "@keyframes sp4{0%{transform:translate(0,0);opacity:1}100%{transform:translate(-2px,-20px);opacity:0}}",
        ".sp1{animation:sp1 1.4s ease-out infinite}",
        ".sp2{animation:sp2 1.8s ease-out infinite .4s}",
        ".sp3{animation:sp3 2.2s ease-out infinite .9s}",
        ".sp4{animation:sp4 1.6s ease-out infinite 1.3s}",
        "@keyframes dblink{0%,93%,97%,100%{opacity:0}94%,96%{opacity:1}}",
        ".dblink{opacity:0;animation:dblink 3.8s steps(1,end) infinite}",
        "@keyframes c0{0%,100%{transform:translateX(0)}50%{transform:translateX(-10px)}}",
        ".c0{animation:c0 14s ease-in-out infinite}",
        "@keyframes c1{0%,100%{transform:translateX(0)}50%{transform:translateX(8px)}}",
        ".c1{animation:c1 18s ease-in-out infinite}",
        "@keyframes pterofly{0%{transform:translateX(-50px);opacity:0}1.5%{opacity:1}56%{transform:translateX(460px);opacity:1}56.1%{opacity:0;transform:translateX(470px)}100%{opacity:0;transform:translateX(-50px)}}",
        ".pterofly{transform:translateX(360px);animation:pterofly 26s linear infinite}",
        "@keyframes pfa{0%,49.9%{opacity:1}50%,100%{opacity:0}}",
        "@keyframes pfb{0%,49.9%{opacity:0}50%,100%{opacity:1}}",
        ".pfa{animation:pfa .44s linear infinite}",
        ".pfb{opacity:0;animation:pfb .44s linear infinite}",
    ]

    # Night sky: stars in corners (completely clear of text, dino, and fire) + moon + gentle hovering clouds + slow pterodactyl
    sky = [
        # Top-left corner stars (well above MOHD JUNAID which starts at y=120)
        '<use href="#star" x="18" y="14" fill="#5f5f5f"/>',
        '<use href="#star" x="42" y="26" fill="#5f5f5f"/>',
        '<use href="#star" x="72" y="10" fill="#5f5f5f"/>',
        '<use href="#star" x="105" y="22" fill="#5f5f5f"/>',
        '<use href="#star" x="140" y="12" fill="#5f5f5f"/>',
        # Top-right corner and sky stars
        '<use href="#star" x="235" y="14" fill="#5f5f5f"/>',
        '<use href="#star" x="295" y="18" fill="#5f5f5f"/>',
        '<use href="#star" x="345" y="55" fill="#5f5f5f"/>',
        '<use href="#star" x="375" y="16" fill="#5f5f5f"/>',
        '<use href="#star" x="412" y="38" fill="#5f5f5f"/>',
        '<use href="#star" x="430" y="15" fill="#5f5f5f"/>',
        '<use href="#star" x="435" y="65" fill="#5f5f5f"/>',
        '<use href="#star" x="424" y="95" fill="#5f5f5f"/>',
        # Moon
        '<use href="#moon" x="250" y="24" fill="#6f6f6f"/>',
        # Clouds gently hovering in right quadrant
        f'<g fill="{DIM}">',
        '<g transform="translate(325 36)"><use href="#cloud" class="c0"/></g>',
        '<g transform="translate(385 75)"><use href="#cloud" class="c1"/></g>',
        '</g>',
        # Majestic pterodactyl flying slowly across the sky from left to right
        '<g transform="translate(0 28)"><g class="pterofly">'
        '<g fill="#888888">'
        '<use href="#ptero1" class="pfa"/>'
        '<use href="#ptero2" class="pfb"/>'
        '</g></g></g>',
    ]

    bump = []
    for i, seg in enumerate((0, 1, 0)):
        d = path_d(rects(horizon_bumps(seg, 0, 600)))
        bump.append(f'<path transform="translate({600 * i} {LINE_Y})" d="{d}"/>')
    ground = (f'<rect x="0" y="{LINE_Y}" width="{xw}" height="1" fill="#b4b4b4"/>'
              f'<g fill="#8a8a8a">{"".join(bump)}</g>')

    # Small cactus on land under name on left side
    cactus_small_elem = '<use href="#cactus_small" x="48" y="98" fill="#888888"/>'

    # Sitting Dino matching profile picture with natural eye blink
    dino_elem = (
        f'<g fill="#e6e6e6">'
        f'<use href="#dino_sit" x="235" y="108"/>'
        f'<rect class="dblink" x="254" y="109" width="1.5" height="2" fill="#e6e6e6"/>'
        f'</g>'
    )

    # Campfire with warm layers & rising sparks
    fire_elem = (
        f'<g transform="translate(280 109)">'
        f'<rect class="sp1" x="10" y="4" width="2" height="2" fill="#ffaa00"/>'
        f'<rect class="sp2" x="15" y="2" width="2" height="2" fill="#ffdd00"/>'
        f'<rect class="sp3" x="7" y="6" width="1" height="1" fill="#ff7700"/>'
        f'<rect class="sp4" x="12" y="5" width="1.5" height="1.5" fill="#ffbb00"/>'
        f'<g fill="#ff5e00">'
        f'<use href="#fl1" class="fl1"/>'
        f'<use href="#fl2" class="fl2"/>'
        f'<use href="#fl3" class="fl3"/>'
        f'</g>'
        f'<g fill="#ffdd00">'
        f'<use href="#fc1" class="fl1"/>'
        f'<use href="#fc2" class="fl2"/>'
        f'<use href="#fc3" class="fl3"/>'
        f'</g>'
        f'<use href="#fire_logs" y="16" fill="#666666"/>'
        f'</g>'
    )

    # Saguaro Cactus matching profile picture
    cactus_elem = f'<use href="#saguaro" x="395" y="102" fill="#888888"/>'

    wrap = f'<g transform="translate(0 {oy}) scale(2)">'
    world_front = wrap + ground + cactus_small_elem + cactus_elem + dino_elem + fire_elem + "</g>"
    world_sky = wrap + "".join(sky) + "</g>"

    # Left-aligned clean typography with distraction-free background
    body = [
        f'<path d="{notch(1, 1, W - 2, H - 2, 6)}" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>',
        world_sky,
        text("MOHD JUNAID", 64, 120, 5, INK),
        text("Full-stack developer", 66, 172, 2.5, SOFT),
        world_front,
    ]

    return svg(H, "Mohd Junaid: Full-stack developer",
               "A professional monochrome hero banner. Left side features crisp typography for Mohd Junaid, "
               "full-stack developer, with a small cactus on the land below. Right side features an accurate pixel-art night scene with a T-Rex sitting "
               "peacefully by a crackling campfire, a saguaro cactus, crescent moon, gentle clouds, stars in the corners, and a pterodactyl gliding across the sky.",
               "".join(css), "".join(defs), "".join(body))


def track():
    H = 200
    cfg = dict(
        w=W, line_y=180, v=150, P=9, clear=20,
        events=[
            dict(kind="cactus", sprite="cs1", y=105, spawn=0.0, base=200, act="jump"),
            dict(kind="cactus", sprite="cs2", y=105, spawn=3.2, base=300, act="jump"),
            dict(kind="ptero", y=50, spawn=4.9, speed=170, base=380),
        ],
        clouds=[(190, 58), (340, 40)],
    )
    w = build_world(cfg)
    body = [f'<path d="{notch(1, 1, W - 2, H - 2, 6)}" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>',
            w["sky"], w["front"]]
    return svg(H, "Dino Runner level strip",
               "A pixel T-Rex runs along a scrolling ground line, jumping over small cacti while a "
               "pterodactyl flies overhead and clouds drift past.",
               w["css"], w["defs"], "".join(body))


# --------------------------------------------------------------------------- #
# HUD panels
# --------------------------------------------------------------------------- #

BLINK = ".blink{animation:blink 1s steps(1,end) infinite}@keyframes blink{50%{opacity:0}}"


def profile_panel():
    H = 250
    b = chrome(H, "Player profile", "Player 01")
    b.append(box(24, 66, W - 48, 146))
    b.append(text("Hey, I'm Mohd Junaid - a third-year B.Tech Computer Science student,", 44, 84, 2, INK))
    b.append(text("full-stack developer, and President of NEXUS Coding Club.", 44, 106, 2, INK))
    b.append(text("I enjoy turning ideas into useful software, exploring how systems fit", 44, 138, 2, SOFT))
    b.append(text("together, and building with AI. My current work sits around the MERN", 44, 160, 2, SOFT))
    last = "stack, TypeScript, Agentic Engineering, and Spec-Driven Development."
    b.append(text(last, 44, 182, 2, SOFT))
    cursor_x = 44 + text_w(last, 2) + 8
    b.append(f'<rect class="blink" x="{cursor_x}" y="182" width="8" height="14" fill="{INK}"/>')
    b.append(ground_footer(H - 22))
    return svg(H, "Mohd Junaid: Player profile",
               "Heads-up display showing Mohd Junaid's developer introduction: third-year B.Tech "
               "Computer Science student, full-stack developer, President of NEXUS Coding Club, "
               "working with MERN stack, TypeScript, Agentic Engineering, and Spec-Driven Development.",
               BLINK, digit_defs(), "".join(b))


def workflow():
    H = 190
    steps = ["Specify", "Plan", "Build", "Evaluate"]
    gap, cw, ch = 16, 198, 82
    b = chrome(H, "Engineering loop", "Spec-driven")
    css = ("@keyframes wf{0%,24.9%{stroke:#e6e6e6}25%,100%{stroke:#444}}"
           ".wf{animation:wf 4s steps(1,end) infinite}")
    for i, s in enumerate(steps):
        x = 24 + i * (cw + gap)
        y = 66
        b.append(box(x, y, cw, ch, stroke=EDGE, cls="wf",
                     style=f"animation-delay:{-(4 - i) % 4}s"))
        b.append(digits(f"0{i + 1}", x + 16, y + 10, 2, SOFT))
        b.append(text(s, x + 16, y + 50, 3, INK))
        if i < 3:
            ax = x + cw + 3
            b.append(f'<path transform="translate({ax} {y + ch // 2 - 7}) scale(3)" fill="{SOFT}" '
                     f'd="m0 0h1v5h-1zm1 1h1v3h-1zm1 1h1v1h-1z"/>')
    b.append(ground_footer(H - 22))
    return svg(H, "Engineering loop: specify, plan, build, evaluate",
               "Four stages shown as game slots that light up in turn: 01 Specify the problem, 02 Plan the "
               "system, 03 Build in small steps, 04 Evaluate, test and refine.",
               css, digit_defs(), "".join(b))


def loadout():
    H = 206
    slots = [("{ }", "Languages", "04"), ("</>", "Frontend", "03"),
             ("DB", "Backend", "05"), (">_", "Toolkit", "05")]
    gap, cw, ch = 16, 198, 104
    b = chrome(H, "Inventory", "4 slots")
    for i, (icon, label, count) in enumerate(slots):
        x = 24 + i * (cw + gap)
        y = 66
        b.append(box(x, y, cw, ch))
        b.append(f'<path d="{notch(x + 14, y + 14, 48, 48, 4)}" fill="{BG}" stroke="{SOFT}" stroke-width="2"/>')
        b.append(text(icon, x + 38, y + 27, 3, INK, "m"))
        b.append(digits(count, x + 80, y + 23, 2, INK))
        b.append(text(label, x + 14, y + 74, 3, SOFT))
    b.append(ground_footer(H - 22))
    return svg(H, "Inventory: equipped skills and tools",
               "Four inventory slots: Languages (4 items), Frontend (3 items), Backend and databases "
               "(5 items), Toolkit (5 items).",
               "", digit_defs(), "".join(b))


def quests():
    H = 298
    rows = [("Roomify", "Floor plans to 3D"), ("Ghost AI", "System design"),
            ("Repnex", "AI dev workspace"), ("NEXUS", "Coding club")]
    rh, gap = 44, 8
    b = chrome(H, "Quest log", "4 quests")
    for i, (name, cat) in enumerate(rows):
        x, y, w = 24, 66 + i * (rh + gap), W - 48
        b.append(box(x, y, w, rh))
        nx = x + 16
        b.append(text(name, nx, y + 5, 4, INK))
        cx = x + w - 16
        b.append(text(cat, cx, y + 12, 3, SOFT, "e"))
        d0 = nx + text_w(name, 4) + 16
        d1 = cx - text_w(cat, 3) - 16
        dots = "".join(f"M{k} 0h2v2h-2z" for k in range(0, int(d1 - d0), 8))
        b.append(f'<path transform="translate({fmt(d0)} {y + 31})" fill="#444" d="{dots}"/>')
    b.append(ground_footer(H - 22))
    return svg(H, "Quest log: featured projects and community",
               "Four quests: Roomify, floor plans to 3D. Ghost AI, system design. Repnex, AI developer "
               "workspace. NEXUS, the coding club community.",
               "", digit_defs(), "".join(b))


def checkpoint():
    H = 204
    line = 172
    b = chrome(H, "Checkpoint", "Next level")
    css = (".dot{animation:blink 1.2s steps(1,end) infinite}.d2{animation-delay:.4s}.d3{animation-delay:.8s}"
           "@keyframes blink{50%{opacity:0}}"
           "@keyframes run{0%{transform:translateX(-40px)}70%,100%{transform:translateX(0)}}"
           ".run{animation:run 6s linear infinite}"
           "@keyframes gs{to{transform:translateX(-1200px)}}.gs{animation:gs 8s linear infinite}"
           ".fb{opacity:0}.fa{animation:fa .1667s steps(1,end) infinite}.fb{animation:fb .1667s steps(1,end) infinite}"
           "@keyframes fa{0%{opacity:1}50%{opacity:0}}@keyframes fb{0%{opacity:0}50%{opacity:1}}")
    # restart button, straight from the game's sprite sheet
    b.append(f'<g transform="translate(28 76) scale(2)" fill="{INK}"><use href="#rs"/></g>')
    b.append(text("Next level loading", 124, 78, 4, INK))
    dx = 124 + text_w("Next level loading", 4) + 14
    for k in range(3):
        b.append(f'<rect class="dot{" d%d" % (k + 1) if k else ""}" x="{dx + k * 14}" y="{78 + 22}" '
                 f'width="6" height="6" fill="{INK}"/>')
    b.append(text("Keep building. Keep learning.", 124, 118, 3, SOFT))
    # finish line
    fx = 858
    b.append(f'<rect x="{fx}" y="{line - 56}" width="2" height="56" fill="{INK}"/>')
    for r in range(3):
        for c in range(3):
            if (r + c) % 2 == 0:
                b.append(f'<rect x="{fx + 2 + c * 8}" y="{line - 56 + r * 8}" width="8" height="8" fill="{INK}"/>')
    # scrolling ground line + running T-Rex (feet sit just below the line, as in the game)
    bump = "".join(f'<path transform="translate({600 * i} 0)" d="{path_d(rects(horizon_bumps(sg, 0, 600)))}"/>'
                   for i, sg in enumerate((0, 1, 0)))
    b.append(f'<rect x="12" y="{line}" width="{W - 24}" height="2" fill="#b4b4b4"/>')
    b.append(f'<svg x="12" y="{line}" width="{W - 24}" height="24" overflow="hidden"><g transform="scale(2)" '
             f'fill="#8a8a8a"><g class="gs">{bump}</g></g></svg>')
    S, R1, R2 = pix("trex_stand"), pix("trex_run1"), pix("trex_run2")
    common = S & R1 & R2
    defs = (sprite_path("rs", pix("restart")) + sprite_path("tb", common)
            + sprite_path("t1", R1 - common) + sprite_path("t2", R2 - common))
    ty = line - 2 * (LINE_Y - DINO_Y)
    b.append(f'<g transform="translate(748 {ty}) scale(2)" fill="{INK}"><g class="run"><use href="#tb"/>'
             '<use href="#t1" class="fa"/><use href="#t2" class="fb"/></g></g>')
    return svg(H, "Checkpoint: keep moving forward",
               "A restart-style button reads Next level loading with animated dots, and the message keep "
               "building, keep learning. A T-Rex runs along the ground toward a checkered finish line.",
               css, defs, "".join(b))


def static_variant(data):
    """Same artwork with every animation removed (the fallback compositions are the base styles)."""
    import re
    data = re.sub(r"animation(-delay)?:[^;}\"]*;?", "", data)
    return data


ASSETS = {
    "dino-world.svg": hero, "dino-track.svg": track, "profile-panel.svg": profile_panel,
    "workflow-panel.svg": workflow, "loadout-panel.svg": loadout, "quest-panel.svg": quests,
    "checkpoint-panel.svg": checkpoint,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for name, fn in ASSETS.items():
        data = fn()
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
        total += len(data)
        print(f"{name:24s} {len(data):7d} bytes")
        still = static_variant(data)
        if "@keyframes" in data:   # only animated assets need a reduced-motion twin
            os.makedirs(os.path.join(OUT, "static"), exist_ok=True)
            with open(os.path.join(OUT, "static", name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(still)
    print(f"{'total':24s} {total:7d} bytes")
