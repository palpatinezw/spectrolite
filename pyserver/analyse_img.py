import cv2
import numpy as np
import matplotlib.pyplot as plt

def extraction_intensite(image_path:str, yh:float, yb:float, xl:float, xr:float, showplots=False, debug=False):
    """
    Extraction en intensite moyenne, entre les hauteurs yh (en haut) et yb (en bas)
    
    :param image_path: chemin de l'image
    :type image_path: str
    :param yh: seuil d'analyse en haut
    :type yh: float
    :param yb: seuil d'analyse en bas
    :type yb: float
    :param xl: seuil d'analyse à gauche
    :type xl: float
    :param xr: seuil d'analyse à droite
    :type xr: float
    :param showplots: affichage des graphiques d'intensité
    :type showplots: bool
    :param debug: affichage d'image pour debouggage
    :type debug: bool
    """
    # ---- LOAD IMAGE ----
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    H, W, _ = img_rgb.shape

    # ---- CLAMP BAND RANGE ----
    y1 = max(0, yh)
    y2 = min(H, yb)
    x1 = max(0, xl)
    x2 = min(W, xr)

    band = img_rgb[y1:y2, x1:x2, :]  # shape: (thickness, W, 3)

    # ---- INTENSITY EXTRACTION ----
    band_gray = (0.2989 * band[:, :, 0] +
                0.5870 * band[:, :, 1] +
                0.1140 * band[:, :, 2])
    intensity = band_gray.mean(axis=0)  # intensity vs x

    # per-channel mean intensity vs x
    intensity_r = band[:, :, 0].mean(axis=0)
    intensity_g = band[:, :, 1].mean(axis=0)
    intensity_b = band[:, :, 2].mean(axis=0)

    # ---- PLOT ----
    if showplots:
        plt.figure()

        plt.plot(intensity)
        plt.title(f"Grayscale intensity vs x (Band [{y1}] - [{y2}])")
        plt.xlabel("x (pixels)")
        plt.ylabel("Intensity (0-255)")
        
        plt.figure()

        plt.plot(intensity_r, label="R")
        plt.plot(intensity_g, label="G")
        plt.plot(intensity_b, label="B")
        plt.title(f"RGB intensity vs x (Band [{y1}] - [{y2}])")
        plt.xlabel("x (pixels)")
        plt.ylabel("Intensity (0-255)")
        plt.legend()

        plt.tight_layout()

    # DEBUG - show image sampled
    if debug:
        debugimg = img_rgb.copy()
        cv2.line(debugimg, (x1, y1), (x2, y1), (255, 0, 0), 2) # type: ignore
        cv2.line(debugimg, (x1, y2-1), (x2, y2-1), (255, 0, 0), 2) # type: ignore

        plt.figure()
        plt.imshow(debugimg)
        plt.title("Sampled band region")
        plt.axis("off")

    plt.show()

    return intensity, intensity_r, intensity_g, intensity_b
