"""
============================================================
ANALYSE SPECTROSCOPIQUE PAR RÉSEAU DE DIFFRACTION
============================================================
Objectif : Exploiter une photo prise au smartphone à travers
un papier de diffraction (CD/DVD ou réseau holographique) pour
extraire le spectre d'intensité et d'absorbance en fonction de
la longueur d'onde.

Pipeline :
  1. Chargement et visualisation de l'image
  2. Sélection de la bande spectrale (ROI)
  3. Extraction du profil d'intensité brut
  4. Calibration pixel → longueur d'onde (lasers de référence)
  5. Correction de fond (background) et normalisation
  6. Calcul de l'absorbance = -log10(I/I₀)
  7. Sauvegarde des résultats (CSV + figures)

Dépendances : numpy, scipy, matplotlib, opencv-python, Pillow
    pip install numpy scipy matplotlib opencv-python Pillow
============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import RectangleSelector, Button
import cv2
from PIL import Image
from scipy.signal import savgol_filter, find_peaks
from scipy.optimize import curve_fit
import csv
import os
import sys

# ─────────────────────────────────────────────────────────
# 1. CHARGEMENT DE L'IMAGE
# ─────────────────────────────────────────────────────────

def charger_image(chemin_fichier):
    """
    Charge l'image depuis le disque et la convertit en tableaux numpy.
    Retourne l'image BGR (OpenCV) et RGB (matplotlib).
    """
    if not os.path.exists(chemin_fichier):
        raise FileNotFoundError(f"Image introuvable : {chemin_fichier}")

    img_bgr = cv2.imread(chemin_fichier)          # OpenCV lit en BGR
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)  # type: ignore # Conversion RGB

    print(f"[✓] Image chargée : {chemin_fichier}")
    print(f"    Dimensions : {img_rgb.shape[1]} × {img_rgb.shape[0]} pixels")
    return img_bgr, img_rgb


# ─────────────────────────────────────────────────────────
# 2. SÉLECTION INTERACTIVE DE LA ROI (Region Of Interest)
# ─────────────────────────────────────────────────────────

class SelecteurROI:
    """
    Outil interactif pour délimiter à la souris la bande spectrale
    sur l'image (le spectre horizontal issu du réseau de diffraction).
    """
    def __init__(self, img_rgb):
        self.img = img_rgb
        self.roi = None          # (x1, y1, x2, y2) en pixels
        self.confirme = False

    def selectionner(self):
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(self.img)
        ax.set_title("Tracez un rectangle autour de la bande spectrale\n"
                     "puis fermez la fenêtre.", fontsize=11)

        def on_select(eclick, erelease):
            x1, y1 = int(eclick.xdata), int(eclick.ydata)
            x2, y2 = int(erelease.xdata), int(erelease.ydata)
            self.roi = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
            print(f"[ROI] x1={self.roi[0]}, y1={self.roi[1]}, "
                  f"x2={self.roi[2]}, y2={self.roi[3]}")

        rs = RectangleSelector(ax, on_select, useblit=True,
                               button=[1], minspanx=5, minspany=5, # type: ignore
                               spancoords='pixels', interactive=True)
        plt.tight_layout()
        plt.show()
        return self.roi


def roi_manuelle(img_rgb, x1, y1, x2, y2):
    """
    Alternative non-interactive : définir la ROI directement en pixels.
    Utile pour les scripts automatisés ou en mode batch.
    Exemple : roi_manuelle(img, 200, 100, 1800, 200)
    """
    return (x1, y1, x2, y2)


# ─────────────────────────────────────────────────────────
# 3. EXTRACTION DU PROFIL D'INTENSITÉ
# ─────────────────────────────────────────────────────────

def extraire_profil(img_rgb, roi, canal='luminance'):
    """
    Moyenne les lignes de la ROI pour obtenir un profil 1D d'intensité.

    Paramètres
    ----------
    canal : 'luminance' | 'R' | 'G' | 'B' | 'V' (value HSV)
        - 'luminance'  : 0.299R + 0.587G + 0.114B  (perception humaine)
        - 'R','G','B'  : canal couleur brut
        - 'V'          : valeur (HSV), utile pour éviter la saturation

    Retourne
    --------
    pixels   : tableau 1D des indices de colonnes
    intensite: tableau 1D des intensités moyennées
    """
    x1, y1, x2, y2 = roi
    bande = img_rgb[y1:y2, x1:x2, :]  # découpe la ROI

    if canal == 'luminance':
        # Luminance perceptuelle (standard ITU-R BT.601)
        profil = (0.299 * bande[:,:,0].astype(float)
                + 0.587 * bande[:,:,1].astype(float)
                + 0.114 * bande[:,:,2].astype(float))
    elif canal == 'R':
        profil = bande[:,:,0].astype(float)
    elif canal == 'G':
        profil = bande[:,:,1].astype(float)
    elif canal == 'B':
        profil = bande[:,:,2].astype(float)
    elif canal == 'V':
        hsv = cv2.cvtColor(bande, cv2.COLOR_RGB2HSV)
        profil = hsv[:,:,2].astype(float)
    else:
        raise ValueError(f"Canal inconnu : {canal}")

    # Moyenne sur l'axe vertical (toutes les lignes de la bande)
    intensite = profil.mean(axis=0)
    pixels = np.arange(len(intensite)) + x1   # coordonnées absolues

    print(f"[✓] Profil extrait : {len(intensite)} points, canal={canal}")
    return pixels, intensite


# ─────────────────────────────────────────────────────────
# 4. CALIBRATION PIXEL → LONGUEUR D'ONDE
# ─────────────────────────────────────────────────────────

"""
PRINCIPE DE CALIBRATION
═══════════════════════
On éclaire le réseau avec des lasers de longueur d'onde CONNUE,
on photographie et on note la position en pixels de chaque raie.

