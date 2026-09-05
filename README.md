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
- **Adjust from impacts.** Log where the round actually landed. The gun's bias
  is estimated as the *average* miss relative to what was aimed, so a single
  impact corrects fully and several smooth each other out instead of making
  the aim chase dispersion. Tracked per battery. Misses below the noise floor
  (±10 MOA dispersion + dial steps) are tagged as such.
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
~2625 m where the table flattens. Solutions flag all of these.

The game's firing tables assume gun and target at the same height: firing
uphill falls short, downhill carries long, and the error grows with range.
That is what the **terrain offset** toggle in Settings encodes — a curve
measured on 05/09 from x96/y109 firing south (−1.5 % at 2 km, −3.7 % at
2.6 km). It is only valid for that position, so it is **off by default**; the
right general tool is a ranging round followed by the impact log. Proper a
priori correction would need the map heightmaps, which this tool does not have.

Output is rounded to what is actually dialable: azimuth to the degree, range in
25 m steps. `python calibrate.py` re-runs the calibration analysis.

## Files

| | |
|---|---|
| `index.html` | the whole app — UI and maths |
| `artillery.py` | Python reference implementation, cross-checked against the page |
| `calibrate.py` | calibration series and its analysis |
| `app.py` | optional local server, not needed to use the page |
