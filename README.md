# Wardogs Mortar

Artillery fire-control calculator for War Dogs.
**<https://vincentsidot.github.io/wardogs-mortar/>**

Give it your battery positions and a target, it gives you the range and azimuth
to dial. Single static page, no server, works offline. English / French.

## What it does

- **Multiple batteries.** Every battery gets its own solution for the same
  target, side by side.
- **Fire missions.** Each target is a saved mission with its own shot log.
  Switch away and come back later, the corrections are still there.
- **Adjust from impacts.** Log where the round actually landed; the aim point
  shifts by (target − impact) and corrections accumulate. Tracked per battery,
  since two guns have no reason to drift the same way.
- **Reverse mode.** Enter what you actually dialled and see which coordinate
  that shot aims at. This is how you catch a stale battery position — on a
  self-propelled gun it changes the moment you drive.

## Conventions

X grows east, Y grows north, 1 grid point = 100 m, azimuth 0 = north clockwise.
Paste `x90.37, y44.35` into either coordinate field: the labels are recognised
and the order does not matter.

## Calibration

Output is corrected from 12 measured shots (SPH-2): rounds fall short,
increasingly so with distance — nil at 800 m, −1.5 % at 2 km, −3.7 % at 2.6 km,
with the gun saturating past ~2500 m. Azimuth showed no systematic offset.
Values are rounded to what is actually dialable: azimuth to the degree, range in
25 m steps.

Re-run `python calibrate.py` after adding shots to `SHOTS` to redo the analysis.

## Files

| | |
|---|---|
| `index.html` | the whole app — UI and maths |
| `artillery.py` | Python reference implementation, cross-checked against the page |
| `calibrate.py` | calibration series and its analysis |
| `app.py` | optional local server, not needed to use the page |
