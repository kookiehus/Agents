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

# simple studio shots
for name, out, kw in (('A17', 'A17_МУЖ.png', dict(rim=0.20)), ('A1', 'A1_МУЖ.png', {}), ('D9', 'D9_ЖЕН.png', {})):
    rgb, cut = load(name); a = smooth_mask(cut > 0.45)
    finish(rim(fill_own(rgb, cut, a), a, 3), a, out, **kw)

# L8 La Vie Est Belle on flat light grey: the clear lower glass defeats rembg; mask = everything that differs from the grey,
# the glass keeps the photo's own pixels (no edge recolouring inside the clear part)
rgb, cut = load('L8'); bg = np.median(rgb[:20, :20].reshape(-1, 3), axis=0)
m = np.abs(rgb - bg).max(axis=2) > 7/255; m = nd.binary_closing(m, iterations=3)
a = smooth_mask(m, 1.4)
finish(rim(rgb, a, 3), a, 'L8_ЖЕН.png')

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
body = down(poly_mask(h, w, [(xl + 64, yt), (xr - 62, yt), (xr, yt + 84), (xr, yb - 50), (xr - 42, yb), (xl + 42, yb), (xl, yb - 60), (xl, yt + 80)], 3), h, w)
capm = (cut > 0.5); capm[:250] = False; capm[420:] = False; capm[:, :505] = False; capm[:, 765:] = False
cap = (down(poly_mask(h, w, [(564, 259), (660, 259), (706, 335), (676, 408), (548, 408), (518, 335)], 2), h, w))
neck = down(poly_mask(h, w, [(547, 400), (677, 400), (677, 496), (547, 496)], 2), h, w)
cap = np.maximum(cap, neck)
a = np.maximum(body, cap)
red = (rgb[..., 0] - rgb[..., 1] > 0.22) & (a > 0.02)          # strawberry pixels where the fruit touches the bottle
red = nd.binary_dilation(red, iterations=3)
good = (a > 0.5) & ~red; gi = nd.distance_transform_edt(~good, return_distances=False, return_indices=True)
rgb = np.where(red[..., None], rgb[gi[0], gi[1]], rgb); rgb = np.where(red[..., None], cv2.GaussianBlur(rgb, (0, 0), 2.0), rgb)
def gentle(rgb, a, name, contrast=1.06):
    """Pastel bottles: no levels stretch (it turns soft pink into raspberry); only a touch of contrast and sharpening."""
    from PIL import ImageEnhance
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c = ImageEnhance.Contrast(img.convert('RGB')).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/{name}'); print(name, img.size)
gentle(rim(rgb, a, 7), a, 'K2_ЖЕН.png')

# E33 Essential Parfums: rectangular glass block with rounded corners + cylindrical cap (wood shavings touch the glass)
rgb, cut = load('E33'); h, w = cut.shape
body = down(poly_mask(h, w, [(330.5, 316.0), (590.5, 316.0), (590.5, 720.0), (330.5, 720.0)], 16), h, w)
cap = down(poly_mask(h, w, [(387.0, 183.0), (531.5, 183.0), (531.5, 322.0), (387.0, 322.0)], 4), h, w)
a = np.maximum(body, cap)
finish(rim(fill_own(rgb, cut, a), a, 4), a, 'E33_УНИ.png', lift=0.97)
