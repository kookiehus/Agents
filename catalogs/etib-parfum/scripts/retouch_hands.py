"""Clean-up of the owner's hands picture (hands_cut_v2.png -> hands_cut_v3.png):
- black glass of the bottle: the crinkled 'lace' texture and scattered AI specks removed, the glass made smooth and glossy;
  the logo, the ETIB PARFUM lettering and the bright frame lines kept and sharpened;
- skin: blotchy AI texture smoothed with an edge-preserving filter, pores and creases softened, not erased.
Usage: retouch_hands.py <in.png> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as nd
src, out = sys.argv[1], sys.argv[2]
im = np.array(Image.open(src).convert('RGBA')).astype(np.float32)/255
C, A = im[..., :3], im[..., 3]; h, w = A.shape
lum = C.mean(axis=2); mx, mn = C.max(axis=2), C.min(axis=2)
def poly(pts, blur=0):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255); m = np.array(m).astype(np.float32)/255
    return nd.gaussian_filter(m, blur) if blur else m
# ---- bottle body (below the collar), the hands excluded by colour
body = poly([(1180, 925), (1860, 935), (1850, 1080), (1830, 1600), (1080, 1610), (1050, 1500), (1090, 1100), (1150, 940)])
neutral = (mx - mn) < 0.10
warm = (C[..., 0] - C[..., 2] > 0.08) & (lum > 0.25)
glass = (body > 0.5) & (A > 0.9) & ~nd.binary_dilation(warm, iterations=4)        # the thumb and its nail stay out
base = nd.median_filter(lum, size=25)
bright = glass & (lum > base + 0.10)
lab, n = nd.label(bright); sizes = nd.sum(bright, lab, range(1, n+1))
keep = np.zeros_like(bright)
for i, (s_, sz) in enumerate(zip(nd.find_objects(lab), sizes)):
    hh, ww = s_[0].stop - s_[0].start, s_[1].stop - s_[1].start
    cy, cx = (s_[0].start + s_[0].stop)/2, (s_[1].start + s_[1].stop)/2
    in_text = 1250 < cx < 1740 and 1140 < cy < 1430
    long_line = max(hh, ww) > 4*max(1, min(hh, ww)) and max(hh, ww) > 70
    if (in_text and sz > 40) or long_line: keep[lab == i+1] = True          # letters, logo ring, long edge highlights
keep = nd.binary_dilation(keep, iterations=2)
# edge-preserving clean-up of the glass: the crinkled texture and droplets go, the bottle's shape, frame and rims stay
x0, y0, x1, y1 = 1000, 860, 1900, 1650
crop = (np.clip(C[y0:y1, x0:x1], 0, 1)*255).astype(np.uint8)
den = cv2.fastNlMeansDenoisingColored(crop, None, 30, 30, 9, 31)
den = cv2.bilateralFilter(den, 15, 40, 9)
den = cv2.medianBlur(den, 7).astype(np.float32)/255*0.86                        # back to deep black
D_ = C.copy(); D_[y0:y1, x0:x1] = den
wgt = nd.gaussian_filter((glass & ~keep).astype(np.float32), 1.2)
o = C*(1 - wgt[..., None]) + D_*wgt[..., None]
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
band = np.exp(-(((xx - 1185) - (yy - 1000)*0.12)/38)**2) * np.clip((1560 - yy)/450, 0, 1)   # soft long reflection, left
o = o + ((band*0.08)*wgt)[..., None]
kp = nd.gaussian_filter(keep.astype(np.float32), 1.0)*body
bl = np.dstack([nd.gaussian_filter(o[..., i], 1.5) for i in range(3)]); o = o + (o - bl)*1.2*kp[..., None]
# ---- skin: edge-preserving smoothing, blended so pores and creases stay faintly
warm2 = (C[..., 0] - C[..., 2] > 0.12) & (C[..., 0] > C[..., 1]) & (A > 0.9) & (lum > 0.25)
skin = nd.gaussian_filter(nd.binary_opening(warm2, iterations=2).astype(np.float32), 2) * (1 - body)
u8 = (np.clip(o, 0, 1)*255).astype(np.uint8)
bil = cv2.bilateralFilter(cv2.bilateralFilter(u8, 9, 22, 7), 9, 18, 5).astype(np.float32)/255
o = o*(1 - 0.7*skin[..., None]) + bil*0.7*skin[..., None]
res = np.dstack([np.clip(o, 0, 1), A]); Image.fromarray((res*255).astype(np.uint8), 'RGBA').save(out)
print('specks removed:', int(n - (sizes > 260).sum()))
