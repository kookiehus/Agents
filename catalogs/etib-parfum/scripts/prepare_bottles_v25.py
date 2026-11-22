"""Bottle cut-outs for catalogue v25 (v23 + second review) (owner's review of v22).
- owner's new photos (white / scene backgrounds) cut with rembg (isnet-general-use), edges cleaned and un-haloed;
- opaque bottles get their inside filled (rembg made the middle of Delina see-through);
- Pacific Chill: the stone under the bottle is cut away;
- clear glass caps (Coco Mademoiselle, ETIB bottles) turned see-through so the dark panel shows through them;
- ETIB bottles: the white ETIB bottle for the women's ETIB fragrances (also B18), the black one for E3/E4.
Usage: prepare_bottles_v23.py <data dir> <uploads dir> <out dir>"""
import sys, os, json, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
D, UP, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)

def smooth_alpha(a):
    """Even outline: slight blur, re-tightened; keeps soft anti-aliasing, removes jaggies and 1-px whiskers."""
    a = cv2.GaussianBlur(a, (0, 0), 0.9)
    return np.clip((a - 0.5)*1.8 + 0.5, 0, 1)

def decontaminate(rgb, a):
    """Edge pixels take the colour of the nearest solid pixel inside (no white / scene fringe)."""
    solid = a > 0.97
    if not solid.any(): return rgb
    idx = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    ref = rgb[idx[0], idx[1]]
    w = np.clip((0.97 - a)/0.5, 0, 1)[..., None]
    return rgb*(1 - w) + ref*w

def glassify(rgb, a, top_frac, bottom_frac=0.0, strength=0.72):
    """Clear glass shot on white: bright neutral pixels in the cap zone become see-through, facet lines stay."""
    ys = np.where(a.max(axis=1) > 0.5)[0]; y0, y1 = ys[0], ys[-1]
    zone = np.zeros(a.shape, np.float32); zone[int(y0 + (y1 - y0)*bottom_frac):int(y0 + (y1 - y0)*top_frac)] = 1
    zone = cv2.GaussianBlur(zone, (0, 0), 3)
    mn, mx = rgb.min(axis=2), rgb.max(axis=2)
    neutral = np.clip((0.10 - (mx - mn))/0.05, 0, 1)
    t = np.clip((mn - 0.62)/0.33, 0, 1); white = t*t*(3 - 2*t)
    a = a*(1 - strength*zone*neutral*white)
    return a

def facets(rgb, a, top_frac, gain=1.0):
    """Facet lines of a clear cap read as light edges on the dark panel (as real glass does)."""
    ys = np.where(a.max(axis=1) > 0.3)[0]; y0, y1 = ys[0], ys[-1]
    zone = np.zeros(a.shape, np.float32); zone[y0:int(y0 + (y1 - y0)*top_frac)] = 1; zone = cv2.GaussianBlur(zone, (0, 0), 3)
    lum = rgb.mean(axis=2).astype(np.float32)
    g = np.hypot(cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3))
    edge = cv2.GaussianBlur(np.clip(g/0.9, 0, 1), (0, 0), 0.6)*zone*(a > 0.02)
    sol = (a > 0.3).astype(np.uint8); rim = sol - cv2.erode(sol, np.ones((3, 3), np.uint8), iterations=2)
    edge = np.maximum(edge, cv2.GaussianBlur(rim.astype(np.float32), (0, 0), 0.8)*zone*0.9)*gain
    edge = np.clip(edge, 0, 1)
    rgb = rgb*(1 - edge[..., None]) + np.array([0.96, 0.95, 0.94])*edge[..., None]
    return rgb, np.maximum(a, 0.85*edge)

def hull_bands(rgb, a, skip_top=0.0):
    """Even, straight outline for boxy bottles: each horizontal band (cap, neck, body) is replaced by its convex hull."""
    m = (a > 0.5).astype(np.uint8); w = m.sum(axis=1).astype(float); ys = np.where(w > 0)[0]
    ws = nd.uniform_filter1d(w, 5); cuts = [ys[0]]
    for y in range(ys[0] + 4, ys[-1]):
        if abs(ws[y] - ws[y - 4]) > 0.10*w.max() and y - cuts[-1] > 12: cuts.append(y)
    cuts.append(ys[-1] + 1); y_skip = ys[0] + (ys[-1] - ys[0])*skip_top
    out = a.copy()
    for t, b in zip(cuts[:-1], cuts[1:]):
        if b <= y_skip: continue
        band = np.zeros_like(m); band[t:b] = m[t:b]
        cnts, _ = cv2.findContours(band, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts: continue
        hull = cv2.convexHull(np.vstack(cnts)); hm = np.zeros_like(m); cv2.fillPoly(hm, [hull], 1); hm[:t] = 0; hm[b:] = 0
        out[t:b] = np.where(hm[t:b] > 0, 1.0, 0.0)                                # band = its hull, nothing outside
    new = (out > 0.5) & (a < 0.5); solid = a > 0.9                               # pixels the hull added take the bottle's own colour
    if new.any() and solid.any():
        idx = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True); rgb = np.where(new[..., None], rgb[idx[0], idx[1]], rgb)
    out = smooth_alpha(out.astype(np.float32))
    return decontaminate(rgb, out), out

