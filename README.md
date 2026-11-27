# Diocese Finder

Finds which Latin-Church diocese a location is in and shows its Ordinary.
Everything (boundaries, bishops, towns, ZIP codes, fonts) is inside one file, so it works with no internet.

## Use it
Double-click **Diocese Finder.html**. Three ways to choose a place:
- **My location**: asks the Mac for its position. A Mac Studio has no GPS; macOS works out location from nearby Wi-Fi, which usually needs internet. Offline, use one of the other two.
- **Pick a place**: type a city, town, village, county or 5-digit ZIP code and choose from the list (e.g. `Rushville`, `Rushville, IN`, `Rush County`, `46173`). Fully offline. Towns use the Census point for the town; a few counties and ZIP codes straddle two dioceses, and the app says so.
- **Coordinates** (e.g. `39.6092, -85.4464`), or click anywhere on the map.

The last location you used is remembered and shown on the next launch.

**The map** moves and zooms. On a Mac: drag to move, pinch on the trackpad (or hold ⌘ and scroll) to zoom, double-click to zoom in. On a phone: two fingers move and pinch the map (one finger still scrolls the page). The + / − / ⊙ buttons zoom and re-center. Town names appear as you zoom in. Alaska, Hawaii and the Virgin Islands are shown in inset boxes, as on a printed map.

If your browser won't give location to a file opened from disk, double-click **start.command** instead (serves it at http://localhost:8765). Safari blocks this more often than Chrome does.

## On a phone
Open https://diocese.bobbyvogel.com once with a signal, then add it to the Home Screen (Safari: Share › Add to Home Screen). After that first visit it opens with no signal, and "My location" uses the phone's GPS, which works offline. The web version lives in `docs/` and is served by GitHub Pages.

## Update the town list
Towns come from the newest `source/YYYY_Gaz_place_national.txt` (Census Gazetteer "Places" file). This copy is the 2016 file. To use a newer one, download it from census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html, unzip it into `source/`, and run `python3 build.py`.

## Update the bishops
Bishops come from Wikipedia's *List of Catholic bishops in the United States*, saved on 23 Nov 2026 in `source/bishops_wikipedia_2026-11-23.tsv` (one row per see: province, see, ordinary, title; `Sede vacante` for vacant sees).
To update: edit that file (or save a newer `bishops_YYYY-MM-DD.tsv` beside it), then run `python3 build.py`. That rebuilds `Diocese Finder.html` and the web version in `docs/` (commit and push to publish; phones update the next time they open it online), and reports any see that fails to match a boundary.

## Sources and licences
- Diocese boundaries and the county table: Ken Burchfiel, github.com/kburchfiel/us_diocese_mapper. Code is MIT, maps are CC BY 4.0, and the county table is public domain. Boundaries are built from simplified Census county shapes, so they can be a few hundred metres off near an edge. The app warns you when you're within about 3 km of a boundary.
- Bishops: Wikipedia (CC BY-SA 4.0).
- Towns, villages and Census-designated places: U.S. Census Bureau Gazetteer, places, 2016 (public domain).
- ZIP codes: U.S. Census Bureau ZIP Code Tabulation Areas, 2022, via the `us-zips` package (MIT). ZIP points are the center of each ZIP area.
- Town populations (used only to list bigger towns first): GeoNames, via the `geonamescache` package (CC BY 4.0 / MIT).
- Font: EB Garamond (SIL Open Font License, `fonts/OFL-LICENSE.txt`).

## Not covered
Puerto Rico, Guam and the Northern Marianas; Eastern Catholic eparchies; the Archdiocese for the Military Services; the Personal Ordinariate of the Chair of St. Peter.
