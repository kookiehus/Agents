"""v74: owner's photos for A17 Armani Code Parfum, K2 Kayali Yum Boujee Marshmallow 81, E33 Essential Parfums Bois Imperial,
D18 Alfred Dunhill Desire Blue, A1 Antonio Banderas King of Seduction, L8 Lancome La Vie Est Belle, D9 Miss Dior Blooming
Bouquet. Studio shots: rembg cut-out, holes filled, smooth outline (D18: cut above its reflection). K2 and E33 lie among
props (strawberries, marshmallows, wood shavings): their outline is exact geometry measured on the photo.
Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v74.py <uploads dir> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, poly_mask, down, smooth_part, finish ...

def fill_own(rgb, cut, a):
    own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
    return np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
def smooth_mask(m, sigma=1.6):
    m = nd.binary_fill_holes(m); m = nd.binary_opening(m, iterations=2)
    lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    p = cv2.GaussianBlur(m.astype(np.float32), (0, 0), sigma); return np.clip((p - 0.5)*2.2 + 0.5, 0, 1)
def rim(rgb, a, band, dark=0.06):
    d = nd.distance_transform_edt(a > 0.5); core = d > band
    idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
    t = np.clip((band + 1 - d)/band, 0, 1)[..., None]
    return rgb*(1 - t) + rgb[idx[0], idx[1]]*(1 - dark*t)*t

def gentle(rgb, a, name, contrast=1.06):
    """Pastel bottles: no levels stretch (it turns soft pink into raspberry); only a touch of contrast and sharpening."""
    from PIL import ImageEnhance
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c = ImageEnhance.Contrast(img.convert('RGB')).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/{name}'); print(name, img.size)

# simple studio shots
for name, out, kw in (('A17', 'A17_МУЖ.png', dict(rim=0.20)), ('A1', 'A1_МУЖ.png', {})):
    rgb, cut = load(name); a = smooth_mask(cut > 0.45)
    finish(rim(fill_own(rgb, cut, a), a, 3), a, out, **kw)

# L8 La Vie Est Belle on flat light grey: exact geometry (the clear glass defeats any mask): straight-sided glass block with
# rounded corners, square cap, neck with the knurled ring; the grey ribbon is taken from the colour mask. Glass keeps its own pixels.
rgb, cut = load('L8'); h, w = cut.shape; bg = np.median(rgb[:20, :20].reshape(-1, 3), axis=0)
cm = np.abs(rgb - bg).max(axis=2) > 7/255; cm = nd.binary_closing(cm, iterations=3); cm = nd.binary_fill_holes(cm)
body = down(poly_mask(h, w, [(545.5, 381.0), (1061.5, 381.0), (1061.5, 949.5), (545.5, 949.5)], 22), h, w)
capL8 = down(poly_mask(h, w, [(712.0, 147.0), (890.5, 147.0), (890.5, 242.0), (712.0, 242.0)], 4), h, w)
neck = down(poly_mask(h, w, [(737.0, 236.0), (865.0, 236.0), (865.0, 384.0), (737.0, 384.0)], 2), h, w)
rib = cm.copy(); rib[:236] = False; rib[392:] = False; rib[:, :862] = False
rib = smooth_mask(rib, 1.2)
a = np.maximum.reduce([body, capL8, neck, rib])
gentle(rim(rgb, a, 2, dark=0.0), a, 'L8_ЖЕН.png', contrast=1.08)

# D9 Miss Dior on white: straight-sided glass block (exact), bow and cap from the cut-out; softer tone so it does not shout
rgb, cut = load('D9'); h, w = cut.shape
top = smooth_mask(cut > 0.45); top[600:] = 0
body = down(poly_mask(h, w, [(51.5, 560.0), (901.5, 560.0), (901.5, 1431.0), (51.5, 1431.0)], 26), h, w)
a = np.maximum(np.minimum(top, 1), body)
rgb = fill_own(rgb, cut, a)
lumD = rgb.mean(axis=2, keepdims=True); rgb = np.clip(lumD + (rgb - lumD)*0.80, 0, 1)*0.97      # calmer pink
dD = nd.distance_transform_edt(a > 0.5); whiteD = (rgb.min(axis=2) > 0.80) & (dD < 40) & (np.arange(h)[:, None] > 560)   # white photo background seen through the thick glass walls
wgt = (whiteD*np.clip((40 - dD)/40, 0, 1))[..., None]; wgt = cv2.GaussianBlur(wgt[..., 0].astype(np.float32), (0, 0), 2)[..., None]
rgb = rgb*(1 - wgt*0.42) + np.array([0.08, 0.06, 0.07])*wgt*0.42
gentle(rim(rgb, a, 3), a, 'D9_ЖЕН.png', contrast=1.04)

# D18 on black with a mirror floor: cut just under the glass base
rgb, cut = load('D18'); h, w = cut.shape
m = cut > 0.45; wd = np.array([np.count_nonzero(r) for r in m])
lum = rgb[:, w//3:2*w//3].mean(axis=(1, 2)); y0 = int(h*0.80)
ybot = y0 + int(np.argmin(lum[y0:int(h*0.97)]))            # dark gap between the base and the reflection
m[ybot:] = False; a = smooth_mask(m); a[ybot:] = 0
finish(rim(fill_own(rgb, cut, a), a, 3), a, 'D18_МУЖ.png'); print('D18 cut at', ybot)

# K2 Kayali: faceted octagonal block + white faceted cap (strawberries and marshmallows touch it)
rgb, cut = load('K2'); h, w = cut.shape
xl, xr, yt, yb = 417.0, 828.5, 493.0, 1101.5
body = down(poly_mask(h, w, [(xl + 80, yt), (xr - 78, yt), (xr, yt + 100), (xr, yb - 66), (xr - 56, yb), (xl + 56, yb), (xl, yb - 74), (xl, yt + 96)], 3), h, w)
capm = (cut > 0.5); capm[:250] = False; capm[420:] = False; capm[:, :505] = False; capm[:, 765:] = False
cap = (down(poly_mask(h, w, [(564, 259), (660, 259), (706, 335), (676, 408), (548, 408), (518, 335)], 2), h, w))
neck = down(poly_mask(h, w, [(547, 400), (677, 400), (677, 496), (547, 496)], 2), h, w)
cap = np.maximum(cap, neck)
a = np.maximum(body, cap)
red = (rgb[..., 0] - rgb[..., 1] > 0.22) & (a > 0.02)          # strawberry pixels where the fruit touches the bottle
red = nd.binary_dilation(red, iterations=3)
good = (a > 0.5) & ~red; gi = nd.distance_transform_edt(~good, return_distances=False, return_indices=True)
rgb = np.where(red[..., None], rgb[gi[0], gi[1]], rgb); rgb = np.where(red[..., None], cv2.GaussianBlur(rgb, (0, 0), 2.0), rgb)
# the bevelled corner facets mirror the beige table: paint them in the body colour sampled further inside
corners = [((xl + 80, yt), (xl, yt + 96)), ((xr - 78, yt), (xr, yt + 100)), ((xr, yb - 66), (xr - 56, yb)), ((xl + 56, yb), (xl, yb - 74))]
yy_, xx_ = np.mgrid[0:h, 0:w]; facet = np.zeros((h, w), bool)
for (x1_, y1_), (x2_, y2_) in corners:
    dx, dy = x2_ - x1_, y2_ - y1_; L_ = np.hypot(dx, dy)
    dist = np.abs((xx_ - x1_)*dy - (yy_ - y1_)*dx)/L_; tpar = ((xx_ - x1_)*dx + (yy_ - y1_)*dy)/L_**2
    facet |= (dist < 34) & (tpar > -0.25) & (tpar < 1.25)
facet &= (a > 0.02) & (yy_ > yt - 2)
good = (a > 0.5) & ~facet & (yy_ > yt + 4); gi = nd.distance_transform_edt(~good, return_distances=False, return_indices=True)
rgb = np.where(facet[..., None], rgb[gi[0], gi[1]], rgb); rgb = np.where(facet[..., None], cv2.GaussianBlur(rgb, (0, 0), 3.0), rgb)
gentle(rim(rgb, a, 9), a, 'K2_ЖЕН.png')

# E33 Essential Parfums: rectangular glass block with rounded corners + cylindrical cap (wood shavings touch the glass)
rgb, cut = load('E33'); h, w = cut.shape
body = down(poly_mask(h, w, [(330.5, 316.0), (590.5, 316.0), (590.5, 720.0), (330.5, 720.0)], 16), h, w)
cap = down(poly_mask(h, w, [(387.0, 183.0), (531.5, 183.0), (531.5, 322.0), (387.0, 322.0)], 4), h, w)
a = np.maximum(body, cap)
finish(rim(fill_own(rgb, cut, a), a, 4), a, 'E33_УНИ.png', lift=0.97)
