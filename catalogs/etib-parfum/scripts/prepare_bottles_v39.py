"""v39 (cap rim darkened) / v37: A2 Avril Lavigne Forbidden Rose from the owner's photo, rebuilt for clean corners.
- body outline = polygon measured on the photo (anti-aliased, drawn 4x and reduced): straight sides, sharp corners;
- rose cap keeps its own (smoothed) outline;
- the white backdrop seen through the clear glass came out as ragged white streaks: those pixels are replaced by a
  smooth glass tone (blurred image of the glass itself), so the glass reads clean; a thin even rim marks the corners.
Usage: prepare_bottles_v37.py <upload png> <out png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
src, out = sys.argv[1:3]
im = Image.open(src).convert('RGB'); rgb = np.array(im).astype(np.float32)/255; h, w = rgb.shape[:2]
cap = np.array(remove(im, session=new_session('isnet-general-use')).getchannel('A')).astype(np.float32)/255
BODY = [(118, 358), (262, 352), (350, 398), (361, 418), (359, 440), (300, 893), (293, 905), (249, 964), (238, 968),
        (90, 925), (80, 906), (18, 440), (20, 424), (32, 410), (108, 364)]
K = 4
def aa_poly(pts):
    m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.array([(x*K, y*K) for x, y in pts], np.int32)], 255)
    return cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
body = aa_poly(BODY)
capm = cap.copy(); capm[356:] = 0
capm = cv2.GaussianBlur((capm > 0.5).astype(np.float32), (0, 0), 1.6); capm = np.clip((capm - 0.5)*2 + 0.5, 0, 1)
a = np.maximum(body, capm)
# smooth glass tone instead of ragged backdrop streaks
inb = body > 0.5
mn, mx = rgb.min(axis=2), rgb.max(axis=2)
backdrop = inb & (mn > 0.78) & ((mx - mn) < 0.07)
keep = inb & ~backdrop
blur = np.dstack([nd.gaussian_filter(rgb[..., i]*keep, 9) for i in range(3)]) / np.maximum(nd.gaussian_filter(keep.astype(np.float32), 9), 1e-3)[..., None]
blur = np.where(np.isfinite(blur), blur, rgb)
glass = blur*0.55 + np.array([0.80, 0.79, 0.84])*0.45                      # pale lilac-grey clear glass
wgt = cv2.GaussianBlur(backdrop.astype(np.float32), (0, 0), 1.5)[..., None]
rgb = rgb*(1 - wgt) + glass*wgt
# pixels outside the photo's object but inside the polygon (corners): same glass tone
outside = (body > 0.02) & (cap < 0.5) & (np.arange(h)[:, None] >= 356)
rgb = np.where((outside & backdrop)[..., None] | (outside & (mn > 0.7))[..., None], glass, rgb)
# clean glass edge: a band along the outline gets a smooth tone sampled further inside (no ragged backdrop bits)
dist = nd.distance_transform_edt(body > 0.5)
src_zone = ((dist > 11) & (dist < 20)).astype(np.float32)
samp = np.dstack([nd.gaussian_filter(rgb[..., i]*src_zone, 10) for i in range(3)]) / np.maximum(nd.gaussian_filter(src_zone, 10), 1e-4)[..., None]
band = np.clip((11 - dist)/4, 0, 1)[..., None]*(body > 0.02)[..., None]
edge_tone = samp*0.75 + np.array([0.86, 0.85, 0.90])*0.25
rgb = rgb*(1 - band) + edge_tone*band
# rose cap: edge pixels take the cap's own colour, outline smoothed (no light fringe)
capcore = nd.binary_erosion(capm > 0.5, iterations=3)
if capcore.any():
    ci = nd.distance_transform_edt(~capcore, return_distances=False, return_indices=True)
    capedge = (capm > 0.02) & ~capcore & (np.arange(h)[:, None] < 356)
    rgb = np.where(capedge[..., None], rgb[ci[0], ci[1]], rgb)
    # v39: no light streak down the cap's side: the outer ~12 px may not be lighter than the cap's own tone
    # 12 px further in (nearest pixel of the shrunk cap), so the side ends dark and even, as in the photo
    cin = (capm > 0.5) & (np.arange(h)[:, None] < 356)
    deep = nd.binary_erosion(cin, iterations=12)
    dd, (di, dj) = nd.distance_transform_edt(~deep, return_indices=True)
    ref = rgb[di, dj]
    ref = np.dstack([cv2.GaussianBlur(ref[..., c], (0, 0), 2.0) for c in range(3)])
    cd = nd.distance_transform_edt(cin)
    wz = np.clip((14 - cd)/4, 0, 1)*(capm > 0.02)*(np.arange(h)[:, None] < 350)*np.clip((18 - dd)/3, 0, 1)  # thin petals keep their own light
    wz = cv2.GaussianBlur(wz.astype(np.float32), (0, 0), 0.8)[..., None]
    rim_d = np.clip((5 - cd)/5, 0, 1)[..., None]*wz                                    # glossy black: side turns darker toward the edge
    rgb = (rgb*(1 - wz) + np.minimum(rgb, ref)*wz)*(1 - 0.45*rim_d)
# thin even rim along the body outline
sol = (body > 0.5).astype(np.uint8); rim = cv2.GaussianBlur((sol - cv2.erode(sol, np.ones((3, 3), np.uint8), iterations=2)).astype(np.float32), (0, 0), 0.7)
rgb = rgb*(1 - 0.55*rim[..., None]) + np.array([0.93, 0.92, 0.95])*0.55*rim[..., None]
# colour bleeds out under the transparent part, so denoising/resizing/sharpening cannot pull the white backdrop into the edge
solid = a > 0.6
bi = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
rgb = np.where(solid[..., None], rgb, rgb[bi[0], bi[1]])
u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8); rgb = cv2.fastNlMeansDenoisingColored(u8, None, 4, 4, 5, 15).astype(np.float32)/255
ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(out); print(img.size)
