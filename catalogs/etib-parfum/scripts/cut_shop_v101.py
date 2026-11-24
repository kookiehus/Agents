"""v101: owner's new shop interior photo for page 18 (end of the men's section).
The source has a baked-in grey/white checkerboard. It is found as neutral pixels where both checker tones
(~234 and ~254) are present in a 15 px window, grown pixel by pixel up to the store outline, then the
outline is smoothed. The floor blurs progressively and fades into the page across the full width.
Usage: cut_shop_v101.py <src.png> <out.png>"""
import sys
import numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd

src, out = sys.argv[1:3]
a = np.array(Image.open(src).convert('RGB')).astype(np.float32); L = a.mean(2); h, w = L.shape
neu = (a.max(2) - a.min(2)) < 7
dark = neu & (np.abs(L - 234.5) < 5.5); light = neu & (L >= 248); tr = neu & (L > 228)
k = (15, 15)
fd, fl, ft = (cv2.blur(m.astype(np.float32), k) for m in (dark, light, tr))
bg = (fd > 0.2) & (fl > 0.2) & (ft > 0.97)
lab, n = nd.label(bg); edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
bg = nd.binary_dilation(np.isin(lab, list(edge)), iterations=12, mask=tr)
obj = ~bg; lab, n = nd.label(obj); c = np.bincount(lab.ravel()); c[0] = 0
obj = nd.binary_fill_holes(lab == np.argmax(c))
obj = nd.binary_opening(obj, np.ones((9, 9)))                 # drop crumbs above the displays
lab, n = nd.label(obj); c = np.bincount(lab.ravel()); c[0] = 0; obj = lab == np.argmax(c)
# straight outline: polygon approximation of the contour, drawn at 4x and averaged down (anti-aliased)
cs, _ = cv2.findContours(obj.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 3.5, True)
big = np.zeros((h*4, w*4), np.uint8); cv2.fillPoly(big, [(poly.astype(np.float32)*4 + 1.5).astype(np.int32)], 255)
pm = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
obj = pm > 0.5
al = cv2.GaussianBlur(pm, (0, 0), 0.5)

# edge colours: take them from 3 px inside so no checker grey bleeds into the outline
core = nd.binary_erosion(obj, iterations=3)
ni = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
rgb = np.where((~core)[..., None], a[ni[0], ni[1]], a)

# floor: progressive blur toward the bottom, extended to the full width, then faded into the page
Y0, Y1, F0, F1 = 760, 1000, 930, h - 4
blur = cv2.GaussianBlur(rgb, (0, 0), 9)
wb = np.clip((np.arange(h) - Y0)/(Y1 - Y0), 0, 1); wb = (wb*wb*(3 - 2*wb))[:, None, None]
rgb = rgb*(1 - wb) + blur*wb
floor = obj.copy(); floor[:880] = False
fill = nd.distance_transform_edt(~floor, return_distances=False, return_indices=True)
ext = cv2.GaussianBlur(rgb[fill[0], fill[1]], (0, 0), 25)
ys = np.arange(h)[:, None]
side = np.clip((ys - 880)/120.0, 0, 1)                         # extension only near the floor line
rgb = np.where(obj[..., None], rgb, ext)
al = np.maximum(al, side*(ys >= 880))
f = np.clip((ys - F0)/(F1 - F0), 0, 1); f = f*f*(3 - 2*f)
al = al*(1 - f)

im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al*255]).astype(np.uint8), 'RGBA')
im = im.resize((w*2, h*2), Image.LANCZOS)
c3 = im.convert('RGB').filter(ImageFilter.UnsharpMask(2, 60, 2)); c3.putalpha(im.getchannel('A'))
c3.save(out); print(out, c3.size)
