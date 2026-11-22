"""v35: owner's new A2 photo (Avril Lavigne Forbidden Rose, clear glass on white): rembg cut, main object only,
inside filled, outline smoothed, white backdrop seen through the clear glass made see-through (facets kept).
Usage: prepare_bottles_v35.py <upload png> <out png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
src, out = sys.argv[1:3]
im = Image.open(src).convert('RGB'); o = remove(im, session=new_session('isnet-general-use'))
rgb = np.array(im).astype(np.float32)/255; a = np.array(o.getchannel('A')).astype(np.float32)/255
m = a > 0.5; lab, n = nd.label(m)
if n > 1: sz = nd.sum(m, lab, range(1, n + 1)); a = a*nd.binary_dilation(lab == (np.argmax(sz) + 1), iterations=3)
inside = nd.binary_fill_holes(nd.binary_erosion(a > 0.5, iterations=2)); a = np.maximum(a, nd.binary_erosion(inside, iterations=2).astype(np.float32))
a = np.clip((cv2.GaussianBlur(a, (0, 0), 0.9) - 0.5)*1.8 + 0.5, 0, 1)
solid = a > 0.97; idx = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
w = np.clip((0.97 - a)/0.5, 0, 1)[..., None]; rgb = rgb*(1 - w) + rgb[idx[0], idx[1]]*w
# clear glass: bright neutral (white backdrop through glass) partly see-through, the lilac juice, cap and collar stay
mn, mx = rgb.min(axis=2), rgb.max(axis=2)
neutral = np.clip((0.08 - (mx - mn))/0.05, 0, 1); t = np.clip((mn - 0.70)/0.25, 0, 1); white = t*t*(3 - 2*t)
a = a*(1 - 0.30*cv2.GaussianBlur((neutral*white).astype(np.float32), (0, 0), 2.0))   # a hint of the panel through the clear glass, no noise
u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8); rgb = cv2.bilateralFilter(cv2.fastNlMeansDenoisingColored(u8, None, 5, 5, 5, 15), 7, 25, 5).astype(np.float32)/255
ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(out); print(img.size)
