"""v26: exact geometric outlines for boxy bottles whose cut-outs were ragged.
Each part (cap, neck, body, label) is a rounded rectangle measured on the source picture; the bottle keeps its own
pixels inside, pixels the shape adds and light/dark fringe along the new edge take the colour found just inside.
Usage: fix_bottles_v26.py <data dir> <v25 dir> <out dir>"""
import sys, os, json, shutil, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
D, V25, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
for f in os.listdir(V25): shutil.copy(f'{V25}/{f}', f'{OUT}/{f}')
cards = json.load(open(f'{D}/cards.json'))
def card_file(code, sec): return f"{D}/" + [c for c in cards if c['code'] == code and c['section'].startswith(sec)][0]['bottle']['file']

def load(path, drop_reflection):
    arr = np.array(Image.open(path).convert('RGBA')).astype(np.float32)/255
    if drop_reflection:
        last = int(np.where(arr[..., 3].max(axis=1) > 0.97)[0][-1]); arr = arr[:last + 1]
    return arr[..., :3].copy(), arr[..., 3].copy()

def shape_mask(h, w, parts, ss=4):
    """Anti-aliased union of rounded rectangles (x0, y0, x1, y1, radius), drawn 4x larger and reduced."""
    m = np.zeros((h*ss, w*ss), np.uint8)
    for x0, y0, x1, y1, r in parts:
        x0, y0, x1, y1, r = [int(round(v*ss)) for v in (x0, y0, x1, y1, r)]
        cv2.rectangle(m, (x0 + r, y0), (x1 - r, y1), 255, -1); cv2.rectangle(m, (x0, y0 + r), (x1, y1 - r), 255, -1)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            if r > 0: cv2.circle(m, (cx, cy), r, 255, -1)
    return cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)

def rectify(rgb, a, parts, keep_rows=None, ring=4, tol=0.16):
    h, w = a.shape; sm = shape_mask(h, w, parts)
    if keep_rows is not None:                                   # rows where the original outline is kept (domed caps etc.)
        y0, y1 = keep_rows; sm[y0:y1] = np.maximum(sm[y0:y1], a[y0:y1])
    inside = sm > 0.5
    core = nd.binary_erosion(inside, iterations=ring + 3) & (a > 0.9)
    if not core.any(): core = inside & (a > 0.9)
    idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True); ref = rgb[idx[0], idx[1]]
    edge = inside & ~nd.binary_erosion(inside, iterations=ring)
    added = inside & (a < 0.6)
    off = np.abs(rgb - ref).max(axis=2) > tol
    fix = added | (edge & off)
    rgb = np.where(fix[..., None], ref, rgb)
    return rgb, sm

def finish(rgb, a, scale, path):
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    if scale != 1:
        im = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
        c = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); im = Image.merge('RGBA', (*c.split(), im.getchannel('A')))
    im.save(path)

# parts measured on each source (x0, y0, x1, y1, corner radius) in source pixels
JOBS = {
 ('C36', 'МУЖ'): (f'{D}/bottles_site/C36_МУЖ.png', False, [(29, 6, 274, 292, 3), (3, 292, 612, 896, 12)], None, 1.0),
 ('M1', 'ПРЕ'):  (card_file('M1', 'ПРЕ'), True, [(92, 3, 156, 81, 3), (32, 82, 217, 332, 7)], None, 2.6),
 ('M2', 'ПРЕ'):  (card_file('M2', 'ПРЕ'), True, [(97, 3, 163, 81, 3), (35, 83, 223, 333, 7)], None, 2.6),
 ('T1', 'МУЖ'):  (card_file('T1', 'МУЖ'), True, [(31, 4, 268, 314, 34)], (0, 30), 2.6),
 ('N2', 'УНИ'):  (f'{D}/bottles_site/N2_УНИ.png', False, [(196, 3, 473, 300, 6), (7, 306, 656, 816, 8)], None, 1.0),
 ('N10', 'ПРЕ'): (f'{D}/../up/N10_rb.png', False, [(2, 3, 361, 446, 6), (91, 446, 271, 566, 2), (44, 566, 334, 1000, 4), (33, 770, 180, 862, 2)], None, 1.0),
 ('B7', 'УНИ'):  (f'{V25}/B7_УНИ.png', False, [(2, 330, 612, 860, 22)], (0, 335), 1.0),
}
for (code, sec), (src, drop, parts, keep, scale) in JOBS.items():
    rgb, a = load(src, drop)
    if code == 'N10':                                            # measured on the cut-out crop; align the source crop the same way
        ys, xs = np.where(a > 0.5); rgb, a = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1], a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgb, a2 = rectify(rgb, a, parts, keep)
    if code == 'N10':                                            # thin warm rim so the black bottle stands off the panel
        sol = (a2 > 0.5).astype(np.uint8); rim = cv2.GaussianBlur((sol - cv2.erode(sol, np.ones((3, 3), np.uint8), iterations=3)).astype(np.float32), (0, 0), 1.2)*(a2 > 0.3)
        rgb = rgb*(1 - 0.7*rim[..., None]) + np.array([0.80, 0.77, 0.74])*0.7*rim[..., None]
    finish(rgb, a2, scale, f'{OUT}/{code}_{sec}.png')

