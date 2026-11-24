#!/usr/bin/env python3
"""Build data.js for Diocese Finder.

Joins the diocese boundary polygons (kburchfiel/us_diocese_mapper) with the
list of current ordinaries (Wikipedia, saved as source/bishops_*.tsv) and the
county -> diocese table, and writes everything the app needs into data.js so
the app runs with no network at all.

Run again whenever you update source/bishops_*.tsv:   python3 build.py
"""
import csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")

# --- bishops -----------------------------------------------------------------
bishop_file = sorted(glob.glob(os.path.join(SRC, "bishops_*.tsv")))[-1]
as_of = re.search(r"(\d{4}-\d{2}-\d{2})", bishop_file).group(1)

# Names that differ between Wikipedia and the boundary dataset
SPECIAL = {
    ("Boston", "Portland"): "Portland in Maine",
    ("Portland", "Portland"): "Portland in Oregon",
    ("Galveston-Houston", "Victoria"): "Victoria in Texas",
    ("St. Paul and Minneapolis", "Bismarck"): "Bismark",  # spelling in boundary data
}

def norm(s):
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\bSaint\b", "St.", s)
    return s.strip()

bishops = {}
for r in csv.DictReader(open(bishop_file, encoding="utf-8"), delimiter="\t"):
    see = r["see"]
    m = re.match(r"(Archdiocese|Diocese) (?:of |for the )(.*)", see)
    kind, short = m.group(1), norm(m.group(2))
    key = SPECIAL.get((norm(r["province"]), short), short)
    vacant = r["ordinary"].strip().lower() == "sede vacante"
    # Display name: fix the dataset's "Bismark" typo and use en dashes like Wikipedia
    bishops[key] = {
        "see": see.replace("Bismark", "Bismarck"),
        "kind": kind,
        "province": r["province"],
        "ordinary": None if vacant else r["ordinary"].strip(),
        "title": r["title"].strip(),
        "vacant": vacant,
    }

# --- cathedrals ----------------------------------------------------------------
cathedrals = {}
for r in csv.DictReader(open(os.path.join(SRC, "diocese_province_cathedral_list_revised.csv"), encoding="utf-8")):
    try:
        names = json.loads(r["Cathedral_List"])
        coords = json.loads(r["Cathedral_coord_list"])
    except Exception:
        names, coords = [], []
    cathedrals[r["Diocese"]] = [{"name": n, "lat": c[0], "lon": c[1]} for n, c in zip(names, coords)]

# --- boundaries ------------------------------------------------------------------
gj = json.load(open(os.path.join(SRC, "diocese_boundaries_revised.geojson"), encoding="utf-8"))

def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [rnd(x) for x in c]

def bbox(c, b=None):
    b = b or [999, 999, -999, -999]
    if isinstance(c[0], (int, float)):
        b[0], b[1] = min(b[0], c[0]), min(b[1], c[1])
        b[2], b[3] = max(b[2], c[0]), max(b[3], c[1])
        return b
    for x in c:
        bbox(x, b)
    return b

dioceses, missing = [], []
for f in gj["features"]:
    name = f["properties"]["Diocese"]
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    polys = rnd(polys)
    b = bishops.get(name)
    if not b:
        missing.append(name)
        b = {"see": "Diocese of " + name, "kind": "Diocese", "province": f["properties"]["Province"],
             "ordinary": None, "title": "", "vacant": False}
    dioceses.append({
        "id": name,
        **b,
        "cathedrals": cathedrals.get(name, []),
        "bbox": [round(v, 4) for v in bbox(polys)],
        "polys": polys,
    })

unused = sorted(set(bishops) - {d["id"] for d in dioceses})

# --- counties (offline fallback picker) ---------------------------------------
counties = {}
for r in csv.DictReader(open(os.path.join(SRC, "counties_by_diocese.csv"), encoding="utf-8")):
    detail = [x.strip() for x in r["Diocese_Detail"].split(",")]
    others = [x for x in detail if x and x != r["Diocese"]]
    counties.setdefault(r["State_Name"], []).append([r["NAMELSAD"], r["Diocese"], others])
for st in counties:
    counties[st].sort()

