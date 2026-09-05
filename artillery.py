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
