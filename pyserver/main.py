from analyse_img import extraction_intensite
from traitement import calibration
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from datetime import datetime
import numpy as np
import os
import cv2

bande = (700, 750) # bande d'extraction par defaut
xMin = 2619
xWidth = 934 # Il faut OBLIGATOIREMENT assurer que cette valeur reste constante

m = -0.2664195129856975
c = 663.5294963737288

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
    return img_rgb

def pixelToLongueur(pxl):
    return m*pxl + c

def ajusterBande(l, h, sample=None):
    """
        Ajuster la bande d'extraction (1). 

        :param l: pixel limite bas (en haute position)
        :param h: pixel limite haut (en basse position)
        :param sample: image example pour visualiser la nouvelle bande
    """
    global bande 
    bande = (l, h)
    if sample:
        extraction_intensite(sample, l, h, xMin, xMin + xWidth, debug=True)
    print(f"[✓] Bande: [ {l} , {h} ]")

def ajusterX(x, xw=None):
    global xMin, xWidth
    xMin = x
    if xw != None:
        print("[!] Attention ! Modification de largueur de bande !")
        xWidth = xw
    print(f"[✓] X width: [ {xMin} , {xMin + xWidth} ] (width : {xWidth})")

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

# e.g. calibrer("img/samplecalib.png", [405, 532, 650])
def calibrer(img, pics):
    """
        Calibration des longueurs d'onde en fonction des pixels. Calibration effectuée à partir de la bande (1)

        :param img: chemin de l'image de calibratoin
        :param pics: liste des longueurs d'onde des pics attendus
    """
    intensite, r, g, b = extraction_intensite(img, bande[0], bande[1], xMin, xMin + xWidth)
    res = calibration(pics, intensite)
    global m
    global c
    m = res[0]
    c = res[1]
    print(f"[✓] Calibration effectuée: {m}*x + {c}")

def analyse(img):
    """
        Analyse simple d'un seul spectre

        :param img: chemin de l'image à analyser
    """
    if m == 0:
        print("[X] Analyse non effectuée - erreur de calibration")
        return
    intensite, r, g, b = extraction_intensite(img, bande[0], bande[1], xMin, xMin + xWidth)
    now = datetime.now()
    resultatstr = f"Extraction [ {img} ] effectuee {str(now)}\n"
    resultatstr += f"Calibration: {m}*x + {c} [largueur {xMin} + {xWidth}]\n\n"
    resultatstr += f"pixel, longueur d'onde, intensite, r, g, b\n"
    for i in range(len(intensite)):
        resultatstr += f"{i}, {pixelToLongueur(i)}, {intensite[i]}, {r[i]}, {g[i]}, {b[i]}\n"
    with open(f"out/resultat_{now.strftime("%Y%m%d-%H%M%S")}.txt", "w") as f:
        f.write(resultatstr)

    print(f"[✓] Analyse simple effectuée [ out/resultat_{now.strftime("%Y%m%d-%H%M%S")}.txt ]")
    return f"out/resultat_{now.strftime("%Y%m%d-%H%M%S")}.txt"

def parse(filename):
    """
    Reads a spectrum output file and returns structured numpy arrays.

    :param filename: path to the .txt file
    :return: dict with keys {intensities, r, g, b, longueurs}
    """
    intensities = []
    r_vals = []
    g_vals = []
    b_vals = []
    longueur = []

    with open(filename, "r") as f:
        lines = f.readlines()

    # Find the start of the data table
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("pixel"):
            start_idx = i + 1
            break

    if start_idx is None:
        raise ValueError("Invalid file format: no data header found")

    # Parse data lines
    for line in lines[start_idx:]:
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 6:
            continue  # skip malformed lines

        _, wavelength, intensity, r, g, b = parts

        longueur.append(float(wavelength))
        intensities.append(float(intensity))
        r_vals.append(float(r))
        g_vals.append(float(g))
        b_vals.append(float(b))

    return {
        "intensities": np.array(intensities),
        "r": np.array(r_vals),
        "g": np.array(g_vals),
        "b": np.array(b_vals),
        "longueurs": np.array(longueur),
    }

def getAbsorbance(base, spectre):
    """
    :param: base (objet retourné par parse())
    :param: spectre (objet retourné par parse())
    """
    return {
        "longueurs": base["longueurs"],
        "absorbance": -np.log( spectre["intensities"] / base["intensities"] )
    }