# --- states (postal code -> name), from the county table ------------------------
states = {}
for r in csv.DictReader(open(os.path.join(SRC, "counties_by_diocese.csv"), encoding="utf-8")):
    states[r["State_Code"]] = r["State_Name"]

# --- cities, towns, villages, CDPs: U.S. Census Gazetteer place file -------------
# Uses the newest source/YYYY_Gaz_place_national.txt (drop a newer one in to upgrade).
place_file = sorted(glob.glob(os.path.join(SRC, "*_Gaz_place_national.txt")))[-1]
place_year = os.path.basename(place_file)[:4]
raw = open(place_file, "rb").read()
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    text = raw.decode("latin-1")
lines = text.splitlines()
hdr = [h.strip() for h in lines[0].split("\t")]
col = {h: i for i, h in enumerate(hdr)}
TYPE_CODE = {"city": "c", "town": "t", "village": "v", "borough": "b", "CDP": "p"}
place_rows = []
for ln in lines[1:]:
    f = [x.strip() for x in ln.split("\t")]
    if len(f) < len(hdr) or f[col["USPS"]] not in states:
        continue  # skips Puerto Rico (no diocese boundaries here)
    full = re.sub(r"\s*\(.*\)\s*$", "", f[col["NAME"]])          # "Indianapolis city (balance)"
    m = re.search(r"\s+CDP$", full) or re.search(r"(?:\s+[a-z][a-z\-]*)+$", full)
    name = full[:m.start()] if m else full
    kind = TYPE_CODE.get(m.group(0).strip() if m else "", "c")  # "city and borough", "metro government"... are cities
    place_rows.append([name, f[col["USPS"]], kind, float(f[col["INTPTLAT"]]), float(f[col["INTPTLONG"]]),
                       float(f[col["ALAND_SQMI"]] or 0)])

# Population (GeoNames, towns of 1,000+) only to put bigger towns first in search results.
def _fold(x):
    import unicodedata
    x = "".join(ch for ch in unicodedata.normalize("NFD", x) if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"\bsaint\b", "st", x.replace(".", "").replace("'", ""))).strip()
pop = {}
for r in csv.DictReader(open(os.path.join(SRC, "geonames_us_cities1000.tsv"), encoding="utf-8"), delimiter="\t"):
    k = (_fold(r["name"]), r["state"])
    pop[k] = max(pop.get(k, 0), int(r["population"]))
for r in place_rows:
    r.insert(6, pop.get((_fold(r[0]), r[1]), 0))

# Flag the place nearest each cathedral as a see city, so "St. Louis" finds Missouri first.
import math
for d in dioceses:
    see_names = {x.strip().replace("Saint ", "St. ") for x in re.split(r"-| in | and ", d["see"].split(" of ", 1)[-1])}
    for c in d["cathedrals"]:
        k = math.cos(math.radians(c["lat"]))
        named = [r for r in place_rows if r[0] in see_names and abs(r[3] - c["lat"]) < 0.8 and abs(r[4] - c["lon"]) < 1.0]
        if named:
            for r in named:
                if len(r) == 7: r.append("S")
            continue
        best = min((r for r in place_rows if abs(r[3] - c["lat"]) < 0.3 and abs(r[4] - c["lon"]) < 0.4 and r[2] != "p"),
                   key=lambda r: (r[3] - c["lat"]) ** 2 + ((r[4] - c["lon"]) * k) ** 2, default=None)
        if best is not None and len(best) == 7:
            best.append("S")
matched_pop = sum(1 for r in place_rows if r[6])
place_rows = ["%s\t%s\t%s\t%.4f\t%.4f\t%g\t%d%s" % (r[0], r[1], r[2], r[3], r[4], round(r[5], 1), r[6], "\tS" if len(r) > 7 else "")
              for r in place_rows]

# --- ZIP codes: Census ZIP Code Tabulation Areas (centre points) -----------------
zip_file = sorted(glob.glob(os.path.join(SRC, "zcta_*.tsv")))[-1]
zip_year = re.search(r"zcta_(\d{4})", zip_file).group(1)
zip_rows = []
for r in csv.DictReader(open(zip_file, encoding="utf-8"), delimiter="\t"):
    if r["zcta"][:3] in ("006", "007", "008", "009", "969") or r["zcta"] == "96799":
        continue  # Puerto Rico, Guam, N. Marianas, American Samoa: no boundaries here
    zip_rows.append("%s\t%.4f\t%.4f" % (r["zcta"], float(r["lat"]), float(r["lon"])))

