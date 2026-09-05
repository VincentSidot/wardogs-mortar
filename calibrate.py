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
GUN = (0.0, 0.0)

# (azimut affiche, portee affichee en m, impact_x, impact_y)
SHOTS = [
    # (0,   2000, 0.0, 0.0),
    # (90,  2000, 0.0, 0.0),
    # (180, 2000, 0.0, 0.0),
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

    print()
    if len(scales) >= 2:
        print(f"echelle   : {statistics.mean(scales):.1f} m/point "
              f"(dispersion {max(scales) - min(scales):.1f})")
        print(f"decalage  : {statistics.mean(offsets):+.1f} deg "
              f"(dispersion {max(offsets) - min(offsets):.1f})")
        print()
        if max(scales) - min(scales) > 0.05 * statistics.mean(scales):
            print("L'echelle varie selon l'azimut : X et Y n'ont pas le meme")
            print("facteur, ou la portee affichee n'est pas la distance au sol.")
        if abs(statistics.mean(offsets)) > 1.0:
            print("Decalage d'azimut systematique : le nord de la piece n'est")
            print("pas le nord de la grille.")


if __name__ == "__main__":
    main()
