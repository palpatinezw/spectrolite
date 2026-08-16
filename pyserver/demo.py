from analyse_img import extraction_intensite
from traitement import calibration
import matplotlib.pyplot as plt

intensite, r, g, b = extraction_intensite("img/samplecalib.png", 40, 110, 10, 710)

print(intensite)

a, b = calibration([405, 532, 650], intensite)

intensite2, r2, g2, b2 = extraction_intensite("img/sample.png", 40, 110, 10, 710, debug=True) 

plt.plot([a*i + b for i in range(len(intensite))], intensite2) # type:ignore

plt.show()