# Report how many places/ZIPs fall outside every diocese (should be very few: coastline points)
def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside

def _lookup(lat, lon):
    for d in dioceses:
        b = d["bbox"]
        if not (b[0] <= lon <= b[2] and b[1] <= lat <= b[3]):
            continue
        for poly in d["polys"]:
            if _in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]):
                return d["id"]
    return None

outside_places = [r.split("\t")[0] + ", " + r.split("\t")[1] for r in place_rows
                  if _lookup(float(r.split("\t")[3]), float(r.split("\t")[4])) is None]
outside_zips = [r.split("\t")[0] for r in zip_rows
                if _lookup(float(r.split("\t")[1]), float(r.split("\t")[2])) is None]

out = {
    "asOf": as_of,
    "dioceses": dioceses,
    "counties": dict(sorted(counties.items())),
    "states": states,
    "placeYear": place_year,
    "zipYear": zip_year,
    "places": "\n".join(place_rows),
    "zips": "\n".join(zip_rows),
}
with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as fh:
    fh.write("// Generated by build.py - do not edit by hand\n")
    fh.write("window.DIOCESE_DATA = ")
    json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    fh.write(";\n")

# --- single-file bundle (double-click to open, no server needed) ----------------
import base64
html = open(os.path.join(HERE, "app.html"), encoding="utf-8").read()
for fn in sorted(os.listdir(os.path.join(HERE, "fonts"))):
    if fn.endswith(".woff2"):
        b64 = base64.b64encode(open(os.path.join(HERE, "fonts", fn), "rb").read()).decode()
        html = html.replace(f'url("fonts/{fn}")', f'url("data:font/woff2;base64,{b64}")')
data_js = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
html = html.replace('<script src="data.js"></script>', "<script>\n" + data_js + "</script>")
bundle = os.path.join(HERE, "Diocese Finder.html")
open(bundle, "w", encoding="utf-8").write(html)

# --- web version (site/): same page plus manifest, icons and offline service worker ---
import hashlib, shutil
SITE = os.path.join(HERE, "docs")
os.makedirs(os.path.join(SITE, "icons"), exist_ok=True)
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(html)
h = hashlib.sha256(html.encode("utf-8"))
for fn in sorted(os.listdir(os.path.join(HERE, "icons"))) + ["../manifest.webmanifest"]:
    h.update(open(os.path.join(HERE, "icons", fn), "rb").read())
version = h.hexdigest()[:12]
sw = open(os.path.join(HERE, "sw.template.js"), encoding="utf-8").read().replace("__VERSION__", version)
open(os.path.join(SITE, "sw.js"), "w", encoding="utf-8").write(sw)
shutil.copy(os.path.join(HERE, "manifest.webmanifest"), SITE)
for fn in os.listdir(os.path.join(HERE, "icons")):
    shutil.copy(os.path.join(HERE, "icons", fn), os.path.join(SITE, "icons", fn))
open(os.path.join(SITE, ".nojekyll"), "w").close()
open(os.path.join(SITE, "CNAME"), "w").write("diocese.bobbyvogel.com\n")  # custom domain for GitHub Pages
print("web version written to docs/ (version %s)" % version)

print(f"bishops as of {as_of}: {len(bishops)} sees")
print("bundle: %s (%.0f KB)" % (os.path.basename(bundle), os.path.getsize(bundle) / 1024))
print(f"dioceses with boundaries: {len(dioceses)}")
print(f"places ({place_year} Census Gazetteer): {len(place_rows)} ({matched_pop} with population); outside every diocese: {len(outside_places)} {outside_places[:12]}")
print(f"ZIP codes ({zip_year} ZCTAs): {len(zip_rows)}; outside every diocese: {len(outside_zips)} {outside_zips[:20]}")
print("boundaries with NO bishop match:", missing or "none")
print("bishop rows with no boundary (expected: Military only):", unused)
print("data.js size: %.0f KB" % (os.path.getsize(os.path.join(HERE, "data.js")) / 1024))
if missing:
    sys.exit(1)
