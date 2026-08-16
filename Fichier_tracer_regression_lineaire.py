"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          RÉGRESSION LINÉAIRE  —  Présentation professionnelle               ║
║                                                                              ║
║  ► Toutes les valeurs à personnaliser sont dans la section 1 (CONFIGURATION)║
║    Les autres sections n'ont pas besoin d'être modifiées.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from scipy.stats import t

# ══════════════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION  ← TOUT CE QUE VOUS DEVEZ MODIFIER EST ICI
# ══════════════════════════════════════════════════════════════════════════════

# ── 1a. VOS DONNÉES ──────────────────────────────────────────────────────────
#   Remplacez ces listes par vos vraies valeurs.
#   Les deux listes doivent avoir la même longueur.

X_DATA = [0.8, 2.0, 3.0, 4.0]

Y_DATA = [0.1152,0.2761, 0.3783, 0.5003]

# Incertitude sur chaque point (même longueur que X_DATA et Y_DATA)

ERREURS_X = np.array([0.0054, 0.0087, 0.012, 0.015])
ERREURS_Y = np.array([0.0033,0.0095, 0.014, 0.0048])

u_X = [0.0054, 0.0087, 0.012, 0.015]
# ── 1b. TEXTES ET ÉTIQUETTES ─────────────────────────────────────────────────

TITRE_GRAPHIQUE = "Dosage par étalonnage du rhodamine B"

LABEL_X_PRINCIPAL = "Concentration (10⁻³ g / L)"       # axe X du graphique principal
LABEL_Y_PRINCIPAL = "Absorbance"          # axe Y du graphique principal
LABEL_X_RESIDUS   = "Concentration (10⁻³ g / L)"        # axe X du panneau résidus (souvent identique)
LABEL_Y_RESIDUS   = "Résidus"                 # axe Y du panneau résidus
TITRE_RESIDUS = "Résidus de la régression linéaire"  # titre du panneau résidus

LABEL_POINTS      = "Données observées"       # légende des points
LABEL_DROITE      = "Droite de régression"    # légende de la droite (équation ajoutée auto.)
ALPHA = 0.05      # 0.05 → 95 %  |  0.01 → 99 %  |  0.10 → 90 %

# ── 1d. APPARENCE ─────────────────────────────────────────────────────────────
FOND_SOMBRE = False   # True = fond noir (slides sombres) | False = fond blanc (rapport)

COULEURS = {
    # fond sombre
    "sombre": {
        "figure_bg":  "#0F1117",
        "axes_bg":    "#171B26",
        "axes_edge":  "#2E3347",
        "texte":      "#CDD6F4",
        "grille":     "#2E3347",
        "tick":       "#7C849B",
        "point":      "#89B4FA",   # bleu
        "droite":     "#CBA6F7",   # mauve
        "ci":         "#CBA6F7",   # bande IC (même couleur, alpha réduit)
        "pi":         "#89B4FA",   # bande IP
        "residu":     "#89DCEB",   # cyan
        "zero":       "#F38BA8",   # rose-rouge
        "sigma":      "#A6E3A1",   # vert
        "box_bg":     "#1E2235",
    },
    # fond clair
    "clair": {
        "figure_bg":  "white",
        "axes_bg":    "#F8F9FB",
        "axes_edge":  "#CCCCCC",
        "texte":      "#1A1A2E",
        "grille":     "#E0E0E0",
        "tick":       "#555555",
        "point":      "#2563EB",   # bleu
        "droite":     "#7C3AED",   # violet
        "ci":         "#7C3AED",
        "pi":         "#2563EB",
        "residu":     "#0891B2",   # cyan foncé
        "zero":       "#DC2626",   # rouge
        "sigma":      "#16A34A",   # vert
        "box_bg":     "#EEF2FF",
    },
}

# ── 1e. TAILLE ET RÉSOLUTION ──────────────────────────────────────────────────
TAILLE_FIGURE = (11, 8)    # largeur, hauteur en pouces
DPI_SAUVEGARDE = 180       # 180 pour écran, 300 pour impression

# ── 1f. FICHIER DE SORTIE ─────────────────────────────────────────────────────
FICHIER_SORTIE = "regression_belle.png"   # extension : .png  .pdf  .svg

# ══════════════════════════════════════════════════════════════════════════════
# 2. CALCULS  (ne pas modifier)
# ══════════════════════════════════════════════════════════════════════════════

x = np.array(X_DATA, dtype=float)
y = np.array(Y_DATA, dtype=float)
n = len(x)

slope, intercept, r, p_val, _ = stats.linregress(x, y)
r2 = r ** 2

x_fit  = np.linspace(0, 5, 400)
y_fit  = slope * x_fit + intercept
y_pred = slope * x + intercept
residus = y - y_pred

