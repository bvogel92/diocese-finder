#!/usr/bin/env python3
"""Draws the app icon: a rubric-red cross pattée on parchment with a thin gold ring."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "icons")
os.makedirs(OUT, exist_ok=True)
PAPER, RED, GOLD = (251, 248, 241), (163, 23, 28), (176, 138, 62)


def cross(d, cx, cy, r):
    """Cross pattée: four arms that flare out to the ends, with slightly concave ends."""
    n = r * 0.12   # half-width at the centre
    w = r * 0.42   # half-width at the arm ends
    for ang in range(4):
        pts = [(-n, n * 0.9), (-w, r), (0, r * 0.90), (w, r), (n, n * 0.9)]
        rot = []
        for x, y in pts:
            for _ in range(ang):
                x, y = -y, x
            rot.append((cx + x, cy + y))
        d.polygon(rot, fill=RED)
    d.rectangle([cx - n, cy - n, cx + n, cy + n], fill=RED)


def icon(size, maskable=False, ss=4):
    S = size * ss
    im = Image.new("RGB", (S, S), PAPER)
    d = ImageDraw.Draw(im)
    c = S / 2
    r = S * (0.30 if maskable else 0.36)
    ring = r * 1.18
    d.ellipse([c - ring, c - ring, c + ring, c + ring], outline=GOLD, width=max(2, int(S * 0.012)))
    cross(d, c, c, r)
    return im.resize((size, size), Image.LANCZOS)


icon(180).save(os.path.join(OUT, "icon-180.png"))
icon(192).save(os.path.join(OUT, "icon-192.png"))
icon(512).save(os.path.join(OUT, "icon-512.png"))
icon(512, maskable=True).save(os.path.join(OUT, "icon-maskable-512.png"))
print("icons written to", OUT)
