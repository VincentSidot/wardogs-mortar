"""Depouillement d'une serie de calibration.

On tire depuis une position connue G avec un azimut A et une portee D
affiches sur la piece, et on releve l'impact I. Chaque tir donne :

    echelle mesuree   = D / distance_en_points(G -> I)
    decalage d'azimut = azimut_mesure(G -> I) - A

Trois tirs sur des azimuts separes permettent de distinguer une erreur
d'echelle (les trois echelles concordent, les decalages sont nuls) d'une
rotation (les decalages concordent, les echelles sont bonnes) d'une
anisotropie X/Y (l'echelle depend de l'azimut).

Usage : editer SHOTS puis  python calibrate.py
"""

import math
import statistics

import artillery

# Position de tir, identique pour toute la serie.
GUN = (96.45, 109.35)

# (azimut affiche, portee affichee en m, impact_x, impact_y)
# SPH-2, 2026-09-05, deux series sans deplacement depuis la meme position.
# Serie 1 : eventail d'azimuts a portee constante -> valide la convention.
# Serie 2 : balayage de portee sur deux azimuts   -> mesure le deficit.
SHOTS = [
    (170, 2000, 99.99, 90.96),
    (200, 2000, 89.71, 90.74),
    (230, 2000, 81.43, 96.89),
    (200, 1200, 92.75, 98.23),

    (200,  800, 94.10, 101.71),
    (200, 1400, 91.99,  96.16),
    (200, 2000, 90.01,  90.64),
    (200, 2600, 88.00,  85.86),
    (230,  800, 90.30, 104.25),
    (230, 1400, 85.87, 100.58),
    (230, 2000, 81.26,  96.96),
    (230, 2600, 77.06,  93.41),
]


def angle_diff(a, b):
    """Ecart signe de a vers b, ramene dans [-180, 180]."""
    return (a - b + 180) % 360 - 180


def main():
    if not SHOTS:
        print("Renseigne GUN et SHOTS avant de lancer le depouillement.")
        return

    print(f"Position de tir : {GUN[0]} / {GUN[1]}\n")
    header = f"{'az. tire':>9} {'portee':>7} {'impact':>15} {'az. mesure':>11} {'ecart az':>9} {'m/point':>9}"
    print(header)
    print("-" * len(header))

    scales, offsets = [], []
    for az, dist, ix, iy in SHOTS:
        # Mesure geometrique pure : 1 point = 1 unite de grille.
        s = artillery.solve(GUN, (ix, iy), meters_per_point=1.0)
        pts = s["distance_m"]
        if pts == 0:
            print(f"{az:>9} {dist:>7} {'impact = position':>15}  -- tir ignore")
            continue

        scale = dist / pts
        offset = angle_diff(s["azimuth_deg"], az)
        scales.append(scale)
        offsets.append(offset)
        print(f"{az:>9} {dist:>7} {ix:>7.2f}/{iy:<7.2f} {s['azimuth_deg']:>11.1f} "
              f"{offset:>+9.1f} {scale:>9.1f}")

    if len(scales) < 2:
        return

    print()
    print(f"echelle   : {statistics.mean(scales):.1f} m/point "
          f"(etendue {max(scales) - min(scales):.1f})")
    print(f"decalage  : {statistics.mean(offsets):+.1f} deg "
          f"(etendue {max(offsets) - min(offsets):.1f})")

    # Reference de bruit : deux tirs de meme azimut ne different que par la
    # dispersion. Sans cette reference, toute variation parait significative.
    noise = dispersion_baseline()
    if noise is not None:
        print(f"dispersion : {noise:.1f} m/point (tirs de meme azimut)")

    print()
    ax, ay = axis_scales()
    if ax and ay:
        gap = abs(statistics.mean(ax) - statistics.mean(ay))
        print(f"echelle sur X : {statistics.mean(ax):.1f}   "
              f"sur Y : {statistics.mean(ay):.1f}   ecart {gap:.1f}")
        if noise is not None and gap > 2 * noise:
            print("  -> X et Y n'ont pas le meme facteur.")
        else:
            print("  -> pas d'anisotropie : l'ecart entre axes reste dans le bruit.")

    if noise is not None and abs(statistics.mean(offsets)) > 1.0:
        print("Decalage d'azimut systematique : le nord de la piece n'est")
        print("pas le nord de la grille.")


def dispersion_baseline():
    """Etendue des echelles mesurees parmi les tirs partageant un azimut."""
    par_azimut = {}
    for az, dist, ix, iy in SHOTS:
        pts = artillery.solve(GUN, (ix, iy), meters_per_point=1.0)["distance_m"]
        if pts:
            par_azimut.setdefault(az, []).append(dist / pts)
    etendues = [max(v) - min(v) for v in par_azimut.values() if len(v) > 1]
    return statistics.mean(etendues) if etendues else None


def axis_scales():
    """Echelle deduite separement de la composante est et de la composante nord.

    Une composante trop faible est ecartee : diviser par un petit deplacement
    amplifie le bruit de lecture au point de rendre le chiffre inexploitable.
    """
    sx, sy = [], []
    for az, dist, ix, iy in SHOTS:
        de = dist * math.sin(math.radians(az))
        dn = dist * math.cos(math.radians(az))
        px, py = ix - GUN[0], iy - GUN[1]
        if abs(px) > 2:
            sx.append(de / px)
        if abs(py) > 2:
            sy.append(dn / py)
    return sx, sy


if __name__ == "__main__":
    main()
