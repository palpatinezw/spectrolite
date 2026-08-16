# Consignes d'utilisation (version ancienne)

Lancer l'application d'analyse avec `main.py`. La bande d'extraction de l'image par defaut est mise à `bande = (40, 100)`. Pour adjuster la bande, utiliser `adjusterBande()`

La fonction `calibrer()` doit être obligatoirement appelée à **chaque reinitialisation** avant de faire une analyse. Une analyse simple est effectuée avec la fonction `analyse()` - le resultat est stocké dans `out/resultat_DATE.txt`

# Protocole 
1. Définir la largeur de référence pour l'expérience `xWidth`. Cette valeur devrait rester inchangé - sinon l'exploitation des données ensuite serait difficile. 
2. Calibrer à l'aide d'une image calibration et la fonction `calibrer()` - par exemple `calibrer("img/samplecalib.png", [405, 532, 650])`. 
3. Obtenir les spectres brutes à l'aide de la fonction `analyse()`. Renommer les resultats pour pouvoir bien identifier notamment le spectre qui correspond à la ligne de base - par exemple `analyse("img/samplecalib.png")`
4. Utiliser la fonction `parse()` pour associer les données enregistrer dans les fichiers à des arrays numpy - par exemple `ligneDeBase = parse("out/base.txt")`
5. Obtenir l'absorbance avec la fonction `getAbsorbance()` - par exemple `absr = getAbsorbance(ligneDeBase, C)`. Il est alors possible de tracer l'absorbance `plt.plot(absr["longeurs"], absr["absorbance"])` ou obtenir l'absorbance à un longeur d'onde spécifique `absr["absorbance"][np.searchsorted(absr["longeurs"], <LONGEUR D'ONDE>, side="left") - 1]` (Bug: wavelengths sorted in the reverse order)