# V23: the poster's grey floor band under the bottle is not part of it
rgb, a = load(f'{V25}/V23_ЖЕН.png', False)
lum = rgb.mean(axis=2); body = (lum > 0.62) & (a > 0.5); rows = np.where(body.sum(axis=1) > body.shape[1]*0.25)[0]
a[rows[-1] + 2:] = 0; finish(rgb, a, 1.0, f'{OUT}/V23_ЖЕН.png')

# black ETIB caps: the clean glass cap of the white ETIB bottle (same mould), made silver, replaces the grainy one
cap_rgb, cap_a = load(f'{OUT}/E2_ЖЕН.png', False)
w2 = (cap_a > 0.5).sum(axis=1); ys2 = np.where(w2 > 0)[0]; sh2 = [y for y in ys2 if w2[y] > 0.7*w2.max()][0]
cap_rgb, cap_a = cap_rgb[:sh2], cap_a[:sh2]
g = cap_rgb.mean(axis=2, keepdims=True); cap_rgb = g + (cap_rgb - g)*0.08                # gold collar -> silver
for code in ('E3', 'E4'):
    rgb, a = load(f'{V25}/{code}_ПРЕ.png', False)
    w3 = (a > 0.5).sum(axis=1); ys3 = np.where(w3 > 0)[0]; sh3 = [y for y in ys3 if w3[y] > 0.7*w3.max()][0]
    k = (sh3 - ys3[0] + 6)/cap_a.shape[0]
    cw, ch = round(cap_a.shape[1]*k), round(cap_a.shape[0]*k)
    ci = Image.fromarray((np.dstack([cap_rgb, cap_a])*255).astype(np.uint8), 'RGBA').resize((cw, ch), Image.LANCZOS)
    cr = np.array(ci).astype(np.float32)/255
    cx = (np.where(a[sh3 + 10] > 0.5)[0].min() + np.where(a[sh3 + 10] > 0.5)[0].max())//2
    top = sh3 + 6 - ch; pad = max(0, -top)
    H2 = a.shape[0] + pad; rgb2 = np.zeros((H2, a.shape[1], 3), np.float32); a2 = np.zeros((H2, a.shape[1]), np.float32)
    rgb2[pad:], a2[pad:] = rgb, a; top += pad; sh3 += pad
    a2[:sh3 - 2] = 0                                                              # old cap goes
    x0 = cx - cw//2; ca = cr[..., 3]
    region = (slice(top, top + ch), slice(x0, x0 + cw))
    a_old = a2[region]; rgb2[region] = cr[..., :3]*ca[..., None] + rgb2[region]*(1 - ca[..., None])*(a_old[..., None] > 0)
    a2[region] = np.maximum(a_old*(np.arange(ch)[:, None] + top >= sh3 - 2), ca)
    finish(rgb2, a2, 1.0, f'{OUT}/{code}_ПРЕ.png')
print('fixed:', [k[0] for k in JOBS] + ['V23', 'E3', 'E4'])
