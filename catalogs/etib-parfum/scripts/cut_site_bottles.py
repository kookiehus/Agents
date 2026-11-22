"""Cut the bottles out of the site catalogue photos (bottle on pure black, 360x480) -> transparent PNG, upscaled x2.
Usage: cut_site_bottles.py <map.json> <photos root> <out dir>"""
import sys, os, json, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
mp, root, out = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
HOLES = {'H4|ЖЕН', 'H14|ЖЕН', 'M5|ЖЕН', 'M20|ЖЕН', 'M17|УНИ', 'P15|МУЖ'}   # openings (cord loop, pendant, trophy handles) stay see-through
def cut(path, holes=False):
    im = np.array(Image.open(path).convert('RGB')).astype(np.float32)/255
    corners = np.concatenate([im[:4, :4].reshape(-1, 3), im[:4, -4:].reshape(-1, 3), im[-4:, :4].reshape(-1, 3), im[-4:, -4:].reshape(-1, 3)])
    white = corners.mean() > 0.85
    if white: im = 1 - im                                                     # photo on white: invert, cut as on black, invert back
    mx = im.max(axis=2); h, w = mx.shape
    bg0 = mx <= (14 if white else 6)/255
    lab, n = nd.label(bg0); border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    if holes:
        dk = mx <= 40/255; lab_, n_ = nd.label(dk)                             # dark enclosed openings (loop, handles) also go
        edge_ = set(np.unique(np.concatenate([lab_[0], lab_[-1], lab_[:, 0], lab_[:, -1]]))) - {0}
        szs = nd.sum(dk, lab_, range(1, n_ + 1)); open_ = np.isin(lab_, [i + 1 for i, s_ in enumerate(szs) if s_ > 300 and (i + 1) not in edge_])
        obj = ~bg0 & ~open_; small = nd.binary_fill_holes(obj) & ~obj; lab_, n_ = nd.label(small)
        if n_: sz_ = nd.sum(small, lab_, range(1, n_ + 1)); obj = obj | np.isin(lab_, [i + 1 for i, s_ in enumerate(sz_) if s_ < 120])
    else: obj = nd.binary_fill_holes(~bg)
    lab, n = nd.label(obj)
    if n > 1:
        sz = nd.sum(obj, lab, range(1, n+1)); obj = np.isin(lab, [i+1 for i, s in enumerate(sz) if s > 0.004*obj.sum()])
    obj = nd.binary_opening(obj, iterations=1)
    if not holes: obj = nd.binary_fill_holes(obj)
    # soft edge: on black, observed = alpha * colour; colour taken from the nearest solid pixel inside
    inner = nd.binary_erosion(obj, iterations=3)
    idx = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    ref = im[idx[0], idx[1]]; refl = np.maximum(ref.max(axis=2), 1e-3)
    a = np.clip(mx/refl, 0, 1)
    band = obj & ~inner
    dark_ref = refl < 0.10                                                     # dark glass: brightness can't tell the edge, use the shape
    alpha = np.where(inner, 1.0, np.where(band, np.where(dark_ref, 1.0, a), 0.0))
    alpha = np.where(obj & ~band, 1.0, alpha)
    # smooth, even outline: blur the shape a little and re-tighten, never wider than the object
    shape = cv2.GaussianBlur(obj.astype(np.float32), (0, 0), 1.1); shape = np.clip((shape - 0.5)*2.2 + 0.5, 0, 1)
    alpha = np.minimum(alpha, shape) * (shape > 0.02)
    col = np.where(alpha[..., None] > 0.15, np.clip(im/np.maximum(alpha[..., None], 1e-3), 0, 1), ref)
    col = np.where(band[..., None], np.minimum(col, np.maximum(ref, im)), col)
    if white: ref = ref
    if white: col = 1 - col
    rgba = np.dstack([col, alpha])
    ys, xs = np.where(alpha > 0.02); y0, y1, x0, x1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
    rgba = rgba[y0:y1, x0:x1]
    img = Image.fromarray((rgba*255).astype(np.uint8), 'RGBA')
    big = img.resize((img.width*2, img.height*2), Image.LANCZOS)
    rgb = big.convert('RGB').filter(ImageFilter.UnsharpMask(1.4, 55, 2)); big = Image.merge('RGBA', (*rgb.split(), big.getchannel('A')))
    touches = y0 <= 1 or x0 <= 1 or y1 >= h-1 or x1 >= w-1
    return big, touches
m = json.load(open(mp)); rep = {}
for key, rel in m.items():
    code, sec = key.split('|'); im, t = cut(os.path.join(root, rel), key in HOLES)
    fn = f"{out}/{code}_{sec}.png"; im.save(fn); rep[key] = dict(file=fn, touches=bool(t))
json.dump(rep, open(f'{out}/index.json', 'w'), ensure_ascii=False, indent=0)
print(len(rep), 'cut;', 'touch the photo edge:', [k for k, v in rep.items() if v['touches']])