Lasers pratiques facilement accessibles (pointeurs laser) :
  • λ = 405 nm  (violet / UV proche)
  • λ = 450 nm  (bleu)
  • λ = 520 nm  (vert)
  • λ = 532 nm  (vert Nd:YAG fréquence doublée)
  • λ = 635 nm  (rouge)
  • λ = 650 nm  (rouge)
  • λ = 780 nm  (IR proche, invisible à l'œil)

On ajuste ensuite un polynôme :
    λ(px) = a·px² + b·px + c
ou une loi linéaire si l'ordre 1 suffit.
"""

# Points de calibration : (position_pixel, longueur_onde_nm)
# À REMPLIR avec vos mesures expérimentales !
POINTS_CALIBRATION = [
    # (pixel, λ en nm)
    # Exemple fictif — à remplacer par vos valeurs réelles :
    (150,  405),   # laser violet
    (310,  450),   # laser bleu
    (520,  520),   # laser vert
    (540,  532),   # laser vert Nd:YAG
    (820,  635),   # laser rouge
    (870,  650),   # laser rouge
]


def calibrer(points_cal, degre=2, afficher=True):
    """
    Ajuste un polynôme pixel→longueur d'onde sur les points de calibration.

    Paramètres
    ----------
    points_cal : liste de tuples (pixel, lambda_nm)
    degre      : degré du polynôme (1=linéaire, 2=quadratique recommandé)
    afficher   : affiche la courbe de calibration et les résidus

    Retourne
    --------
    coefs : coefficients du polynôme (ordre décroissant)
    poly  : fonction numpy.poly1d prête à l'emploi
    """
    pixels_cal = np.array([p[0] for p in points_cal], dtype=float)
    lambdas_cal = np.array([p[1] for p in points_cal], dtype=float)

    # Ajustement polynomial par moindres carrés
    coefs = np.polyfit(pixels_cal, lambdas_cal, degre)
    poly = np.poly1d(coefs)

    # Résidus
    residus = lambdas_cal - poly(pixels_cal)
    rmse = np.sqrt(np.mean(residus**2))
    print(f"[✓] Calibration polynomial degré {degre}")
    print(f"    Coefficients : {coefs}")
    print(f"    RMSE résidus : {rmse:.2f} nm")

    if afficher:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Courbe de calibration
        px_fin = np.linspace(pixels_cal.min()-50, pixels_cal.max()+50, 500)
        ax1.plot(px_fin, poly(px_fin), 'b-', label=f'Poly degré {degre}')
        ax1.scatter(pixels_cal, lambdas_cal, color='red', zorder=5,
                    label='Lasers de référence')
        for px, lam in zip(pixels_cal, lambdas_cal):
            ax1.annotate(f'{lam} nm', (px, lam),
                         textcoords="offset points", xytext=(5,5), fontsize=8)
        ax1.set_xlabel('Position (pixels)')
        ax1.set_ylabel('Longueur d\'onde (nm)')
        ax1.set_title('Courbe de calibration')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Résidus
        ax2.bar(pixels_cal, residus, color='orange', edgecolor='k', width=15)
        ax2.axhline(0, color='k', linewidth=0.8)
        ax2.set_xlabel('Position (pixels)')
        ax2.set_ylabel('Résidu (nm)')
        ax2.set_title(f'Résidus  |  RMSE = {rmse:.2f} nm')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('calibration.png', dpi=150)
        plt.show()
        print("[✓] Figure calibration.png sauvegardée")

    return coefs, poly


def pixels_vers_lambda(pixels, poly):
    """Convertit un tableau de positions pixels en longueurs d'onde (nm)."""
    return poly(pixels)


# ─────────────────────────────────────────────────────────
# 5. CORRECTION DE FOND ET LISSAGE
# ─────────────────────────────────────────────────────────

def soustraire_fond(lambdas, intensite, methode='min_rolling', fenetre=50):
    """
    Estime et soustrait le fond continu (bruit électronique, lumière parasite).

    methodes disponibles :
      'min_rolling' : minimum glissant sur une fenêtre → fond adaptatif
      'constant'    : soustrait simplement le minimum global
      'percentile'  : utilise le 5e percentile local
    """
    if methode == 'constant':
        fond = np.full_like(intensite, intensite.min())
    elif methode == 'min_rolling':
        fond = np.array([
            intensite[max(0, i-fenetre//2):min(len(intensite), i+fenetre//2)].min()
            for i in range(len(intensite))
        ])
    elif methode == 'percentile':
        fond = np.array([
            np.percentile(
                intensite[max(0, i-fenetre//2):min(len(intensite), i+fenetre//2)],
                5)
            for i in range(len(intensite))
        ])
    else:
        raise ValueError(f"Méthode inconnue : {methode}")

    intensite_corr = np.clip(intensite - fond, 0, None)
    print(f"[✓] Fond soustrait (méthode={methode})")
    return intensite_corr, fond


def lisser(intensite, fenetre=11, ordre=3):
    """
    Lissage Savitzky-Golay : préserve les pics tout en réduisant le bruit.
    fenetre : nombre de points (impair, ≥ ordre+2)
    ordre   : degré du polynôme de lissage
    """
    intensite_lissee = savgol_filter(intensite, fenetre, ordre)
    return np.clip(intensite_lissee, 0, None) # type: ignore


# ─────────────────────────────────────────────────────────
# 6. CALCUL DE L'ABSORBANCE
# ─────────────────────────────────────────────────────────

def calculer_absorbance(intensite_echantillon, intensite_reference,
                        epsilon=1e-6):
    """
    Loi de Beer-Lambert : A(λ) = -log₁₀(I_éch / I_ref)

    Paramètres
    ----------
    intensite_echantillon : spectre de l'échantillon (lampe + cuvette + solution)
    intensite_reference   : spectre de référence (lampe + cuvette vide ou blanc)
    epsilon               : petit nombre pour éviter log(0)

    ATTENTION : les deux spectres doivent être sur la même grille λ
    et acquis dans des conditions identiques (même temps d'exposition,
    même position caméra).
    """
    # Normalisation préalable pour compenser les variations de source
    # I_e = intensite_echantillon / (intensite_echantillon.max() + epsilon)
    # I_r = intensite_reference   / (intensite_reference.max()   + epsilon)
    # # A déterminer - à quoi ça sert??

    # transmittance = np.clip(I_e / (I_r + epsilon), epsilon, 1.0)
    # absorbance = -np.log10(transmittance)

    # version directe
    transmittance = intensite_echantillon / intensite_reference
    absorbance = -np.log10(transmittance)

    print("[✓] Absorbance calculée (Beer-Lambert)")
    return absorbance, transmittance


# ─────────────────────────────────────────────────────────
# 7. DÉTECTION DES PICS SPECTRAUX
# ─────────────────────────────────────────────────────────

def detecter_pics(lambdas, intensite, prominence=0.05, distance_nm=10):
    """
    Trouve automatiquement les pics d'émission ou d'absorption.
    prominence  : hauteur minimale relative par rapport au voisinage
    distance_nm : séparation minimale entre deux pics (en nm)
    """
    # Convertir distance en nm → distance en indices
    dlambda = np.abs(np.diff(lambdas).mean())  # nm/pixel moyen
    distance_idx = max(1, int(distance_nm / dlambda))

    pics_idx, props = find_peaks(intensite,
                                  prominence=prominence * intensite.max(),
                                  distance=distance_idx)
    print(f"[✓] {len(pics_idx)} pic(s) détecté(s) :")
    for idx in pics_idx:
        print(f"    λ = {lambdas[idx]:.1f} nm  |  I = {intensite[idx]:.3f}")
    return pics_idx, props


# ─────────────────────────────────────────────────────────
# 8. VISUALISATION COMPLÈTE
# ─────────────────────────────────────────────────────────

def afficher_resultats(lambdas, intensite_brute, intensite_corr,
                       absorbance=None, pics_idx=None,
                       titre="Analyse spectrale"):
    """
    Génère une figure multi-panneaux avec :
      - Spectre d'intensité brut
      - Spectre corrigé (fond soustrait, lissé)
      - Absorbance (si fournie)
      - Marqueurs des pics
    """
    n_panneaux = 3 if absorbance is not None else 2
    fig, axes = plt.subplots(n_panneaux, 1, figsize=(12, 4*n_panneaux),
                              sharex=True)
    fig.suptitle(titre, fontsize=14, fontweight='bold')

    # --- Panneau 1 : Intensité brute ---
    ax = axes[0]
    ax.plot(lambdas, intensite_brute, color='gray', linewidth=1,
            label='Intensité brute')
    ax.set_ylabel('Intensité (u.a.)')
    ax.set_title('Signal brut')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # --- Panneau 2 : Intensité corrigée ---
    ax = axes[1]
    # Coloration par λ (arc-en-ciel approximatif)
    _colorier_spectre(ax, lambdas, intensite_corr)
    ax.plot(lambdas, intensite_corr, color='k', linewidth=1.2,
            label='Intensité corrigée')
    if pics_idx is not None:
        ax.scatter(lambdas[pics_idx], intensite_corr[pics_idx],
                   color='red', zorder=5, s=60, label='Pics détectés')
        for idx in pics_idx:
            ax.annotate(f'{lambdas[idx]:.0f} nm',
                        (lambdas[idx], intensite_corr[idx]),
                        textcoords="offset points", xytext=(0, 8),
                        ha='center', fontsize=8, color='darkred')
    ax.set_ylabel('Intensité (u.a.)')
    ax.set_title('Signal corrigé et lissé')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # --- Panneau 3 : Absorbance (optionnel) ---
    if absorbance is not None:
        ax = axes[2]
        ax.plot(lambdas, absorbance, color='navy', linewidth=1.5,
                label='Absorbance A(λ)')
        ax.fill_between(lambdas, absorbance, alpha=0.15, color='navy')
        ax.set_ylabel('Absorbance (u.a.)')
        ax.set_title('Absorbance  A = –log₁₀(I/I₀)')
        ax.grid(True, alpha=0.3)
        ax.legend()

    axes[-1].set_xlabel('Longueur d\'onde (nm)')
    plt.tight_layout()
    plt.savefig('spectre_complet.png', dpi=150)
    plt.show()
    print("[✓] Figure spectre_complet.png sauvegardée")


def _colorier_spectre(ax, lambdas, intensite):
    """Remplit le spectre avec les couleurs approximatives λ→RVB."""
    from matplotlib.colors import hsv_to_rgb
    for i in range(len(lambdas)-1):
        lam = lambdas[i]
        # Teinte approximative : violet(380nm)→rouge(700nm)
        hue = np.clip((700 - lam) / (700 - 380), 0, 1) * 0.75  # 0→rouge, 0.75→violet
        couleur = hsv_to_rgb([hue, 0.9, 0.85])
        ax.fill_between(lambdas[i:i+2], 0, intensite[i:i+2],
                        color=couleur, alpha=0.5)


# ─────────────────────────────────────────────────────────
# 9. EXPORT CSV
# ─────────────────────────────────────────────────────────

def exporter_csv(lambdas, intensite, absorbance=None,
                 nom_fichier='spectre.csv'):
    """
    Sauvegarde le spectre dans un fichier CSV lisible par Excel, OriginLab, etc.
    Colonnes : lambda_nm, intensite, absorbance (si disponible)
    """
    with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        entetes = ['lambda_nm', 'intensite']
        if absorbance is not None:
            entetes.append('absorbance')
        writer.writerow(entetes)
        for i, (lam, inte) in enumerate(zip(lambdas, intensite)):
            ligne = [f'{lam:.2f}', f'{inte:.4f}']
            if absorbance is not None:
                ligne.append(f'{absorbance[i]:.4f}')
            writer.writerow(ligne)
    print(f"[✓] Données exportées : {nom_fichier}")


# ─────────────────────────────────────────────────────────
# 10. PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────

def pipeline_spectro(
    chemin_echantillon,
    chemin_reference=None,
    points_cal=None,
    roi=None,
    canal='luminance',
    fond_methode='min_rolling',
    lisser_fenetre=11,
    degre_poly_cal=2,
    afficher=True,
    exporter=True
):
    """
    Lance le pipeline complet d'analyse spectroscopique.

    Paramètres
    ----------
    chemin_echantillon : str  — image de l'échantillon
    chemin_reference   : str  — image de référence (blanc/lampe seule)
                                Si None, pas de calcul d'absorbance.
    points_cal         : list — [(pixel, λ_nm), ...]
                                Si None, utilise POINTS_CALIBRATION par défaut.
    roi                : tuple (x1,y1,x2,y2) ou None (sélection interactive)
    canal              : canal d'intensité ('luminance','R','G','B','V')
    fond_methode       : méthode de soustraction de fond
    lisser_fenetre     : taille de la fenêtre Savitzky-Golay (impair)
    degre_poly_cal     : degré du polynôme de calibration
    afficher           : afficher les figures
    exporter           : sauvegarder les CSV
    """
    print("\n" + "═"*55)
    print("  PIPELINE SPECTROSCOPIQUE — RÉSEAU DE DIFFRACTION")
    print("═"*55)

    # ── Étape 1 : Chargement ──────────────────────────────
    _, img_rgb = charger_image(chemin_echantillon)

    # ── Étape 2 : ROI ─────────────────────────────────────
    if roi is None:
        print("[→] Sélection interactive de la ROI...")
        sel = SelecteurROI(img_rgb)
        roi = sel.selectionner()
        if roi is None:
            print("[!] Aucune ROI sélectionnée. Arrêt.")
            return

    # ── Étape 3 : Extraction du profil ───────────────────
    pixels, intensite_brute = extraire_profil(img_rgb, roi, canal)

    # ── Étape 4 : Calibration ────────────────────────────
    cal = points_cal if points_cal else POINTS_CALIBRATION
    _, poly = calibrer(cal, degre=degre_poly_cal, afficher=afficher)
    lambdas = pixels_vers_lambda(pixels, poly)

    # Garder seulement la plage visible (380–780 nm)
    masque = (lambdas >= 350) & (lambdas <= 800)
    lambdas = lambdas[masque]
    intensite_brute = intensite_brute[masque]

    # ── Étape 5 : Correction de fond et lissage ──────────
    intensite_corr, fond = soustraire_fond(lambdas, intensite_brute,
                                           methode=fond_methode)
    print("DEBUG", intensite_corr, lisser_fenetre)
    intensite_lissee = lisser(intensite_corr, fenetre=lisser_fenetre)

    # ── Étape 6 : Absorbance (si référence fournie) ──────
    absorbance = None
    if chemin_reference:
        print(f"\n[→] Traitement de la référence : {chemin_reference}")
        _, img_ref = charger_image(chemin_reference)
        _, intensite_ref_brute = extraire_profil(img_ref, roi, canal)
        intensite_ref_brute = intensite_ref_brute[masque]
        intensite_ref, _ = soustraire_fond(lambdas, intensite_ref_brute,
                                            methode=fond_methode)
        intensite_ref = lisser(intensite_ref, fenetre=lisser_fenetre)
        absorbance, _ = calculer_absorbance(intensite_lissee, intensite_ref)

    # ── Étape 7 : Détection des pics ─────────────────────
    pics_idx, _ = detecter_pics(lambdas, intensite_lissee)

    # ── Étape 8 : Affichage ───────────────────────────────
    if afficher:
        afficher_resultats(lambdas, intensite_brute, intensite_lissee,
                           absorbance=absorbance, pics_idx=pics_idx)

    # ── Étape 9 : Export ─────────────────────────────────
    if exporter:
        exporter_csv(lambdas, intensite_lissee, absorbance)

    print("\n[✓] Analyse terminée.")
    return lambdas, intensite_lissee, absorbance


# ─────────────────────────────────────────────────────────
# EXEMPLE D'UTILISATION
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":

    # ╔═══════════════════════════════════════════════════════╗
    # ║  PARAMÈTRES À ADAPTER À VOTRE CONFIGURATION          ║
    # ╚═══════════════════════════════════════════════════════╝

    # Chemin vers votre image capturée par smartphone
    IMAGE_ECHANTILLON = "img/s3/dil4.jpg"
    IMAGE_REFERENCE   = "img/s3/dil4.jpg"   # None si pas de référence

    # Points de calibration mesurés sur vos images avec les lasers :
    # Photographiez chaque laser, notez le pixel du centre de la raie.
    MES_POINTS_CALIBRATION = [
        (1130,  650),   # ← remplacez ces valeurs par les vôtres
        (1336,  520),
        (1536,  405)
    ]

    # ROI : si None → sélection interactive à la souris
    # Sinon définissez (x_gauche, y_haut, x_droite, y_bas) en pixels
    MA_ROI = None   # ex: (200, 100, 1800, 200)

    # Lancement du pipeline
    lambdas, intensite, absorbance = pipeline_spectro(
        chemin_echantillon = IMAGE_ECHANTILLON,
        chemin_reference   = IMAGE_REFERENCE,
        points_cal         = MES_POINTS_CALIBRATION,
        roi                = MA_ROI,
        canal              = 'luminance',   # ou 'G' pour spectre vert dominant
        fond_methode       = 'constant',
        lisser_fenetre     = 11,
        degre_poly_cal     = 1,
        afficher           = True,
        exporter           = False,
    ) # type: ignore