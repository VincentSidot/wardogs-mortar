# Wardogs Mortar

v2.1.0 · 
Artillery fire-control calculator for War Dogs.
**<https://vincentsidot.github.io/wardogs-mortar/>**

Give it your battery positions and a target, it gives you the range and azimuth
to dial. Single static page, no server, works offline. English / French.

## What it does

- **Multiple batteries.** Every battery gets its own solution for the same
  target, side by side.
- **Fire missions.** Each target is a saved mission with its own shot log.
  Switch away and come back later, the corrections are still there.
- **Gun model.** Every logged impact feeds a model of the gun that fired:
  a range bias, a chassis tilt plane (error varying with azimuth) and an
  azimuth drift, fitted by regularised least squares over all its impacts
  across missions. A ranging round on one target therefore corrects every
  other target fired from the same position. On a synthetic gun with 15 mil of
  tilt and −18 m of bias, three ranging rounds bring the first-round miss on
  300 fresh targets from 38 m down to 16 m — the floor set by the 25 m / 1°
  dial steps. When the gun moves, add a new battery.
- **Dial dithering.** When the exact range falls between two 25 m steps the
  solution names both, so alternating them on fire-for-effect centres the
  mean impact on the target instead of carrying a half-step bias.
- **Reverse mode.** Enter what you actually dialled and see which coordinate
  that shot aims at. This is how you catch a stale battery position — on a
  self-propelled gun it changes the moment you drive.

## Conventions

X grows east, Y grows north, 1 grid point = 100 m, azimuth 0 = north clockwise.
Paste `x90.37, y44.35` into either coordinate field: the labels are recognised
and the order does not matter.

## Accuracy, arcs and terrain

Community measurements ([wardogshub](https://wardogshub.gg/blog/how-to-use-artillery-in-wardogs/))
put the SPH-2 at 10 MOA of dispersion (±3 m at 1 km, ±8 m at 2.6 km), a
780–2629 m envelope, high arc only below ~1181 m, and an arc turnover past
~2625 m where the table flattens. Solutions flag all of these, and show the
elevation in mils from the community firing table for cross-checking against
the in-game sight.

**Heights (ΔZ).** Optional, off by default. Loads the Bakurani heightfield
(2 m mesh, 0.5 MB chunks on demand) from
[wardogs-artillery.com](https://wardogs-artillery.com/) by Apollyon — thanks —
and shows target − battery height on each solution. Information only: on our
12 calibration shots the range deficit correlates with ΔZ (r = −0.68) but is
2–3× smaller than a flat-table model predicts, so the tool does not correct
automatically. Neither does the community calculator.

**Terrain offset.** A curve measured on 05/09 from x96/y109 firing south. Only
valid there; off by default. The general tool is a ranging round followed by
the impact log.

Output is rounded to what is actually dialable: azimuth to the degree, range in
25 m steps. `python calibrate.py` re-runs the calibration analysis.

## Files

| | |
|---|---|
| `index.html` | the whole app — UI and maths |
| `artillery.py` | Python reference implementation, cross-checked against the page |
| `calibrate.py` | calibration series and its analysis |
| `app.py` | optional local server, not needed to use the page |
