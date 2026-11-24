# Diocese Finder

Finds which Latin-Church diocese a location is in and shows its Ordinary.
Everything (boundaries, bishops, fonts) is inside one file, so it works with no internet.

## Use it
Double-click **Diocese Finder.html**. Three ways to choose a place:
- **My location**: asks the Mac for its position. A Mac Studio has no GPS; macOS works out location from nearby Wi-Fi, which usually needs internet. Offline, use one of the other two.
- **Pick a county**: state, then county. Fully offline. A few counties are split between two dioceses; the app says so.
- **Coordinates** (e.g. `39.6092, -85.4464`), or click anywhere on the map.

The last location you used is remembered and shown on the next launch.

If your browser won't give location to a file opened from disk, double-click **start.command** instead (serves it at http://localhost:8765). Safari blocks this more often than Chrome does.

## On a phone
Open https://diocese.bobbyvogel.com once with a signal, then add it to the Home Screen (Safari: Share › Add to Home Screen). After that first visit it opens with no signal, and "My location" uses the phone's GPS, which works offline. The web version lives in `docs/` and is served by GitHub Pages.

## Update the bishops
Bishops come from Wikipedia's *List of Catholic bishops in the United States*, saved on 23 Nov 2026 in `source/bishops_wikipedia_2026-11-23.tsv` (one row per see: province, see, ordinary, title; `Sede vacante` for vacant sees).
To update: edit that file (or save a newer `bishops_YYYY-MM-DD.tsv` beside it), then run `python3 build.py`. That rebuilds `Diocese Finder.html` and the web version in `docs/` (commit and push to publish; phones update the next time they open it online), and reports any see that fails to match a boundary.

## Sources and licences
- Diocese boundaries and the county table: Ken Burchfiel, github.com/kburchfiel/us_diocese_mapper. Code is MIT, maps are CC BY 4.0, and the county table is public domain. Boundaries are built from simplified Census county shapes, so they can be a few hundred metres off near an edge. The app warns you when you're within about 3 km of a boundary.
- Bishops: Wikipedia (CC BY-SA 4.0).
- Font: EB Garamond (SIL Open Font License, `fonts/OFL-LICENSE.txt`).

## Not covered
Puerto Rico, Guam and the Northern Marianas; Eastern Catholic eparchies; the Archdiocese for the Military Services; the Personal Ordinariate of the Chair of St. Peter.
