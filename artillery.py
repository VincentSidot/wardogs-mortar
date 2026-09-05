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


def aim_after(target, shots):
    """Point de visee apres une suite d'impacts observes (reglage amorti).

    Chaque tir est (impact, point_vise) : le biais de la piece est estime par
    la moyenne des ecarts impact - point vise, et la visee vaut cible - biais.
    Un seul impact corrige a fond ; plusieurs se lissent au lieu de faire
    osciller la visee au rythme de la dispersion. Les tirs passes ici doivent
    tous provenir de la meme piece.
    """
    tx, ty = target
    if not shots:
        return (tx, ty)
    bx = sum(ix - ax for (ix, iy), (ax, ay) in shots) / len(shots)
    by = sum(iy - ay for (ix, iy), (ax, ay) in shots) / len(shots)
    return (tx - bx, ty - by)


def log_shots(target, impacts):
    """Rejoue une sequence d'impacts comme le ferait la page : le point vise
    de chaque tir est celui en vigueur au moment ou il a ete enregistre."""
    shots = []
    for impact in impacts:
        shots.append((tuple(impact), aim_after(target, shots)))
    return shots


def adjust(gun, target, impacts, meters_per_point=METERS_PER_POINT):
    """Solution corrigee d'apres les impacts observes, dans l'ordre."""
    if impacts and not isinstance(impacts[0], (tuple, list)):
        impacts = [impacts]          # tolere un impact unique
    shots = log_shots(target, impacts)
    aim = aim_after(target, shots)
    last = impacts[-1] if impacts else target

    return {
        "offset": solve(last, target, meters_per_point),
        "aim_point": {"x": aim[0], "y": aim[1]},
        "corrected": solve(gun, aim, meters_per_point),
        "original": solve(gun, target, meters_per_point),
        "shots": len(impacts),
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


# Offset terrain mesure sur SPH-2 le 2026-09-05 : 12 coups depuis x96/y109
# vers le sud, portee systematiquement courte, deficit croissant avec la
# distance. Les tables du jeu supposent gun et cible a la meme altitude ; ce
# deficit est tres probablement la pente, pas le canon. La courbe n'est donc
# valable que pour cette position, et la page la laisse desactivee par defaut.
# Chaque entree est (portee au sol visee, facteur a appliquer).
RANGE_CALIBRATION = [
    (800, 1.0013),
    (1400, 1.0123),
    (2000, 1.0155),
    (2600, 1.0388),
]

# Enveloppe du SPH-2 d'apres les mesures communautaires (wardogshub) :
# arc haut seul sous 1181 m, bascule de l'arc vers 2625 m.
SPH2_MIN_RANGE_M = 780
SPH2_LOW_ARC_FROM_M = 1181
SPH2_MAX_RANGE_M = 2629
SPH2_NEAR_MAX_FROM_M = 2550
DISPERSION_MOA = 10


def dispersion_m(ground_m):
    """Rayon de dispersion de la piece a cette portee (10 MOA)."""
    return ground_m * (DISPERSION_MOA / 60) * math.pi / 180


def range_status(ground_m):
    if ground_m < SPH2_MIN_RANGE_M:
        return "tooClose"
    if ground_m > SPH2_MAX_RANGE_M:
        return "outOfRange"
    if ground_m > SPH2_NEAR_MAX_FROM_M:
        return "nearMax"
    if ground_m < SPH2_LOW_ARC_FROM_M:
        return "highArcOnly"
    return "ok"


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


def dialable(ground_m, azimuth_deg, use_curve=False):
    """Traduit une solution exacte en valeurs reellement composables.

    Renvoie ce qu'il faut afficher sur la piece, et le cout en metres de
    chaque arrondi : au-dela de 2 km, l'arrondi de l'azimut au degre pese
    plus lourd que l'offset terrain, lui-meme optionnel.
    """
    exact_range = dial_range(ground_m) if use_curve else ground_m
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


# ---------------------------------------------------------------------------
# Modele de piece : les causes d'erreur appartiennent a la position de la piece
# (inclinaison du chassis, biais de vitesse ou de table, decalage d'azimut),
# pas a la cible. On les apprend sur tous les impacts d'une batterie et on les
# applique a toute cible tiree depuis la meme position. Miroir de index.html.
#
#   erreur de portee  = c + s(D) * (alpha*cos A + beta*sin A)
#   erreur laterale   = D * (delta + kappa_s*sin A + kappa_c*cos A)   (devers du chassis)
MODEL_PRIOR = {"sigma_r": 12.0, "sigma_l": 12.0, "tau_c": 40.0, "tau_tilt": 20.0,
               "tau_delta": math.pi / 180, "tau_cant": 2.5 * math.pi / 180}

# Table communautaire (wardogs-artillery.com), arc haut : (portee m, mil).
SPH2_HIGH = sorted([
    [735, 1400], [780, 1390], [825, 1380], [869, 1370], [913, 1360], [956, 1350], [999,
    1340], [1041, 1330], [1083, 1320], [1124, 1310], [1165, 1300], [1205, 1290], [1245,
    1280], [1285, 1270], [1324, 1260], [1363, 1250], [1401, 1240], [1438, 1230], [1475,
    1220], [1512, 1210], [1547, 1200], [1582, 1190], [1616, 1180], [1650, 1170], [1684,
    1160], [1717, 1150], [1750, 1140], [1782, 1130], [1813, 1120], [1844, 1110], [1875,
    1100], [1905, 1090], [1934, 1080], [1963, 1070], [1991, 1060], [2019, 1050], [2046,
    1040], [2072, 1030], [2098, 1020], [2123, 1010], [2147, 1000], [2171, 990], [2194,
    980], [2217, 970], [2239, 960], [2261, 950], [2282, 940], [2303, 930], [2323, 920],
    [2342, 910], [2360, 900], [2378, 890], [2395, 880], [2412, 870], [2429, 860], [2444,
    850], [2460, 840], [2474, 830], [2488, 820], [2501, 810], [2513, 800], [2524, 790],
    [2536, 780], [2546, 770], [2557, 760], [2567, 750], [2576, 740], [2584, 730], [2592,
    720], [2599, 710], [2604, 700], [2609, 690], [2613, 680], [2617, 670], [2621, 660],
    [2624, 650], [2626, 640], [2628, 630], [2629, 610], [2629, 620],
])


def range_slope_m_per_mil(ground_m, table=SPH2_HIGH):
    """Sensibilite de la portee a l'elevation (m/mil) autour de ground_m."""
    bi = 0
    for i in range(len(table) - 1):
        if table[i][0] <= ground_m <= table[i + 1][0]:
            bi = i
            break
        if abs(table[i][0] - ground_m) < abs(table[bi][0] - ground_m):
            bi = i
    r0, m0 = table[bi]
    r1, m1 = table[min(bi + 1, len(table) - 1)]
    return 0.0 if m1 == m0 else (r1 - r0) / (m1 - m0)


def _solve3(n, v):
    a = [row[:] for row in n]
    b = v[:]
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        b[i], b[p] = b[p], b[i]
        for r in range(i + 1, 3):
            f = a[r][i] / a[i][i]
            for c in range(i, 3):
                a[r][c] -= f * a[i][c]
            b[r] -= f * b[i]
    x = [0.0, 0.0, 0.0]
    for i in (2, 1, 0):
        acc = b[i] - sum(a[i][c] * x[c] for c in range(i + 1, 3))
        x[i] = acc / a[i][i]
    return x


def fit_battery(gun, shots, meters_per_point=METERS_PER_POINT, prior=MODEL_PRIOR):
    """Ajuste le modele de piece. shots : liste de ((impact_x, impact_y), (aim_x, aim_y))."""
    rows = []
    for (ix, iy), (ax, ay) in shots:
        intended = solve(gun, (ax, ay), meters_per_point)
        measured = solve(gun, (ix, iy), meters_per_point)
        d = intended["distance_m"]
        a = math.radians(intended["azimuth_deg"])
        da = (measured["azimuth_deg"] - intended["azimuth_deg"] + 540) % 360 - 180
        rows.append((d, a, measured["distance_m"] - d, d * math.radians(da), range_slope_m_per_mil(d)))

    p = prior
    n_mat = [[1 / p["tau_c"] ** 2, 0, 0], [0, 1 / p["tau_tilt"] ** 2, 0], [0, 0, 1 / p["tau_tilt"] ** 2]]
    v = [0.0, 0.0, 0.0]
    w = 1 / p["sigma_r"] ** 2
    for d, a, er, el, sl in rows:
        x = [1.0, sl * math.cos(a), sl * math.sin(a)]
        for i in range(3):
            v[i] += w * x[i] * er
            for j in range(3):
                n_mat[i][j] += w * x[i] * x[j]
    c, alpha, beta = _solve3(n_mat, v) if rows else (0.0, 0.0, 0.0)

    nl = [[1 / p["tau_delta"] ** 2, 0, 0], [0, 1 / p["tau_cant"] ** 2, 0], [0, 0, 1 / p["tau_cant"] ** 2]]
    vl = [0.0, 0.0, 0.0]
    wl = 1 / p["sigma_l"] ** 2
    for d, a, er, el, sl in rows:
        x = [d, d * math.sin(a), d * math.cos(a)]
        for i in range(3):
            vl[i] += wl * x[i] * el
            for j in range(3):
                nl[i][j] += wl * x[i] * x[j]
    delta, kappa_s, kappa_c = _solve3(nl, vl) if rows else (0.0, 0.0, 0.0)

    ss = 0.0
    for d, a, er, el, sl in rows:
        pr = c + sl * (alpha * math.cos(a) + beta * math.sin(a))
        pl = d * (delta + kappa_s * math.sin(a) + kappa_c * math.cos(a))
        ss += (er - pr) ** 2 + (el - pl) ** 2
    return {"n": len(rows), "c": c, "alpha": alpha, "beta": beta, "delta": delta,
            "kappa_s": kappa_s, "kappa_c": kappa_c,
            "rms": math.sqrt(ss / (2 * len(rows))) if rows else 0.0}


def aim_with_model(gun, target, model, meters_per_point=METERS_PER_POINT):
    """Point de visee tel que le tir, entache de l'erreur predite, tombe sur la cible."""
    if not model or not model["n"]:
        return tuple(target)
    want = solve(gun, target, meters_per_point)
    d, a = want["distance_m"], want["azimuth_deg"]
    for _ in range(3):
        ar = math.radians(a)
        er = model["c"] + range_slope_m_per_mil(d) * (model["alpha"] * math.cos(ar) + model["beta"] * math.sin(ar))
        el = d * (model["delta"] + model["kappa_s"] * math.sin(ar) + model["kappa_c"] * math.cos(ar))
        d = want["distance_m"] - er
        a = want["azimuth_deg"] - math.degrees(el / want["distance_m"])
    pt = project(gun, d, a, meters_per_point)
    return (pt["x"], pt["y"])
