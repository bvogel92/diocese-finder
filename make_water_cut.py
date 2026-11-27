#!/usr/bin/env python3
"""One-time step: cut lakes and bays out of the diocese shapes.

The diocese outlines are built from county shapes, and many counties extend over
water (the Great Lakes, Chesapeake Bay, Puget Sound, Great Salt Lake ...), so those
waters were drawn as land. This subtracts Natural Earth's 1:10m ocean and lake
polygons (public domain) from the lower 48 and writes
source/diocese_boundaries_water_cut.geojson, which build.py then uses.

The water that is cut off is kept too (property "water", simplified), because the
diocese still includes it: the app draws only the land, but a point on the water, or on
a small island Natural Earth doesn't show (Mackinac, Put-in-Bay), is still looked up
against the county-based outline.

Needs: pip install shapely   (only for this step; build.py doesn't need it)
Inputs (in source/): diocese_boundaries_revised.geojson, ne_10m_ocean.geojson,
                     ne_10m_lakes.geojson, ne_10m_minor_islands.geojson (naturalearthdata.com)
"""
import json, os
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
LOWER48 = box(-125.5, 24.0, -66.0, 49.6)   # Alaska, Hawaii and the Virgin Islands are left as they are
TOL = 0.006                                 # simplify the water outlines to about 600 m (keeps the app small)
ERODE = 0.004                               # leave ~400 m of shore so thin barrier islands survive

def load_water(fn, min_area=0.0):
    out = []
    for f in json.load(open(os.path.join(SRC, fn), encoding="utf-8"))["features"]:
        g = make_valid(shape(f["geometry"]))
        if g.area < min_area or not g.intersects(LOWER48):
            continue
        out.append(g.intersection(LOWER48))
    return out

print("loading water ...")
water = unary_union(load_water("ne_10m_ocean.geojson") + load_water("ne_10m_lakes.geojson", min_area=0.004))
water = water.buffer(-ERODE, quad_segs=1, join_style="mitre")
water = water.difference(unary_union(load_water("ne_10m_minor_islands.geojson")).buffer(0.002, quad_segs=1))
water = water.simplify(TOL, preserve_topology=True).buffer(0)
wide_water = water.buffer(0.01, quad_segs=1)   # the kept water overlaps the shore a little, so no gaps

gj = json.load(open(os.path.join(SRC, "diocese_boundaries_revised.geojson"), encoding="utf-8"))
changed = 0
for f in gj["features"]:
    g = make_valid(shape(f["geometry"]))
    if not g.intersects(LOWER48):
        continue
    cut = g.difference(water)
    # keep only polygon parts, drop specks smaller than ~0.1 km²
    parts = [p for p in getattr(cut, "geoms", [cut]) if p.geom_type == "Polygon" and p.area > 1e-5]
    for p in getattr(cut, "geoms", []):
        if p.geom_type == "MultiPolygon":
            parts += [q for q in p.geoms if q.area > 1e-5]
    if not parts:
        continue
    new = unary_union(parts)
    if abs(new.area - g.area) > 1e-6:
        changed += 1
        f["geometry"] = mapping(new)
        wet = g.intersection(wide_water).simplify(0.01, preserve_topology=True)
        wet_parts = [p for p in getattr(wet, "geoms", [wet]) if p.geom_type == "Polygon" and p.area > 1e-5]
        if wet_parts:
            f["properties"]["water"] = mapping(unary_union(wet_parts))

with open(os.path.join(SRC, "diocese_boundaries_water_cut.geojson"), "w", encoding="utf-8") as fh:
    json.dump(gj, fh, separators=(",", ":"))
print(f"dioceses with water removed: {changed}")
