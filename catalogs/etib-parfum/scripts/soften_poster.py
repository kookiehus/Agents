"""Owner's wood poster -> softer, cleaner print version in the mood of her reference:
clean denoised background, butter-smooth gradient, soft bloom, crisper bottle. Usage: soften_poster.py <in.png> <out.jpg>"""
import sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as nd
src, out = sys.argv[1], sys.argv[2]
im = np.array(Image.open(src).convert('RGB'))
h0, w0 = im.shape[:2]; K = 2
# 1) clean the noise first, then upscale
den = cv2.fastNlMeansDenoisingColored(im, None, 5, 5, 7, 21)
up = cv2.resize(den, (w0*K, h0*K), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)/255
raw = cv2.resize(im, (w0*K, h0*K), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)/255
h, w = up.shape[:2]
def poly(pts, blur):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon([(x*K, y*K) for x, y in pts], fill=255)
    return nd.gaussian_filter(np.array(m).astype(np.float32)/255, blur)
bottle = poly([(420, 505), (545, 460), (575, 600), (712, 592), (818, 915), (520, 1025), (402, 700), (470, 655)], 3)
up = up*(1 - bottle[..., None]) + raw*bottle[..., None]                    # the bottle keeps its sparkle (no denoise)
lum = up.mean(axis=2)
# 2) butter-smooth background: flat areas (little local detail) take a heavily blurred version
var = nd.gaussian_filter(lum**2, 6) - nd.gaussian_filter(lum, 6)**2
flat0 = (var < 0.0006)
flat0 = nd.binary_erosion(flat0, iterations=10)                                # keep the smoothing away from the edges (no dark halos)
halo = np.clip(nd.gaussian_filter(nd.binary_dilation(bottle > 0.5, iterations=60).astype(np.float32), 18), 0, 1)   # the bottle and its glow
flat = nd.gaussian_filter(flat0.astype(np.float32), 4)*(1 - bottle)
smooth = np.dstack([nd.gaussian_filter(up[..., i], 10) for i in range(3)])
o = up*(1 - flat[..., None]) + smooth*flat[..., None]
# 2b) background deeper and redder, wood calmer. Each pixel is weighted by how far its colour is from the
#     local background colour, so the edge pixels that are background-coloured get no greying (no halos).
fl = (var < 0.0006); fl = nd.binary_erosion(fl, iterations=4) & (bottle < 0.05)
ks = 4; sm = cv2.resize(o, (w//ks, h//ks), interpolation=cv2.INTER_AREA); msk = cv2.resize((~fl).astype(np.uint8)*255, (w//ks, h//ks), interpolation=cv2.INTER_NEAREST)
BGc = cv2.resize(cv2.inpaint((np.clip(sm, 0, 1)*255).astype(np.uint8), msk, 15, cv2.INPAINT_TELEA), (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)/255
BGc = np.dstack([nd.gaussian_filter(BGc[..., i], 12) for i in range(3)])
dist = np.abs(o - BGc).max(axis=2)
wood = np.clip((dist - 0.06)/0.14, 0, 1)*(1 - halo)
bgm = (1 - wood)*(1 - bottle)
o = o*(1 - bgm[..., None]) + (o**np.array([1.0, 1.12, 1.25])*np.array([0.97, 0.90, 0.86]))*bgm[..., None]
lw = o.mean(axis=2, keepdims=True); calm = lw + (o - lw)*0.70                    # a bit less fiery, still warm
calm = np.clip(calm*np.array([1.0, 0.97, 0.92])*0.95, 0, 1)                      # warm beige-brown, never grey
o = o*(1 - wood[..., None]) + calm*wood[..., None]
# 3) crisper bottle: unsharp mask inside the bottle only
blur_b = np.dstack([nd.gaussian_filter(o[..., i], 2.2) for i in range(3)])
o = o + (o - blur_b)*1.1*bottle[..., None]
# 4) soft bloom on the light (the glowing bottle edges and lit wood)
l2 = o.mean(axis=2); hi = np.clip((l2 - 0.55)/0.45, 0, 1)**1.6
glow = np.dstack([nd.gaussian_filter(o[..., i]*hi, 28) for i in range(3)])
o = 1 - (1 - o)*(1 - glow*0.35)
# 5) gentle grade: a touch redder and softer, deeper top-left corner like the reference
o = np.clip(o, 0, 1)**np.array([0.98, 1.02, 1.06])
yy, xx = np.mgrid[0:h, 0:w]; vig = np.clip(1 - 0.45*np.exp(-(((xx/w)**2 + (yy/h)**2)/0.16)), 0, 1)
o = o*vig[..., None]
Image.fromarray((np.clip(o, 0, 1)*255).astype('uint8')).save(out, quality=94)
print('saved', w, h)