def trim_white_bottom(rgb, a):
    """Remove light rows at the very bottom (white backdrop seen through the glass base)."""
    ys = np.where(a.max(axis=1) > 0.5)[0]
    for y in range(ys[-1], ys[0] + (ys[-1] - ys[0])//2, -1):
        row = a[y] > 0.5
        if row.sum() and np.median(rgb[y][row].min(axis=1)) < 0.80: break
        a[y] = 0
    return a

def rim_light(rgb, a, strength=0.45):
    """Thin warm-white rim along the outline so a dark bottle stands off the dark panel."""
    sol = (a > 0.5).astype(np.uint8); inner = cv2.erode(sol, np.ones((3, 3), np.uint8), iterations=3)
    rim = cv2.GaussianBlur((sol - inner).astype(np.float32), (0, 0), 1.2)*(a > 0.3)
    return rgb*(1 - strength*rim[..., None]) + np.array([0.80, 0.77, 0.74])*strength*rim[..., None]

def finish(rgb, a, scale):
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    if scale != 1:
        im = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
        c = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.4, 50, 2)); im = Image.merge('RGBA', (*c.split(), im.getchannel('A')))
    return im

_sess = None
def rembg_cut(path):
    global _sess
    from rembg import remove, new_session
    if _sess is None: _sess = new_session('isnet-general-use')
    src = Image.open(path).convert('RGB'); o = remove(src, session=_sess)
    rgb = np.array(src).astype(np.float32)/255; a = np.array(o.getchannel('A')).astype(np.float32)/255
    return rgb, a

def keep_main(a, frac=0.02):
    m = a > 0.5; lab, n = nd.label(m)
    if n > 1:
        sz = nd.sum(m, lab, range(1, n + 1)); keep = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > frac*m.sum()])
        a = a*nd.binary_dilation(keep, iterations=3)
    return a

# code, section, upload file, fill inside, glass cap zone (top fraction of the object) or None
NEW = [('C17', 'ЖЕН', 'C17', True, 0.30), ('E5', 'ЖЕН', 'E5', True, None), ('G22', 'ЖЕН', 'G22', True, None),
       ('P1', 'ЖЕН', 'P1', True, None), ('T15', 'ЖЕН', 'TRUSS', True, None), ('V9', 'ЖЕН', 'BOMB', False, None),
       ('V11', 'ЖЕН', 'BOMB', False, None), ('V19', 'ЖЕН', 'V19', False, None), ('V22', 'ЖЕН', 'V22', True, None),
       ('B8', 'МУЖ', 'B8', True, None), ('B7', 'УНИ', 'B7', True, None), ('R1', 'УНИ', 'R1', True, None),
       ('L4', 'ПРЕ', 'L4', True, None), ('L3', 'ПРЕ', 'L3', True, None), ('N10', 'ПРЕ', 'N10', True, None),
       ('S3', 'ПРЕ', 'S3', True, None), ('S4', 'ПРЕ', 'S4', True, None), ('S16', 'ЖЕН', 'S16', False, None), ('V23', 'ЖЕН', 'V23', True, None), ('T14', 'ПРЕ', 'T14', True, None)]
