"""v30: owner's new V19 photo (Sexy Little Things Noir): rembg cut, inside filled, tilt straightened by the bottle's
shoulders, outline smoothed, light-background fringe removed, thin rim light so the black bottle stands off the panel.
Usage: prepare_bottles_v30.py <upload png> <out png>"""
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
# tilt: angle of the body's bottom edge (lowest solid pixel per column across the middle of the body)
m = a > 0.5; cols = np.where(m.any(axis=0))[0]; xs = cols[len(cols)//4: 3*len(cols)//4]
yb = np.array([np.where(m[:, x])[0].max() for x in xs]); k = np.polyfit(xs, yb, 1)[0]; ang = np.degrees(np.arctan(k))
ang += 0.6                                                      # shoulders + base measured together (the photo has slight perspective)
print('tilt', round(ang, 2))
rgba = np.dstack([rgb, a]); h, w = a.shape
M = cv2.getRotationMatrix2D((w/2, h/2), ang, 1.0)
rgba = cv2.warpAffine(rgba, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)); rgb, a = rgba[..., :3], np.clip(rgba[..., 3], 0, 1)
a = np.clip((cv2.GaussianBlur(a, (0, 0), 0.9) - 0.5)*1.8 + 0.5, 0, 1)
sm = cv2.GaussianBlur(cv2.erode((a > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(np.float32), (0, 0), 0.8)
a = np.minimum(a, sm)                                           # outline pulled 1 px in: no light backdrop fringe
solid = a > 0.97; idx = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
wgt = np.clip((0.97 - a)/0.5, 0, 1)[..., None]; rgb = rgb*(1 - wgt) + rgb[idx[0], idx[1]]*wgt
edge = (a > 0.3) & ~nd.binary_erosion(a > 0.5, iterations=3)                           # pale backdrop caught on the black edge
ref = rgb[idx[0], idx[1]]; pale = edge & (rgb.mean(axis=2) > ref.mean(axis=2) + 0.12) & (ref.mean(axis=2) < 0.25)
rgb = np.where(pale[..., None], ref, rgb)
edge2 = (a > 0.02) & ~nd.binary_erosion(a > 0.5, iterations=4)        # any remaining light pixel on the black edge takes the colour inside
ref2 = rgb[idx[0], idx[1]]; rgb = np.where((edge2 & (ref2.mean(axis=2) < 0.3) & (rgb.mean(axis=2) > ref2.mean(axis=2) + 0.05))[..., None], ref2, rgb)
lum = rgb.mean(axis=2, keepdims=True); dk = np.clip((0.45 - lum)/0.35, 0, 1)            # phone photo: greyish, cool blacks -> deep neutral black like the studio shots
rgb = rgb*(1 - dk) + ((lum + (rgb - lum)*0.4)**1.35)*dk
ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA').save(out)
