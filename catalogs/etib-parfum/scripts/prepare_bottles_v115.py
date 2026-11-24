"""v115: owner's photos for T2/T15 Trussardi Donna, K23 Kenzo L'Eau par Kenzo pour Homme, L5 Lancome La Nuit Tresor,
M11 Marc Jacobs Perfect, A2 Avril Lavigne Forbidden Rose.
Four are studio shots on black with a mirror floor: the reflection is cut off along the bottle's real lower edge
(measured on the photo). Mask = rembg cut-out made solid (clear glass shot on black keeps its own dark backdrop, which
reads as glass on the dark panel), holes filled, lightly smoothed; edge colours from 2 px inside; light sharpening.
Usage: prepare_bottles_v115.py <src dir with T2.png K23.png L5.png M11.jpg A2.png and *_rb.png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True); K = 4

def below(h, w, poly):
    m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.round(np.array(poly)*K).astype(np.int32)], 255)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255

def cut(name, src, keep, sig=1.0, thr=0.25, color=1.05, contrast=1.05):
    rgb = np.array(Image.open(f'{SRC}/{src}').convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
    al = np.array(Image.open(f'{SRC}/{name}_rb.png'))[..., 3].astype(np.float32)/255
    clip = below(h, w, keep(w))
    m = (al > thr) & (clip > 0.5)
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(m); c = np.bincount(lab.ravel()); c[0] = 0; m = nd.binary_fill_holes(lab == np.argmax(c))
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), sig); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1)*clip
    inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
    yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c3 = ImageEnhance.Color(img.convert('RGB')).enhance(color)
    c3 = ImageEnhance.Contrast(c3).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/{name}.png'); print(name, img.size)

cut('T2', 'T2.png', lambda w: [(0, 0), (w, 0), (w, 1338), (0, 1338)])
cut('K23', 'K23.png', lambda w: [(0, 0), (w, 0), (w, 1305), (0, 1305)])
cut('L5', 'L5.png', lambda w: [(0, 0), (w, 0), (w, 1200), (590, 1200), (545, 1233), (500, 1200), (0, 1200)])
cut('M11', 'M11.jpg', lambda w: [(0, 0), (w, 0), (w, 2000), (0, 2000)], thr=0.3)
cut('A2', 'A2.png', lambda w: [(0, 0), (w, 0), (w, 1323), (692, 1325), (548, 1352), (392, 1325), (0, 1323)])
