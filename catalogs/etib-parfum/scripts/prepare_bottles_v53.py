"""v53 (v52 + E25 outline: seam notches filled, smooth dip, wider edge recolour; v52: V15 photo, edge colour fix for E9 / E22 / E25): owner's photos for E9 Escada Sexy Graffiti, E22 Escada Flor del Sol, E25 Escada Candy Love, V25 Victoria's Secret
Velvet Petals, V15 Versace Dylan Purple; S2 Scandalous: grey shadow under the glass removed, clean rounded bottom edge.
E9 / E22: rembg cut-out, holes filled, outline smoothed. E25: pink heart on pure white, mask by distance from white,
reflection under the base cut off. V25: exact geometry (straight-sided body with rounded corners, collar, cap fitted to the
cut-out) because the splash and flowers touch the bottle. Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v53.py <uploads dir: E9.jpg E22.jpg E25.jpg V25.jpg V15.jpg> <data dir> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
UP, DATA, OUT = sys.argv[1:4]; sys.argv[1:] = [UP, OUT]
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...

def fill_own(rgb, cut, a):
    own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
    return np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)

def rim(rgb, a, band, dark=0.12, amt=1.0):
    """Outer `band` px take the colour found `band` px inside (removes background glow / white flecks), slightly darker
    at the very edge like glass on a dark panel."""
    solid = a > 0.5; d = nd.distance_transform_edt(solid)
    core = d > band; idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
    t = np.clip((band + 1 - d)/band, 0, 1)[..., None]*amt
    inner = rgb[idx[0], idx[1]]*(1 - dark*t)
    return rgb*(1 - t) + inner*t

def smooth_all(cut, sigma):
    m = nd.binary_fill_holes(cut > 0.35).astype(np.float32)
    m = nd.binary_opening(m > 0.5, iterations=2).astype(np.float32)
    p = cv2.GaussianBlur(m, (0, 0), sigma); return np.clip((p - 0.5)*2.2 + 0.5, 0, 1)

# E9 Sexy Graffiti and E22 Flor del Sol: teardrop bottles, smooth outline; the pink / orange background glow on the
# glass edge and the yellow strip on the left of the E22 cap are replaced with the bottle's own colour
for name, sig, band, lift in (('E9', 2.0, 6, 0.96), ('E22', 1.6, 7, 0.93)):
    rgb, cut = load(name); a = smooth_all(cut, sig)
    rgb = rim(fill_own(rgb, np.maximum(cut, nd.binary_fill_holes(cut > 0.35)), a), a, band, dark=0.18)
    finish(rgb, a, f'{name}_ЖЕН.png', lift=lift)

# E25 Candy Love: soft-touch pink heart on white
im = np.array(Image.open(f'{UP}/E25.jpg').convert('RGB')).astype(np.float32)/255
dist = 1 - im.min(axis=2); m = nd.binary_fill_holes(dist > 0.09)
lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
w = np.array([np.count_nonzero(r) for r in m]); ys = np.where(w > 0)[0]
ybot = 740 + int(np.argmin(w[740:800]))                    # narrowest row = foot of the base (reflection widens below it)
m[ybot + 1:] = False
disk = lambda r: np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
m = nd.binary_closing(np.pad(m, 30), disk(14))[30:-30, 30:-30] | m      # fills the notches where the seam meets the edge
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3.0) > 0.5             # smooth outline, no jagged white bits in the dip
m = nd.binary_erosion(m, disk(2)); m[ybot + 1:] = False
a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1); a[ybot + 1:] = 0
de = nd.distance_transform_edt(m)
ys_ = np.arange(m.shape[0])[:, None]
sy = 480 + int(np.argmax([np.count_nonzero(m[y] & (dist[y] < 0.12)) for y in range(480, 600)]))   # row of the pale seam line
bad = ((dist < 0.16) & (de < 45)) | ((im[..., 1] > 0.49) & (de < 90) & (np.abs(ys_ - sy) <= 10))   # white wedges at the seam ends, white in the dip
good = m & ~bad; gi = nd.distance_transform_edt(~good, return_distances=False, return_indices=True)
im = np.where(bad[..., None], im[gi[0], gi[1]], im)
im = np.where(bad[..., None], cv2.GaussianBlur(im, (0, 0), 2.0), im)
finish(rim(im, a, 11, dark=0.06), a, 'E25_ЖЕН.png', lift=0.97)

# V25 Velvet Petals: clear body mist bottle
rgb, cut = load('V25'); h, w = cut.shape
body = box(h, w, fit(cut, range(260, 800, 4), 'l'), fit(cut, range(260, 800, 4), 'r'), 209.0, 843.5, 16)
collar = box(h, w, fit(cut, range(198, 206), 'l'), fit(cut, range(198, 206), 'r'), 190.0, 214.0, 1)
cap = smooth_all(np.where(np.arange(h)[:, None] < 196, cut, 0), 1.2)
a = np.maximum(np.maximum(body, collar), cap)
finish(fill_own(rgb, cut, a), a, 'V25_ЖЕН.png')

# V15 Dylan Purple: owner's photo on flat light grey; mask by distance from the background, trapezoid cap kept straight
rgb = np.array(Image.open(f'{UP}/V15.jpg').convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
m = nd.binary_fill_holes(np.abs(rgb - rgb[5, 5]).max(axis=2) > 12/255)
lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
m = nd.binary_erosion(m, iterations=3)                    # drop the anti-aliased grey rim of the photo
cut = m.astype(np.float32)
cap = box(h, w, fit(cut, range(60, 255, 3), 'l'), fit(cut, range(60, 255, 3), 'r'), 37.0, 268.0, 3)
rest = smooth_all(np.where(np.arange(h)[:, None] >= 262, cut, 0), 1.4)
top = smooth_all(np.where(np.arange(h)[:, None] < 40, cut, 0), 1.0)
a = np.maximum(np.maximum(cap, rest), top)
finish(rim(fill_own(rgb, cut, a), a, 7, dark=0.12), a, 'V15_ЖЕН.png', lift=0.98)

# S2 Scandalous: cut the old grey shadow below the glass, rounded bottom corners
im = Image.open(f'{DATA}/bottles_site/S2_ЖЕН.png').convert('RGBA'); arr = np.array(im).astype(np.float32)/255
h, w = arr.shape[:2]; YB, R = 847.5, 60
clip = down(poly_mask(h, w, [(0.5, 430), (484.5, 430), (484.5, YB), (0.5, YB)], R), h, w)
clip[:760] = 1
arr[..., 3] *= clip
Image.fromarray((np.clip(arr, 0, 1)*255).astype(np.uint8), 'RGBA').save(f'{OUT}/S2_ЖЕН.png'); print('S2_ЖЕН.png', im.size)
