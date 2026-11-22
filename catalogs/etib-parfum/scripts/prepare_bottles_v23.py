"""Bottle cut-outs for catalogue v23 (owner's review of v22).
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
    return a*(1 - strength*zone*neutral*white)

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
       ('S3', 'ПРЕ', 'S3', True, None), ('S4', 'ПРЕ', 'S4', True, None), ('S16', 'ЖЕН', 'S16', False, None)]
done = {}
for code, sec, up, fill, cap in NEW:
    if up not in done:
        rgb, a = rembg_cut(f'{UP}/{up}.png'); a = keep_main(a)
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
        if cap: a = glassify(rgb, a, cap)
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
    a = glassify(rgb, a, 0.30 if src[0] == 'E2' else 0.30, strength=0.70)
    finish(rgb, a, 1.0).save(f'{OUT}/{code}_{sec}.png')
print('done:', sorted(os.listdir(OUT)))
