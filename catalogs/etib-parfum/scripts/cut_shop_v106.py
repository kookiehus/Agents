"""v101/v102/v106: owner's new shop interior photo for page 18 (end of the men's section).
The source has a baked-in grey/white checkerboard. It is found as neutral pixels where both checker tones
(~234 and ~254) are present in a 15 px window, grown pixel by pixel up to the store outline, then the
outline is smoothed. The floor (only the floor, between the plinth lines) blurs and fades into the page.
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
# v106: exact corners where the side cabinets meet the back wall (measured on the source):
# display frame top line, the short end post, the wall edge and wall top
def corner(x0, x1, y0, y1, inside):
    ss = 8; yy, xx = np.mgrid[y0:y1:1/ss, x0:x1:1/ss] + 0.5/ss
    m = inside(xx, yy).astype(np.float32)
    return m.reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3))
pm[300:400, 420:530] = corner(420, 530, 300, 400, lambda x, y:
    ((x < 491) & (y >= 339 + (x - 436)*0.759 - 1)) | ((x >= 491) & (x < 511.5) & (y >= 383)) | ((x >= 511.5) & (y >= 348.5)))
pm[300:400, 915:1020] = corner(915, 1020, 300, 400, lambda x, y:
    ((x < 930.5) & (y >= 346)) | ((x >= 930.5) & (x < 950) & (y >= 384)) | ((x >= 950) & (y >= 381 - (x - 950)*0.685 - 1)))
obj = pm > 0.5
al = cv2.GaussianBlur(pm, (0, 0), 0.5)

# edge colours: take them from 3 px inside so no checker grey bleeds into the outline
core = nd.binary_erosion(obj, iterations=3)
ni = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
rgb = np.where((~core)[..., None], a[ni[0], ni[1]], a)

# floor only (v102): the polygon between the two plinth lines blurs and fades into the page;
# the cabinets and their bottom corners stay sharp and solid
FLOOR = [(91, 1060), (558, 745), (905, 745), (1332, 1061), (1332, h), (91, h)]
fm = np.zeros((h*4, w*4), np.uint8); cv2.fillPoly(fm, [(np.array(FLOOR, np.float32)*4).astype(np.int32)], 255)
fm = cv2.resize(fm, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
fm = cv2.GaussianBlur(fm, (0, 0), 2.0)[..., None]
ys = np.arange(h)[:, None, None].astype(np.float32)
Y0, Y1, F0, F1 = 800, 1000, 900, 1046
blur = cv2.GaussianBlur(rgb, (0, 0), 7)
wb = np.clip((ys - Y0)/(Y1 - Y0), 0, 1); wb = wb*wb*(3 - 2*wb)*fm
rgb = rgb*(1 - wb) + blur*wb
f = np.clip((ys - F0)/(F1 - F0), 0, 1); f = (f*f*(3 - 2*f))*fm
al = al*(1 - f[..., 0])
# exact bottom of the two cabinet plinths (lit strip), nothing below them
LB = [(0, 1061.5), (45, 1061.5), (77.5, 1064.5), (91, 1060), (91, h), (0, h)]
RB = [(1332, 1061), (1358, 1061), (1369, 1067.5), (1408, 1067.5), (w, 1067.5), (w, h), (1332, h)]
cutm = np.zeros((h*4, w*4), np.uint8)
for P in (LB, RB): cv2.fillPoly(cutm, [(np.array(P, np.float32)*4).astype(np.int32)], 255)
cutm = cv2.resize(cutm, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
al = al*(1 - cutm)

im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al*255]).astype(np.uint8), 'RGBA')
im = im.resize((w*2, h*2), Image.LANCZOS)
c3 = im.convert('RGB').filter(ImageFilter.UnsharpMask(2, 60, 2)); c3.putalpha(im.getchannel('A'))
c3.save(out); print(out, c3.size)