def run():
    """
    Execute l'intégralité du code pour effecteur une analyse de spectre complète.
    """

    # Calibration (facultative)
    print(f"[.] La droite de calibration est actuellement {m} x + {c} [{xMin} (largueur {xWidth})]")
    calibrate = input("[?] Voulez-vous effectuer une calibration ? (y/n): ") == 'y'

    while calibrate:
        calibrate_file = input("[?] Entrer le nom du fichier de calibration : ")
        calib_roi = None
        
        print("[→] Sélection interactive de la ROI...")
        sel = SelecteurROI(charger_image(calibrate_file))
        roi = sel.selectionner()
        if roi is None:
            print("[!] Aucune ROI sélectionnée. Arrêt.")

        ajusterBande(roi[1], roi[3])  # type: ignore
        ajusterX(roi[0], roi[2]-roi[0]) # type: ignore

        calibrate_peaks = input("[?] Entrer les longueurs d'onde des pics (en nm, separes de virgules) : ")
        calibrer(calibrate_file, [int(x) for x in calibrate_peaks.split(",")])
        
        calibrate = input(f"[?] La droite de calibration est actuellement {m} x + {c} - voulez-vous re-effectuer une calibration ? (y/n): ") == 'y'
    
    print(f"[!] Sauvegarder la calibration ! {m} x + {c} [{xMin} (largueur {xWidth})]")

    
    blanc = []
    spectres = []
    absrs = []
    continueanalysis = True

    while continueanalysis:
        continueanalysis = False
        print(f"[.] Debut d'analyse {len(spectres)}")

        blanc_file = input("[?] Entrer le nom du BLANC : ")
        print("[→] Sélection interactive de la ROI...")
        sel = SelecteurROI(charger_image(blanc_file))
        roi = sel.selectionner()
        if roi is None:
            print("[!] Aucune ROI sélectionnée. Arrêt.")
        ajusterBande(roi[1], roi[3])  # type: ignore
        if abs(roi[0] - xMin) > 100: # type: ignore
            print(f"[!] Attention : ecart important entre xMin selectionne {roi[0]} et xMin de calibration {xMin}") # type: ignore
            ajusterBande(roi[1], roi[3], blanc_file) # type: ignore
        
        print("[.] Analyse du BLANC")
        blanc_res = analyse(blanc_file)
        blanc.append(parse(blanc_res))

        spectre_file = input("[?] Entrer le nom du fichier (vide pour utiliser le même fichier que le blanc) : ")

        print("[→] Sélection interactive de la ROI...")
        if spectre_file == "":
            spectre_file = blanc_file
        sel = SelecteurROI(charger_image(spectre_file))
        roi = sel.selectionner()
        if roi is None:
            print("[!] Aucune ROI sélectionnée. Arrêt.")
        ajusterBande(roi[1], roi[3])  # type: ignore
        if abs(roi[0] - xMin) > 100: # type: ignore
            print(f"[!] Attention : ecart important entre xMin selectionné {roi[0]} et xMin de calibration {xMin}") # type: ignore
            ajusterBande(roi[1], roi[3], spectre_file) # type: ignore
        
        print(f"[.] Analyse du spectre {len(spectres)}")
        spectre_res = analyse(spectre_file)
        spectres.append(parse(spectre_res))
        absrs.append(getAbsorbance(blanc[-1], spectres[-1]))

        for i in range(len(absrs)):
            absr = absrs[i]
            plt.plot(absr["longueurs"], absr["absorbance"], label=f"Spectre {i}")
        plt.legend()
        plt.show()

        continueanalysis = input("[?] Voulez-vous continuer ? (y/n): ") == 'y'
    
    exportnom = input("[?] Sous quel nom voulez-vous sauvegarder les spectres ? (vide pour passer): ")
    if exportnom == "": return

    with open(f"out/{exportnom}.csv", "w") as f:
        f.write("longueur")
        for i in range(len(absrs)):
            f.write(f",spectre {i}")
        f.write("\n")

        for j in range(len(absrs[0]["longueurs"])):
            f.write(f"{absrs[0]["longueurs"][j]}")
            for i in range(len(absrs)):
                absr = absrs[i]
                f.write(f",{absr["absorbance"][j]}")
            f.write("\n")

def generateAbsorbanceCsv(basefiles, spectrefiles):
    """
        Génère un fichier CSV contenant les longueurs d'ondes et les absorbances calculées à partir d'un fichier de base (blanc) et une liste de fichiers de spectres.

        :param basefile: chemin vers le fichier de base (blanc)
        :param spectrefiles: liste de chemins vers les fichiers de spectres à analyser
    """
    now = datetime.now()
    
    base = parse(basefiles[0])
    with open(f"out/absorbance-{now.strftime('%Y%m%d-%H%M%S')}.csv", "w") as f:
        f.write("longueur")
        for spectrefile in spectrefiles:
            f.write(f",absorbance_{spectrefile}")
        f.write("\n")

        for i in range(len(base["longueurs"])):
            f.write(f"{base['longueurs'][i]}")
            for j in range(len(spectrefiles)):
                spectrefile = spectrefiles[j]
                basefile = basefiles[j] if j < len(basefiles) else basefiles[0]
                spectre = parse(spectrefile)
                curbase = parse(basefile)
                absorbance = -np.log( spectre["intensities"][i] / curbase["intensities"][i] )
                f.write(f",{absorbance}")
            f.write("\n")

# analyse_complete()