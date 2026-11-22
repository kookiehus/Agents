"""v36: owner's new A2 photo (Avril Lavigne Forbidden Rose, clear glass on white).
The glass body is a convex shape, so below the collar the outline is the convex hull of the cut-out: straight, even
edges. The bottle stays opaque with its own colours (the pale lilac right side is the juice, not background).
Edge pixels take the colour found just inside (no white fringe). Usage: prepare_bottles_v35.py <upload png> <out png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
src, out = sys.argv[1:3]
im = Image.open(src).convert('RGB'); o = remove(im, session=new_session('isnet-general-use'))
rgb = np.array(im).astype(np.float32)/255; a = np.array(o.getchannel('A')).astype(np.float32)/255
m = a > 0.5; lab, n = nd.label(m)
if n > 1: sz = nd.sum(m, lab, range(1, n + 1)); m = lab == (np.argmax(sz) + 1)
m = nd.binary_fill_holes(m)
w = m.sum(axis=1); ys = np.where(w > 0)[0]
neck = ys[0] + int(np.argmin(w[ys[0] + 120: ys[0] + 260])) + 120               # narrowest row under the rose cap = collar
K = 4; h, wd = m.shape
big = cv2.resize(m.astype(np.uint8)*255, (wd*K, h*K), interpolation=cv2.INTER_LINEAR)
low = big.copy(); low[:neck*K] = 0
cnts, _ = cv2.findContours((low > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
hull = cv2.convexHull(np.vstack(cnts)); hm = np.zeros_like(big); cv2.fillPoly(hm, [hull], 255); hm[:neck*K] = 0
top = cv2.GaussianBlur(big, (0, 0), 2.5); top[neck*K:] = 0                       # rose cap: its own outline, smoothed
mask = np.maximum((top > 127).astype(np.uint8)*255, hm)
a = cv2.resize(cv2.GaussianBlur(mask.astype(np.float32)/255, (0, 0), 1.2), (wd, h), interpolation=cv2.INTER_AREA)
a = np.clip((a - 0.5)*1.6 + 0.5, 0, 1)
core = nd.binary_erosion(a > 0.5, iterations=3)
idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True); ref = rgb[idx[0], idx[1]]
edge = (a > 0.02) & ~core
bright = rgb.mean(axis=2) > ref.mean(axis=2) + 0.06                              # white backdrop caught along the edge
rgb = np.where((edge & bright)[..., None] | (~m & (a > 0.02))[..., None], ref, rgb)
u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8); rgb = cv2.fastNlMeansDenoisingColored(u8, None, 4, 4, 5, 15).astype(np.float32)/255
ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(out); print(img.size, 'collar row', neck)