done = {}
for code, sec, up, fill, cap in NEW:
    if up not in done:
        rgb, a = rembg_cut(f'{UP}/{up}.png'); a = keep_main(a)
        if up == 'V23':                                                         # poster: keep only the bottle in the middle
            lab, n = nd.label(a > 0.5); cx = a.shape[1]//2; ids = set(np.unique(lab[:, cx])) - {0}
            a = a*nd.binary_dilation(np.isin(lab, list(ids)), iterations=3)
        if up == 'C17':                                                        # the cap's cast shadow on the white backdrop is not part of the bottle
            a[:252, :338] = 0; a[:205, 506:] = 0
        if up == 'L4':                                                         # cut the stone away: rows wider than the bottle
            m = a > 0.5; widths = m.sum(axis=1); ys = np.where(widths > 0)[0]
            mid = widths[ys[0] + (ys[-1] - ys[0])//4: ys[0] + (ys[-1] - ys[0])//2]; bw = np.median(mid)
            below = [y for y in range(ys[0] + (ys[-1] - ys[0])//2, ys[-1]) if widths[y] > bw*1.12]
            if below:
                cut = below[0] - 2; a[cut:] = 0
                xs = np.where(m[ys[0] + (ys[-1] - ys[0])//3])[0]; a[:, :max(0, xs[0] - 4)] = 0; a[:, xs[-1] + 5:] = 0
        if fill:
            inside = nd.binary_fill_holes(nd.binary_erosion(a > 0.5, iterations=2))
            a = np.maximum(a, nd.binary_erosion(inside, iterations=2).astype(np.float32))
        a = smooth_alpha(a); rgb = decontaminate(rgb, a)
        if up in ('C17',): rgb, a = hull_bands(rgb, a)
        if cap: a = glassify(rgb, a, cap, strength=0.55); rgb, a = facets(rgb, a, cap)
        if up == 'B7': a = trim_white_bottom(rgb, a)
        if up in ('T14',): rgb = rim_light(rgb, a, 0.6)
        h = np.where(a.max(axis=1) > 0.5)[0]; h = h[-1] - h[0]
        done[up] = finish(rgb, a, max(1.0, 700/h))
    done[up].save(f'{OUT}/{code}_{sec}.png')

# ETIB bottles from the original catalogue, without their baked reflection, glass cap made see-through
cards = json.load(open(f'{D}/cards.json'))
def card_file(code, sec): return f"{D}/" + [c for c in cards if c['code'] == code and c['section'].startswith(sec)][0]['bottle']['file']
for code, sec, src in [('E2', 'ЖЕН', ('E2', 'ЖЕН')), ('E20', 'ЖЕН', ('E2', 'ЖЕН')), ('S7', 'ЖЕН', ('E2', 'ЖЕН')), ('B18', 'ЖЕН', ('E2', 'ЖЕН')),
                       ('E3', 'ПРЕ', ('E3', 'ПРЕ')), ('E4', 'ПРЕ', ('E3', 'ПРЕ'))]:
    im = Image.open(card_file(*src)).convert('RGBA'); arr = np.array(im).astype(np.float32)/255
    al = arr[..., 3]; last = int(np.where(al.max(axis=1) > 0.97)[0][-1]); arr = arr[:last + 1]
    rgb, a = arr[..., :3], arr[..., 3]
    rgb, a = hull_bands(rgb, a, skip_top=0.30)                                 # straight body edges, clean bottom corners
    a = glassify(rgb, a, 0.30, strength=0.55); rgb, a = facets(rgb, a, 0.30)
    finish(rgb, a, 1.0).save(f'{OUT}/{code}_{sec}.png')

# earlier cut-outs the owner keeps, with straightened outlines / trimmed bases / rim light
def load(path, drop_reflection=True):
    arr = np.array(Image.open(path).convert('RGBA')).astype(np.float32)/255
    if drop_reflection:
        last = int(np.where(arr[..., 3].max(axis=1) > 0.97)[0][-1]); arr = arr[:last + 1]
    return arr[..., :3].copy(), arr[..., 3].copy()
for code, sec, path, ops in [('M1', 'ПРЕ', card_file('M1', 'ПРЕ'), 'hull'), ('M2', 'ПРЕ', card_file('M2', 'ПРЕ'), 'hull'),
                             ('N2', 'УНИ', card_file('N2', 'УНИ'), 'hull'), ('T1', 'МУЖ', card_file('T1', 'МУЖ'), 'hull trim'),
                             ('C36', 'МУЖ', f'{D}/bottles_site/C36_МУЖ.png', 'hull site'), ('N10', 'ПРЕ', f'{OUT}/N10_ПРЕ.png', 'hull rim site strong')]:
    rgb, a = load(path, drop_reflection='site' not in ops)
    if 'trim' in ops: a = trim_white_bottom(rgb, a)
    if 'hull' in ops: rgb, a = hull_bands(rgb, a)
    if 'rim' in ops: rgb = rim_light(rgb, a, 0.75 if 'strong' in ops else 0.45)
    finish(rgb, a, 1.0).save(f'{OUT}/{code}_{sec}.png')
print('done:', sorted(os.listdir(OUT)))
