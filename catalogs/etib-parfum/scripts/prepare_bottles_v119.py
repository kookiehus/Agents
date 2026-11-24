"""v119: owner's photos for A10 Blue Seduction (men), C9 Chanel Egoiste, G20 Gentlemen Only, E1 Ex Nihilo Fleur Narcotique,
E31 Ex Nihilo Blue Talisman, G7 Acqua di Gio (studio shots on white/grey).
Outline = per-row extents of the rembg cut-out (low threshold so the clear glass base counts), made symmetric about the
bottle's axis (front views; removes the side shadow), median + Gaussian smoothed, drawn as a polygon at 4x -> a solid,
smooth silhouette; clear glass keeps its photographed (light) look. Edge colours from 3 px inside, light sharpening.
Usage: prepare_bottles_v119.py <src dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True); K = 4

def cut(name, src, thr=20, ybot=None, color=1.06, contrast=1.06, axis=None, own=0.0, raw=False, recolor=True, flat=()):
    rgb = np.array(Image.open(f'{SRC}/{src}').convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
    A = np.array(Image.open(f'{SRC}/{name}_rb.png'))[..., 3] > thr
    lab, n = nd.label(A); c = np.bincount(lab.ravel()); c[0] = 0; A = nd.binary_fill_holes(lab == np.argmax(c))
    ys = np.where(A.any(1))[0]; y1 = ybot if ybot else ys.max()
    Y = np.arange(ys.min(), y1 + 1)
    lx = np.array([np.where(A[y])[0].min() if A[y].any() else np.nan for y in Y], float)
    rx = np.array([np.where(A[y])[0].max() + 1 if A[y].any() else np.nan for y in Y], float)
    ok = ~np.isnan(lx); lx = np.interp(Y, Y[ok], lx[ok]); rx = np.interp(Y, Y[ok], rx[ok])
    cx = np.median((lx + rx)/2); hw = (rx - lx)/2
    if axis: cx = axis; hw = rx - cx                               # C9: shadow on the left, use the right edge about the cap's axis
    hw = nd.gaussian_filter1d(nd.median_filter(hw, 9), 1.5) - 0.8
    for f0, f1 in flat:                                              # v135: straight sides (constant half-width) on these rows
        sel = (Y >= f0) & (Y <= f1); hw[sel] = np.median(hw[sel])
    L_, R_ = cx - hw, cx + hw
    if own:                                                          # v124: each side follows its own edge, pulled in by `own` px
        L_ = nd.gaussian_filter1d(nd.median_filter(lx, 9), 1.5) + own; R_ = nd.gaussian_filter1d(nd.median_filter(rx, 9), 1.5) - own
    poly = np.r_[np.c_[L_, Y], np.c_[R_, Y][::-1]]
    big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [np.round(poly*K).astype(np.int32)], 255)
    a = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
    if raw:                                                          # v133: keep the given mask's own top edge (black-on-black)
        a = np.minimum(a, cv2.GaussianBlur(A.astype(np.float32), (0, 0), 1.0))
    e = max(5, int(round(h/350))*2 + 1) if recolor else 1   # v134: black-on-black keeps its own bright rim
    inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((e, e), np.uint8)).astype(bool)
    gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
    yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c3 = ImageEnhance.Color(img.convert('RGB')).enhance(color)
    c3 = ImageEnhance.Contrast(c3).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/{name}.png'); print(name, img.size)

if os.environ.get('ONLY') == 'V137':                              # v137: owner's photos C24 C25 C4 (Chanel Chance: mirrored about the
    cut('C24', 'C24.jpg', axis=1084.0)                             #   bottle axis, the cap's cast shadow on the left is dropped),
    cut('C25', 'C25.jpg', axis=1078.0)                             #   C5 CK All, G2 L'Interdit, G11 Bamboo (symmetric),
    cut('C4', 'C4.jpg', axis=799.0)                                #   E10 Eclat, G15 Flora (asymmetric clip / bow: own edges)
    cut('C5', 'C5.jpg'); cut('G2', 'G2.jpg'); cut('G11', 'G11.jpg')
    cut('E10', 'E10.jpg', own=1.0); cut('G15', 'G15.jpg', own=1.0); sys.exit()
if os.environ.get('ONLY') == 'V26':                               # v134: V26 Aqua Kiss mist, symmetric
    cut('V26', 'V26.jpg', thr=100, color=1.06, contrast=1.06, flat=((193, 322), (331, 338), (352, 852))); sys.exit()
if os.environ.get('ONLY') == 'V19':                               # v131: V19 SLT Noir, black on black (mask from scripts/mask_black_v133.py)
    cut('V19', 'V19.png', thr=128, ybot=1253, color=1.0, contrast=1.04, own=1.5, raw=True, recolor=False); sys.exit()
if os.environ.get('ONLY') == 'L20':                               # v126: L20 L'Immensite (cropped away from its tube box), symmetric
    cut('L20', 'L20.png', thr=100, color=1.04, contrast=1.08); sys.exit()
if os.environ.get('ONLY') == 'T12':                               # v123: T12 Trussardi Uomo
    cut('T12', 'T12.jpg', thr=60, own=3.0); sys.exit()   # v124: no light rim on the right
if os.environ.get('ONLY') == 'L6':                                # v120: L6 Lacoste Pour Femme (bottle cropped away from its box)
    cut('L6', 'L6.png'); sys.exit()
cut('A10', 'A10.png')
cut('C9', 'C9.jpg', thr=60, axis=1082.0)
cut('G20', 'G20.jpg')
cut('E1', 'E1.jpg')
cut('E31', 'E31.jpg', ybot=1476)
cut('G7', 'G7.jpg')
