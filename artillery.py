"""Calculs de tir d'artillerie sur grille de carte.

Repere carte (Warno / War Dogs style) :
  - X croit vers l'est (droite), Y croit vers le nord (haut)
  - 1 point de grille = 100 m
  - azimut 0 = nord, sens horaire
"""

import math
import re

METERS_PER_POINT = 100.0


def solve(gun, target, meters_per_point=METERS_PER_POINT):
    """gun / target : (x, y) en points de grille. Renvoie la solution de tir."""
    gx, gy = gun
    tx, ty = target

    d_east = (tx - gx) * meters_per_point
    d_north = (ty - gy) * meters_per_point

    distance = math.hypot(d_east, d_north)
    azimuth = math.degrees(math.atan2(d_east, d_north)) % 360.0

    return {
        "distance_m": distance,
        "distance_pts": distance / meters_per_point,
        "azimuth_deg": azimuth,
        "azimuth_mils": azimuth * 6400.0 / 360.0,
        "d_east_m": d_east,
        "d_north_m": d_north,
        "cardinal": cardinal(azimuth),
    }


_CARDINALS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]


def cardinal(azimuth_deg):
    return _CARDINALS[int((azimuth_deg % 360.0) / 22.5 + 0.5) % 16]


_LABELLED = re.compile(r"([xy])\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)", re.IGNORECASE)


def parse_coord(text, y_first=False):
    """Lit une paire de coordonnees.

    Deux formes acceptees :
      - etiquetee : 'x90.37, y44.35' (l'ordre n'a pas d'importance)
      - positionnelle : '99.4 62.3', '99.4, 62.3', '99.4;62.3', '99.4/62.3'
        (ordre X puis Y, ou Y puis X si y_first)
    """
    if text is None:
        raise ValueError("coordonnee vide")

    found = {k.lower(): v.replace(",", ".") for k, v in _LABELLED.findall(text)}
    if "x" in found and "y" in found:
        return float(found["x"]), float(found["y"])

    cleaned = text
    for sep in ",;/|":
        cleaned = cleaned.replace(sep, " ")
    parts = cleaned.split()
    if len(parts) != 2:
        raise ValueError("format attendu : 'x90.37, y44.35' ou '90.37 44.35'")
    a, b = float(parts[0]), float(parts[1])
    return (b, a) if y_first else (a, b)


def adjust(gun, target, impact, meters_per_point=METERS_PER_POINT):
    """Reglage de tir : d'apres l'impact observe, corrige le point de visee.

    Si l'obus est tombe en I alors qu'on visait T, on vise desormais
    T' = T + (T - I), ce qui annule l'erreur systematique (echelle,
    declinaison, derive) sans avoir a l'identifier.
    """
    tx, ty = target
    ix, iy = impact
    aim = (2 * tx - ix, 2 * ty - iy)

    return {
        "offset": solve(impact, target, meters_per_point),  # de l'impact vers la cible
        "aim_point": {"x": aim[0], "y": aim[1]},
        "corrected": solve(gun, aim, meters_per_point),
        "original": solve(gun, target, meters_per_point),
    }


def project(gun, distance_m, azimuth_deg, meters_per_point=METERS_PER_POINT):
    """Mode inverse : ou tombe un obus tire a cette distance et cet azimut ?"""
    gx, gy = gun
    r = distance_m / meters_per_point
    a = math.radians(azimuth_deg)
    return {
        "x": gx + r * math.sin(a),
        "y": gy + r * math.cos(a),
        "distance_pts": r,
    }


# Courbe de correction balistique, mesuree sur SPH-2 le 2026-09-05.
# Deux series, 12 coups depuis une position fixe : la portee affichee sur la
# piece tombe systematiquement court, d'un deficit qui s'accelere avec la
# distance. Chaque entree est (portee au sol visee, facteur a appliquer).
RANGE_CALIBRATION = [
    (800, 1.0013),
    (1400, 1.0123),
    (2000, 1.0155),
    (2600, 1.0388),
]

# Au-dela, la piece sature : afficher plus n'allonge plus le tir.
EFFECTIVE_MAX_RANGE_M = 2500


def dial_range(ground_m, table=RANGE_CALIBRATION):
    """Portee a afficher sur la piece pour toucher a `ground_m` au sol.

    Interpolation lineaire entre les points mesures, extrapolation plate
    au-dela des bornes : hors du domaine calibre, mieux vaut ne rien inventer.
    """
    if ground_m <= table[0][0]:
        return ground_m * table[0][1]
    if ground_m >= table[-1][0]:
        return ground_m * table[-1][1]

    for (r0, f0), (r1, f1) in zip(table, table[1:]):
        if r0 <= ground_m <= r1:
            t = (ground_m - r0) / (r1 - r0)
            return ground_m * (f0 + t * (f1 - f0))
    return ground_m


# Resolution de reglage de la piece, mesuree sur le viseur SPH-2 :
# l'azimut se compose au degre, et un cran de 10 mils vaut 24 a 30 m de portee.
DIAL_AZIMUTH_STEP_DEG = 1
DIAL_RANGE_STEP_M = 25


def dialable(ground_m, azimuth_deg):
    """Traduit une solution exacte en valeurs reellement composables.

    Renvoie ce qu'il faut afficher sur la piece, et le cout en metres de
    chaque arrondi : au-dela de 2 km, l'arrondi de l'azimut au degre pese
    plus lourd que la correction balistique.
    """
    exact_range = dial_range(ground_m)
    # Arrondi au demi superieur, comme Math.round en JavaScript : les deux
    # implementations doivent donner le meme cran, y compris sur les .5 exacts
    # que l'arrondi bancaire de Python trancherait dans l'autre sens.
    range_dialed = math.floor(exact_range / DIAL_RANGE_STEP_M + 0.5) * DIAL_RANGE_STEP_M
    az_dialed = math.floor(azimuth_deg / DIAL_AZIMUTH_STEP_DEG + 0.5) * DIAL_AZIMUTH_STEP_DEG % 360

    return {
        "range_dialed": range_dialed,
        "range_exact": exact_range,
        "range_loss_m": abs(range_dialed - exact_range),
        "azimuth_dialed": az_dialed,
        "azimuth_loss_m": abs(math.radians(azimuth_deg - az_dialed)) * ground_m,
        # Un demi-pas d'azimut, le pire cas de l'arrondi, en metres au sol.
        "azimuth_step_m": math.radians(DIAL_AZIMUTH_STEP_DEG / 2) * ground_m,
        "correction_below_step": abs(exact_range - ground_m) < DIAL_RANGE_STEP_M / 2,
    }
