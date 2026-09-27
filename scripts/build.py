#!/usr/bin/env python3
"""Generate the animated SVGs used by the GitHub profile README.

    python scripts/build.py                          # rebuild every SVG in assets/
    python scripts/build.py --photo me.jpg [--mono]  # crop me.jpg into assets/avatar.jpg, then rebuild

Every graphic is written twice, <name>-dark.svg and <name>-light.svg; the README
picks one per viewer with <picture> + prefers-color-scheme.
"""
from __future__ import annotations

import argparse
import base64
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
AVATAR = ASSETS / "avatar.jpg"
MAX_BYTES = 150_000

# GitHub's own UI font stack: an SVG shown through <img> cannot load web fonts.
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

# Feng shui career palette: water (blues) carries the motion, metal (ink/silver) the text.
THEMES = {
    "dark": {
        "tx": "#e6edf3", "mu": "#8b949e", "ln": "#30363d", "a2": "#60A5FA",
        "sky": "#1c2129", "back": "#1E3A8A", "front": "#3B82F6", "sun": "#e6edf3", "edge": "#ffffff",
    },
    "light": {
        "tx": "#1f2328", "mu": "#59636e", "ln": "#d0d7de", "a2": "#2563EB",
        "sky": "#eef2f6", "back": "#93C5FD", "front": "#2563EB", "sun": "#1E3A8A", "edge": "#000000",
    },
}

# Head-and-shoulders crop of the source photo: centre x, centre y (fractions of
# width/height) and side length (fraction of width). Any wider and the coffee cup
# creeps in at the lower left.
CROP = (0.512, 0.350, 0.422)


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def svg(w: int, h: int, css: str, body: str, label: str, scale: float = 1) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{f(w * scale)}" height="{f(h * scale)}" role="img" aria-label="{label}">'
        f"<title>{label}</title><style>{css}</style>{body}</svg>\n"
    )