dof    = n - 2
t_crit = t.ppf(1 - ALPHA / 2, dof)
s_res  = np.sqrt(np.sum(residus ** 2) / dof)
x_mean = x.mean()
ss_x   = np.sum((x - x_mean) ** 2)

niveau_confiance = int((1 - ALPHA) * 100)

# ── Monte Carlo sur les coefficients ──────────────────────────────────────────
N = 10000   # nombre d'itérations (augmentez pour plus de précision)

a_sim, b_sim = [], []

for i in range(N):
    X_sim = np.random.normal(X_DATA, ERREURS_X)
    Y_sim = np.random.normal(Y_DATA, ERREURS_Y)
    RL = np.polyfit(X_sim, Y_sim, 1)
    a_sim.append(RL[0])
    b_sim.append(RL[1])
    
u_a = np.std(a_sim, ddof = 1)
u_b = np.std(b_sim, ddof = 1)



# ══════════════════════════════════════════════════════════════════════════════
# 3. STYLE MATPLOTLIB  (ne pas modifier)
# ══════════════════════════════════════════════════════════════════════════════

C = COULEURS["sombre"] if FOND_SOMBRE else COULEURS["clair"]

plt.rcParams.update({
    "figure.facecolor":  C["figure_bg"],
    "axes.facecolor":    C["axes_bg"],
    "axes.edgecolor":    C["axes_edge"],
    "axes.labelcolor":   C["texte"],
    "axes.titlecolor":   C["texte"],
    "axes.grid":         True,
    "grid.color":        C["grille"],
    "grid.linewidth":    0.6,
    "xtick.color":       C["tick"],
    "ytick.color":       C["tick"],
    "text.color":        C["texte"],
    "font.family":       "sans-serif",
    "font.size":         11,
    "axes.titlesize":    14,
    "axes.labelsize":    20,
    "legend.framealpha": 0.15,
    "legend.edgecolor":  C["axes_edge"],
})

# ══════════════════════════════════════════════════════════════════════════════
# 4. FIGURE  (ne pas modifier)
# ══════════════════════════════════════════════════════════════════════════════

fig, ax_main = plt.subplots(figsize=TAILLE_FIGURE, constrained_layout=True)

# ── Axe principal ─────────────────────────────────────────────────────────────

# u_a = 0.0028
# slope = 0.1284
# intercept = 0
r2 = 0.998
x_fit  = np.linspace(0, 5, 400)
y_fit  = slope * x_fit + intercept

signe = "+" if intercept >= 0 else "−"
ax_main.plot(x_fit, y_fit, color=C["droite"], lw=2.2, zorder=5,
             label=f"{LABEL_DROITE}  ($y = {slope:.4f}x {signe} {abs(intercept):.4f}$)")

ax_main.errorbar(x, y, xerr=2*ERREURS_X, yerr=2*ERREURS_Y, fmt='o', color=C["point"],
                 ecolor=C["point"], elinewidth=1.5, capsize=4,
                 alpha=0.85, zorder=6, label=LABEL_POINTS)
stats_txt = (
    f"$a = {slope:.4f} \\pm {u_a:.4f}$\n"
    f"$b = {intercept:.4f} \\pm {u_b:.4f}$\n"
    f"$R^2 = {r2:.3f}$\n"
    )

ax_main.text(0.02, 0.6, stats_txt,
             transform=ax_main.transAxes,
             va="top", ha="left", fontsize=20,
             color=C["texte"],
             bbox=dict(boxstyle="round,pad=0.55",
                       facecolor=C["box_bg"],
                       edgecolor=C["axes_edge"],
                       alpha=0.92))

ax_main.set_xlabel(LABEL_X_PRINCIPAL)
ax_main.set_ylabel(LABEL_Y_PRINCIPAL)
ax_main.set_title(TITRE_GRAPHIQUE, pad=10, fontweight="semibold", fontsize=20)
ax_main.legend(loc="upper left", fontsize=20)
ax_main.set_xlim(0, 5)


# -- Residus ---

residuals = y - (slope * x + intercept)
plt.figure(figsize=(12, 9))
plt.errorbar(x, residuals, xerr=2*ERREURS_X, yerr=2*ERREURS_Y, fmt='o', color=C["residu"],
             ecolor=C["residu"], elinewidth=1.5, capsize=4, alpha=0.85, zorder=6)
plt.axhline(0, color=C["zero"], lw=1.5, ls="--", zorder=4)
plt.xlabel(LABEL_X_RESIDUS) 
plt.ylabel(LABEL_Y_RESIDUS)
plt.title(TITRE_RESIDUS, pad=10, fontweight="semibold", fontsize=20)

# ── Sauvegarde ────────────────────────────────────────────────────────────────

fig.savefig(FICHIER_SORTIE,
            dpi=DPI_SAUVEGARDE,
            bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.show()
print(f"✅  Graphique enregistré → {FICHIER_SORTIE}")
