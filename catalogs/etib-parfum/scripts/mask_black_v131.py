"""v131: silhouette of a black bottle shot on pure black (rembg sees only the label): pixels brighter than the backdrop,
closed and hole-filled, cut at the bottle's foot (mirror floor below). Writes an RGBA whose alpha is the mask.
Usage: mask_black_v131.py <photo> <foot row> <out.png>"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
src, foot, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
im = Image.open(src).convert('RGB'); L = np.array(im).astype(int).max(2)
m = nd.binary_closing(L > 6, iterations=6); m[foot:] = False
lab, n = nd.label(m); c = np.bincount(lab.ravel()); c[0] = 0; m = nd.binary_fill_holes(lab == np.argmax(c))
m = nd.binary_opening(m, iterations=2)
o = im.convert('RGBA'); o.putalpha(Image.fromarray((m*255).astype(np.uint8))); o.save(out); print(out, m.sum())
