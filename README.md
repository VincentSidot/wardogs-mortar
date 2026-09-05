# Calcul artillerie (War Dogs)

Calculateur de tir : tu donnes la position de la piece et celle de la cible en
coordonnees de grille, la page renvoie **distance** et **azimut**.

La page est **autonome** : tout le calcul se fait en JavaScript, aucun serveur
n'est necessaire. Double-clic sur `index.html`, ou hebergement statique
(GitHub Pages), ou ouverture sur le telephone comme second ecran.

## Conventions

- X croit vers l'est, Y croit vers le nord (comme les graduations de la carte).
- 1 point de grille = 100 m (modifiable via "metres / point").
- Azimut 0 = nord, sens horaire. Affiche aussi en mils OTAN (6400), a reporter
  sur le compas en haut du viseur ; la distance se reporte sur l'echelle RNG.

## Calibration

La page ne sort pas la distance geometrique mais **la valeur a composer sur la
piece**, corrigee de deux choses mesurees sur le terrain (12 coups, SPH-2,
voir `calibrate.py`) :

- **Deficit de portee.** Les obus tombent court, d'un ecart qui s'accelere avec
  la distance : nul a 800 m, -1,2 % a 1400 m, -1,5 % a 2000 m, -3,7 % a 2600 m.
- **Saturation.** Au-dela de ~2500 m au sol, afficher plus n'allonge plus le
  tir ; la page le signale.

Les valeurs sont arrondies a ce qui est reellement reglable : azimut au degre,
portee par crans de 25 m (un cran de 10 mils vaut 24 a 30 m sur le viseur).
Le sous-titre rappelle ce que coute 1 degre d'ecart a la portee courante --
au-dela de 2 km, cet arrondi pese plus lourd que la correction balistique.

En revanche l'azimut n'a **aucun** decalage systematique : sur 12 coups,
moyenne -0,5 deg sans signe constant. La convention de la grille est exacte.

## Les trois outils

**Solution de tir.** Position batterie (memorisee entre les sessions) + cible
-> portee a composer et azimut. Les cibles s'empilent dans une liste ; un clic
sur une ligne la remet en grand et sur la rose des vents.

**Reglage sur impact observe.** L'obus est tombe a cote : entre les coordonnees
de l'impact, la page vise `T + (T - I)` et sort la solution corrigee. Ca annule
l'erreur systematique sans avoir a en identifier la cause. Au-dela de 1,5 km
d'ecart, un avertissement s'affiche : c'est en general une coordonnee mal
relevee, pas une derive.

**Mode inverse.** Entre la distance et l'azimut reellement affiches sur la
piece : la page dit quelle coordonnee ce tir vise. C'est le test qui detecte
une position batterie perimee -- sur un automoteur (SPH-2) elle change des que
le vehicule bouge, et c'est la premiere cause d'ecart.

## Saisie

Colle `x90.37, y44.35` dans n'importe lequel des deux champs : les etiquettes
x/y sont reconnues et l'ordre n'a pas d'importance. Sans etiquette,
`90.37 44.35` suit l'ordre affiche, que le bouton **Ordre de saisie** bascule
entre `X puis Y` et `Y puis X`.

## Hebergement sur GitHub Pages

Depot : <https://github.com/VincentSidot/wardogs-mortar>

Activation (une seule fois) : **Settings -> Pages -> Source: Deploy from a
branch**, branche `main`, dossier `/ (root)`. La page sort sur
<https://vincentsidot.github.io/wardogs-mortar/> apres une minute ou deux.

Le depot doit etre public pour Pages sur un compte gratuit.

Ensuite, chaque mise a jour se deploie toute seule :

    git add -A && git commit -m "..." && git push

## Fichiers

- `index.html` : l'application complete (interface + moteur de calcul JS).
- `artillery.py` : implementation Python de reference (`solve`, `adjust`,
  `project`, `parse_coord`). Sert a recouper le moteur JS.
- `app.py` : serveur local optionnel, expose `/api/solve`, `/api/adjust`,
  `/api/project`. Non necessaire pour utiliser la page.
- `start.bat` : lance le serveur local.
