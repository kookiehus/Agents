"""v73 final polish: cleans the outline of older cut-outs that the final QA flagged (dark / brown / light fringes,
background specks and ragged edges). Per bottle: alpha -> solid mask, small specks removed (opening), outline smoothed,
`erode` px of fringe taken off, the outer `band` px recoloured from the bottle's own colour a little further inside.
Usage: clean_bottles_v73.py <data dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
D, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
JOBS = {   # code_sec: (source, erode px, band px, opening radius)
    'L10_УНИ': ('bottles_site/L10_УНИ.png', 2, 5, 4),
    'T1_МУЖ':  ('bottles_v27/T1_МУЖ.png', 3, 7, 3),
    'N10_ПРЕ': ('bottles_v27/N10_ПРЕ.png', 2, 5, 3),
    'T14_ПРЕ': ('bottles_v27/T14_ПРЕ.png', 2, 5, 2),
    'L4_ПРЕ':  ('bottles_v27/L4_ПРЕ.png', 2, 5, 3),
    'K23_МУЖ': ('bottles_site/K23_МУЖ.png', 2, 4, 2),
    'K5_ПРЕ':  ('bottles_site/K5_ПРЕ.png', 2, 4, 2),
    'C4_ЖЕН':  ('bottles_site/C4_ЖЕН.png', 2, 5, 3),
    'D1_ЖЕН':  ('bottles_site/D1_ЖЕН.png', 2, 4, 3),
    'D3_ЖЕН':  ('bottles_site/D3_ЖЕН.png', 2, 4, 3),
    'E10_ЖЕН': ('bottles_site/E10_ЖЕН.png', 2, 4, 3),
    'G2_ЖЕН':  ('bottles_site/G2_ЖЕН.png', 2, 5, 3),
    'G4_ЖЕН':  ('bottles_site/G4_ЖЕН.png', 2, 5, 3),
    'H4_ЖЕН':  ('bottles_site/H4_ЖЕН.png', 2, 4, 3),
    'H14_ЖЕН': ('bottles_site/H14_ЖЕН.png', 2, 4, 3),
    'L8_ЖЕН':  ('bottles_site/L8_ЖЕН.png', 2, 4, 2),
    'V23_ЖЕН': ('bottles_v27/V23_ЖЕН.png', 2, 5, 3),
    'Z1_ЖЕН':  ('bottles_site/Z1_ЖЕН.png', 2, 4, 3),
}
disk = lambda r: np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
for name, (src, er, band, op) in JOBS.items():
    im = Image.open(f'{D}/{src}').convert('RGBA'); a = np.array(im).astype(np.float32)/255
    rgb, al = a[..., :3], a[..., 3]
    m = al > 0.5
    m = nd.binary_opening(m, disk(op))
    lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)    # one piece: specks dropped
    m = nd.binary_fill_holes(m)
    if name == 'L10_УНИ':   # straight cylinder: the right side (ragged leftover background) is mirrored from the clean left side
        h_, w_ = m.shape; rows = np.where(m.any(axis=1))[0]
        L = np.array([np.where(m[y])[0][0] if m[y].any() else -1 for y in range(h_)]); R_ = np.array([np.where(m[y])[0][-1] if m[y].any() else -1 for y in range(h_)])
        top = rows[0]; capr = range(top + 5, top + 60); cx = np.median([(L[y] + R_[y])/2 for y in capr if L[y] >= 0])
        for y in rows:
            if L[y] >= 0: m[y, :] = False; m[y, L[y]:int(round(2*cx - L[y])) + 1] = True
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0) > 0.5                     # smooth outline
    m = nd.binary_erosion(m, disk(er))
    d = nd.distance_transform_edt(m)
    core = d > band; idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
    t = np.clip((band + 1 - d)/band, 0, 1)[..., None]*m[..., None]
    rgb = rgb*(1 - t) + rgb[idx[0], idx[1]]*t
    if name == 'T1_МУЖ':    # the thick glass frame took the brown of the old background: make it neutral clear glass
        fr = np.clip((26 - d)/10, 0, 1)[..., None]*m[..., None]
        g_ = rgb.mean(axis=2, keepdims=True); rgb = rgb*(1 - fr) + (g_*np.array([0.97, 0.99, 1.02]))*fr
    alpha = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.9); alpha = np.clip((alpha - 0.5)*2.0 + 0.5, 0, 1)
    Image.fromarray((np.dstack([np.clip(rgb, 0, 1), alpha])*255).astype(np.uint8), 'RGBA').save(f'{OUT}/{name}.png'); print(name, im.size)
