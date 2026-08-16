import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

fichier_entree = "excel/mystere a lisser.csv"
fichier_sortie = "excel/mystere_lisse.csv"

window_length = 21  # doit être impair
polyorder = 3

data = pd.read_csv(fichier_entree, sep=";", header=None)

x = range(len(data))

# Lissage
data_lisse = data.apply( # type:ignore
    lambda col: savgol_filter(col, window_length, polyorder) #type:ignore
)

# Sauvegarde
data_lisse.to_csv(
    fichier_sortie,
    sep=";",
    index=False,
    header=False
)

# =========================
# Affichage
# =========================

plt.figure(figsize=(12, 6))

for i in range(data.shape[1]):
    # Données brutes
    plt.plot(
        x,
        data.iloc[:, i],
        linestyle="--",
        alpha=0.5,
        label=f"Brut {i+1}"
    )

    # Données lissées
    plt.plot(
        x,
        data_lisse.iloc[:, i],
        linewidth=2,
        label=f"Lissé {i+1}"
    )

plt.xlabel("Indice (ou longueur d'onde)")
plt.ylabel("Absorbance")
plt.title("Spectres avant et après lissage")
plt.legend()
plt.grid(True)

plt.show()

print("Lissage terminé.")