def base_css(t: dict) -> str:
    return (
        f"text{{font-family:{FONT}}}"
        f".tx{{fill:{t['tx']}}}.mu{{fill:{t['mu']}}}.lf{{fill:{t['ln']}}}.na{{fill:{t['a2']}}}"
        f".ln{{stroke:{t['ln']}}}.a2{{stroke:{t['a2']}}}"
        "@keyframes up{from{opacity:0;transform:translateY(6px)}}"
        ".in{animation:up .9s cubic-bezier(.2,.7,.2,1) both}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )


# --- hero: name on the left, portrait as the hub of a neural network ---------

HUB, HUB_R, RING_R = (575, 82), 50, 56
NODES = {
    "a": (365, 48), "b": (345, 118), "c": (440, 92), "d": (455, 30),
    "e": (470, 148), "f": (655, 22), "g": (662, 146), "h": (520, 156),
}
MESH = ["ac", "bc", "ad", "ce", "be", "eh", "hg"]
SPOKES = "cdefgh"
# Pulses leave the portrait and travel outward along these routes.
ROUTES = [("c", "b"), ("d", "a"), ("f",), ("e", "b"), ("g",), ("h", "g")]
PULSE_TIMING = [(4.5, 0), (5.5, -1.5), (3.5, -3), (5, -0.7), (4, -2.2), (6, -3.6)]


def on_ring(name: str) -> tuple[float, float]:
    x, y = NODES[name]
    dx, dy = x - HUB[0], y - HUB[1]
    k = RING_R / math.hypot(dx, dy)
    return HUB[0] + dx * k, HUB[1] + dy * k


def pt(p: tuple[float, float]) -> str:
    return f"{f(p[0])} {f(p[1])}"


def hero(t: dict, photo: str | None) -> str:
    css = base_css(t) + (
        "@keyframes fl{to{stroke-dashoffset:-200}}"
        ".p{stroke-dasharray:10 190;animation:fl 4.5s linear infinite}"
        "@keyframes br{50%{opacity:.3}}.n{animation:br 3.2s ease-in-out infinite}"
        "@keyframes sp{to{transform:rotate(360deg)}}"
        ".o{transform-box:fill-box;transform-origin:center;animation:sp 14s linear infinite}"
        "@media (prefers-reduced-motion:reduce){.p{display:none}}"
        # Media queries inside an <img> SVG see the image's rendered width: on phones
        # the banner shrinks to ~330 px, so the text grows to stay readable.
        "@media (max-width:520px){.hi,.sb{font-size:24px}.nm{font-size:54px}"
        ".hi{transform:translateY(-7px)}.sb{transform:translateY(6px)}}"
    )
    mesh = "".join(f"M{pt(NODES[a])}L{pt(NODES[b])}" for a, b in MESH)
    spokes = "".join(f"M{pt(on_ring(n))}L{pt(NODES[n])}" for n in SPOKES)
    pulses = "".join(
        f'<path class="p" pathLength="100" style="animation-duration:{d}s;animation-delay:{delay}s" '
        f'd="M{pt(on_ring(r[0]))}{"".join("L" + pt(NODES[n]) for n in r)}"/>'
        for r, (d, delay) in zip(ROUTES, PULSE_TIMING)
    )
    nodes = "".join(
        f'<circle class="n" style="animation-delay:{-0.6 * i:.1f}s" cx="{x}" cy="{y}" r="{3.5 if n == "c" else 3}"/>'
        for i, (n, (x, y)) in enumerate(NODES.items())
    )
    cx, cy = HUB
    if photo:
        portrait = (
            f'<clipPath id="pc"><circle cx="{cx}" cy="{cy}" r="{HUB_R}"/></clipPath>'
            f'<image class="in" style="animation-delay:.2s" href="data:image/jpeg;base64,{photo}" '
            f'x="{cx - HUB_R}" y="{cy - HUB_R}" width="{2 * HUB_R}" height="{2 * HUB_R}" '
            f'clip-path="url(#pc)" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        portrait = (
            f'<circle class="lf" cx="{cx}" cy="{cy}" r="{HUB_R}"/>'
            f'<text class="mu" x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="12">photo</text>'
        )
    body = (
        f'<g class="ln" fill="none" stroke-width="1"><path d="{mesh}{spokes}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{RING_R}"/></g>'
        f'<g class="a2" fill="none" stroke-width="2" stroke-linecap="round">{pulses}'
        f'<circle class="o" cx="{cx}" cy="{cy}" r="{RING_R}" stroke-width="1.5" pathLength="100" stroke-dasharray="11 89"/></g>'
        f'<g class="na">{nodes}</g>'
        f"{portrait}"
        '<text class="mu in hi" x="40" y="58" font-size="15">Hi, I\'m</text>'
        '<text class="tx in nm" style="animation-delay:.15s" x="38" y="98" font-size="44" font-weight="600" letter-spacing="-.5">Davin</text>'
        '<text class="in sb" style="animation-delay:.3s" x="40" y="126" font-size="17">'
        '<tspan class="tx">AI Engineer</tspan><tspan class="mu"> · Robotics AI</tspan></text>'
    )
    return svg(680, 170, css, body, "Davin, AI Engineer · Robotics AI", scale=1200 / 680)


# --- project card: tech_europe (technical drawing -> 3D part) ----------------

def iso(x: float, y: float, z: float, ox: float = 182.7, oy: float = 70) -> tuple[float, float]:
    return ox + (x - y) * 0.866, oy + (x + y) * 0.5 - z


# Two cards sit side by side, so on phones each renders ~160 px wide: keep just a
# larger title there (the description stays in the README's alt text).
CARD_CSS = "@media (max-width:300px){.cd{display:none}.ct{font-size:30px;transform:translateY(24px)}}"


def card_frame(t: dict, title: str, desc: str, lang: str) -> str:
    return (
        '<rect class="ln" x=".5" y=".5" width="399" height="239" rx="12" fill="none"/>'
        f'<text class="tx ct" x="20" y="180" font-size="15" font-weight="600">{title}</text>'
        '<text class="mu ct" x="380" y="180" font-size="15" text-anchor="end">↗</text>'
        f'<g class="cd"><text class="mu" x="20" y="202" font-size="13">{desc}</text>'
        f'<circle class="na" cx="24" cy="220" r="4"/>'
        f'<text class="mu" x="34" y="224" font-size="12">{lang}</text></g>'
    )


def card_tech_europe(t: dict) -> str:
    css = base_css(t) + (
        ".d2{stroke-dasharray:100;animation:d2 8s cubic-bezier(.4,0,.2,1) infinite}"
        ".dm{animation:dm 8s linear infinite}"
        ".d3{stroke-dasharray:100;animation:d3 8s cubic-bezier(.4,0,.2,1) infinite}"
        ".tf{animation:tf 8s linear infinite}"
        ".sc{animation:sc 8s linear infinite}"
        "@keyframes d2{0%{stroke-dashoffset:100;opacity:1}22%,42%{stroke-dashoffset:0;opacity:1}"
        "50%,100%{stroke-dashoffset:0;opacity:0}}"
        "@keyframes dm{0%,18%{opacity:0}26%,42%{opacity:1}50%,100%{opacity:0}}"
        "@keyframes d3{0%,46%{stroke-dashoffset:100;opacity:1}72%,90%{stroke-dashoffset:0;opacity:1}"
        "97%,100%{stroke-dashoffset:0;opacity:0}}"
        "@keyframes tf{0%,64%{opacity:0}74%,90%{opacity:1}97%,100%{opacity:0}}"
        "@keyframes sc{0%,26%{opacity:0;transform:translateY(0)}28%{opacity:1;transform:translateY(0)}"
        "40%{opacity:1;transform:translateY(56px)}43%,100%{opacity:0;transform:translateY(56px)}}"
        "@media (prefers-reduced-motion:reduce){.d2,.dm,.sc{display:none}}" + CARD_CSS
    )
    # Front view of a 90 x 50 block with a vertical through-hole, plus its dimensions.
    drawing = (
        '<path class="d2" pathLength="100" d="M155 53H245V103H155Z" fill="none" stroke-width="1.25" '
        f'stroke="{t["tx"]}"/>'
        f'<g class="dm" fill="none" stroke="{t["mu"]}" stroke-width=".75">'
        '<path stroke-dasharray="4 3" d="M188 53V103M212 53V103"/>'
        '<path stroke-dasharray="10 3 2 3" d="M200 46V110"/>'
        '<path d="M155 107V122M245 107V122M155 118H245M249 53H264M249 103H264M260 53V103"/></g>'
        '<g class="dm"><text class="mu" x="200" y="115" font-size="10" text-anchor="middle">90</text>'
        '<text class="mu" x="266" y="81" font-size="10">50</text></g>'
        '<path class="sc a2" d="M148 50H252" stroke-width="1.5" stroke-linecap="round"/>'
    )
    # The same block in isometric 3D; (0,0,0) is the hidden back corner.
    W, D, H = 90, 50, 50
    E, F, B, C = iso(0, 0, H), iso(W, 0, H), iso(W, 0, 0), iso(W, D, 0)
    Dp, Hp, G = iso(0, D, 0), iso(0, D, H), iso(W, D, H)
    top_c = iso(W / 2, D / 2, H)
    rx, ry = 12 * 1.2247, 12 * 0.7071
    part = (
        f'<path class="tf" d="M{pt(E)}L{pt(F)}L{pt(G)}L{pt(Hp)}Z" fill="{t["a2"]}" fill-opacity=".12"/>'
        f'<g class="a2" fill="none" stroke-width="1.5" stroke-linejoin="round">'
        f'<path class="d3" pathLength="100" d="M{pt(E)}L{pt(F)}L{pt(B)}L{pt(C)}L{pt(Dp)}L{pt(Hp)}Z"/>'
        f'<path class="d3" pathLength="100" d="M{pt(Hp)}L{pt(G)}L{pt(F)}M{pt(G)}L{pt(C)}"/>'
        f'<ellipse class="d3" pathLength="100" cx="{f(top_c[0])}" cy="{f(top_c[1])}" rx="{f(rx)}" ry="{f(ry)}"/>'
        f'<path class="d3" pathLength="100" d="M{f(top_c[0] - rx + 1.5)} {f(top_c[1] + 6)}'
        f'A{f(rx - 1.5)} {f(ry - 1)} 0 0 1 {f(top_c[0] + rx - 1.5)} {f(top_c[1] + 6)}"/></g>'
    )
    body = drawing + part + card_frame(t, "tech_europe", "Turning a technical drawing into a 3D part", "Python")
    return svg(400, 240, css, body, "tech_europe: turning a technical drawing into a 3D part")


# --- project card: image2lego (image -> brick mosaic) ------------------------

COLS, ROWS, CELL = 12, 8, 14
GX, GY = 116, 24  # grid origin


def back_ridge(x: float) -> float:
    return 2.8 + abs(x - 4.2) * 0.75


def front_ridge(x: float) -> float:
    return 4.6 + abs(x - 9) * 0.55


def tone(c: int, r: int) -> str:
    x, y = c + 0.5, r + 0.5
    if y > front_ridge(x):
        return "front"
    if y > back_ridge(x):
        return "back"
    if math.hypot(x - 8.6, y - 2.3) < 1.6:
        return "sun"
    return "sky"


def card_image2lego(t: dict) -> str:
    css = base_css(t) + (
        ".src{animation:src 8s linear infinite}"
        ".bk{animation:bk 8s cubic-bezier(.2,.8,.2,1) infinite both}"
        ".st{transform-box:fill-box;transform-origin:center;animation:st 8s ease-out infinite both}"
        "@keyframes src{0%,14%{opacity:1}30%,90%{opacity:0}98%,100%{opacity:1}}"
        "@keyframes bk{0%,14%{opacity:0;transform:translateY(-16px)}24%,86%{opacity:1;transform:translateY(0)}"
        "94%,100%{opacity:0;transform:translateY(0)}}"
        "@keyframes st{0%,28%{transform:scale(0)}34%{transform:scale(1.25)}38%,86%{transform:scale(1);opacity:1}"
        "94%,100%{transform:scale(1);opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.src{display:none}}" + CARD_CSS
    )
    x1, y1 = GX + COLS * CELL, GY + ROWS * CELL
    px = lambda c: GX + c * CELL  # noqa: E731
    py = lambda r: GY + r * CELL  # noqa: E731
    # The original "photo": a smooth landscape that the bricks replace.
    bottom_back = 4.2 + (ROWS - 2.8) / 0.75
    left_front = 9 - (ROWS - 4.6) / 0.55
    source = (
        f'<clipPath id="sc"><rect x="{GX}" y="{GY}" width="{COLS * CELL}" height="{ROWS * CELL}" rx="6"/></clipPath>'
        f'<g class="src" clip-path="url(#sc)">'
        f'<rect x="{GX}" y="{GY}" width="{COLS * CELL}" height="{ROWS * CELL}" fill="{t["sky"]}"/>'
        f'<circle cx="{f(px(8.6))}" cy="{f(py(2.3))}" r="{f(1.6 * CELL)}" fill="{t["sun"]}"/>'
        f'<path fill="{t["back"]}" d="M{GX} {y1}V{f(py(back_ridge(0)))}L{f(px(4.2))} {f(py(2.8))}L{f(px(bottom_back))} {y1}Z"/>'
        f'<path fill="{t["front"]}" d="M{f(px(left_front))} {y1}L{f(px(9))} {f(py(4.6))}L{x1} {f(py(front_ridge(COLS)))}V{y1}Z"/>'
        "</g>"
    )
    bricks = []
    for r in range(ROWS):
        for c in range(COLS):
            delay = f"{c * 0.05 + (ROWS - 1 - r) * 0.035:.2f}"
            fill = t[tone(c, r)]
            x, y = px(c), py(r)
            bricks.append(
                f'<g class="bk" style="animation-delay:{delay}s">'
                f'<rect x="{x + 0.75}" y="{y + 0.75}" width="12.5" height="12.5" rx="2" fill="{fill}"/>'
                f'<circle class="st" style="animation-delay:{delay}s" cx="{x + 7}" cy="{y + 7}" r="3.6" '
                f'fill="{fill}" stroke="{t["edge"]}" stroke-opacity=".22" stroke-width=".8"/></g>'
            )
    body = source + "".join(bricks) + card_frame(
        t, "image2lego", "Turns any image into a buildable brick mosaic", "Python"
    )
    return svg(400, 240, css, body, "image2lego: turns any image into a buildable brick mosaic")


# --- tech stack: chips that fade in, with a light sweep beneath -------------

# Three short rows keep the graphic narrow, so it barely shrinks on phones.
STACK = [
    ["Python", "PyTorch", "TensorFlow", "scikit-learn"],
    ["LangChain", "LangGraph", "LiveKit", "Flutter"],
    ["Java", "REST APIs", "Linux"],
]
CORE = {"Python", "PyTorch", "TensorFlow", "scikit-learn", "LangChain", "LangGraph"}  # full ink; the rest silver


# Helvetica advance widths per 1000 em. A fixed table keeps the build identical on
# every machine; it runs a little wider than Segoe UI and SF, so labels never clip.
HELVETICA = {
    **dict.fromkeys("abdeghnopqu", 556), **dict.fromkeys("ckvxyzJ", 500), **dict.fromkeys("ijl", 222),
    "f": 278, "t": 278, "r": 333, "s": 500, "m": 833, "w": 722, " ": 278, "-": 333, ".": 278,
    **dict.fromkeys("ABEKPSVXY", 667), **dict.fromkeys("CDHNRU", 722), **dict.fromkeys("FTZ", 611),
    "G": 778, "O": 778, "Q": 778, "I": 278, "L": 556, "M": 833, "W": 944,
}


def text_width(s: str, size: int = 14) -> float:
    return sum(HELVETICA.get(ch, 556) for ch in s) * size / 1000


def stack(t: dict) -> str:
    CH, GAP, PAD, X0 = 34, 10, 14, 1  # rows are left-aligned with the README text
    rows = [[text_width(n) * 1.06 + 2 * PAD for n in names] for names in STACK]
    W = math.ceil(max(sum(ws) + GAP * (len(ws) - 1) for ws in rows)) + 2 * X0
    SWEEP_Y, X1 = X0 + len(STACK) * (CH + GAP) + 12, W - X0
    # The 120-unit sweep crosses the baseline in the first 60% of each 6 s cycle;
    # every chip lights up as it passes beneath its centre.
    speed = (120 + X1 - X0) / 3.6
    css = base_css(t) + (
        ".ch{animation:up .6s cubic-bezier(.2,.7,.2,1) both}"
        ".cr{animation:hl 6s linear infinite}"
        ".sw{stroke-dasharray:120 1400;animation:sw 6s linear infinite}"
        f"@keyframes hl{{0%{{stroke:{t['ln']}}}3%{{stroke:{t['a2']}}}12%,100%{{stroke:{t['ln']}}}}}"
        f"@keyframes sw{{0%{{stroke-dashoffset:120}}60%,100%{{stroke-dashoffset:-{X1 - X0}}}}}"
        "@media (prefers-reduced-motion:reduce){.sw{display:none}}"
    )
    chips, i = [], 0
    for row, (names, widths) in enumerate(zip(STACK, rows)):
        x, y = X0, X0 + row * (CH + GAP)
        for name, w in zip(names, widths):
            cls = "tx" if name in CORE else "mu"
            cx = x + w / 2
            glow = (cx - X0 + 60) / speed - 0.18
            chips.append(
                f'<g class="ch" style="animation-delay:{i * 0.06:.2f}s">'
                f'<rect class="cr ln" style="animation-delay:{glow:.2f}s" x="{f(x)}" y="{y}" width="{f(w)}" '
                f'height="{CH}" rx="{CH / 2}" fill="none"/>'
                f'<text class="{cls}" x="{f(cx)}" y="{y + 22}" font-size="14" text-anchor="middle">{name}</text></g>'
            )
            x += w + GAP
            i += 1
    body = (
        "".join(chips)
        + f'<path class="ln" d="M{X0} {SWEEP_Y}H{X1}" stroke-width="1"/>'
        + f'<path class="sw a2" d="M{X0} {SWEEP_Y}H{X1}" stroke-width="1.5" stroke-linecap="round"/>'
    )
    label = "Tech stack: " + ", ".join(n for row in STACK for n in row)
    return svg(W, SWEEP_Y + 2, css, body, label)


# --- build -------------------------------------------------------------------

def crop_avatar(src: Path, mono: bool) -> None:
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = im.size
    cx, cy, side = CROP[0] * w, CROP[1] * h, CROP[2] * w
    im = im.crop(tuple(round(v) for v in (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)))
    im = im.resize((360, 360), Image.LANCZOS)
    if mono:
        im = ImageOps.grayscale(im).convert("RGB")
    im.save(AVATAR, "JPEG", quality=82, optimize=True, progressive=True)
    print(f"cropped {src.name} -> {AVATAR.relative_to(ROOT)} ({AVATAR.stat().st_size:,} bytes)")


def write(name: str, content: str) -> None:
    ET.fromstring(content)  # fail loudly on malformed XML
    size = len(content.encode())
    if size > MAX_BYTES:
        raise SystemExit(f"{name} is {size:,} bytes, over the {MAX_BYTES:,} byte budget")
    (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"{name:32} {size:>8,} bytes")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", type=Path, help="source photo to crop into assets/avatar.jpg")
    ap.add_argument("--mono", action="store_true", help="make the cropped avatar black and white")
    args = ap.parse_args()

    ASSETS.mkdir(exist_ok=True)
    if args.photo:
        crop_avatar(args.photo, args.mono)
    photo = base64.b64encode(AVATAR.read_bytes()).decode() if AVATAR.exists() else None
    if photo is None:
        print("no assets/avatar.jpg yet: hero uses a placeholder portrait")

    for theme, t in THEMES.items():
        write(f"hero-{theme}.svg", hero(t, photo))
        write(f"card-tech_europe-{theme}.svg", card_tech_europe(t))
        write(f"card-image2lego-{theme}.svg", card_image2lego(t))
        write(f"stack-{theme}.svg", stack(t))


if __name__ == "__main__":
    main()
