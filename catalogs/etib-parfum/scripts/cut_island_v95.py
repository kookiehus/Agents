"""v92/v94 (denoised, smoother glass, 2x): island cut-out with a clean straight-segment outline (no ragged see-through edges); glass shows the white page.
Usage: cut_island_v92.py <photo> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
src, outp = sys.argv[1], sys.argv[2]
I = np.array(Image.open(src).convert('RGB'))
Id = cv2.fastNlMeansDenoisingColored(I, None, 2, 2, 7, 21)                        # v94: denoised colours (the outline is still found on the original)
h, w = I.shape[:2]
# 1) object mask: GrabCut on the composite
mask = np.zeros((h, w), np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(cv2.cvtColor(I, cv2.COLOR_RGB2BGR), mask, (55, 140, w - 110, h - 150), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
fg = np.isin(mask, (1, 3))
lab, n = nd.label(fg); sz = nd.sum(fg, lab, range(1, n + 1)); fg = lab == (np.argmax(sz) + 1)
from PIL import ImageDraw
def poly(pts):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255); return np.array(m) > 0
cabinet = poly([(1030, 590), (1452, 536), (1453, 873), (1410, 867), (1402, 870), (1080, 975), (1077, 987), (1030, 989), (1016, 950), (1016, 600)])
sign = poly([(641.5, 156.5), (759.5, 153.5), (759, 319), (768, 318), (768, 341), (634, 343), (634, 324), (643, 325)])
excl = poly([(0, 490), (70, 490), (90, 504), (548, 966), (573, 978), (1030, 996), (1078, 990), (1080, 978), (1402, 872), (1451, 876), (1535, 876), (1535, 1024), (0, 1024)]) \
     | poly([(0, 0), (81, 0), (81, 505), (0, 505)]) | poly([(1451, 0), (1535, 0), (1535, 1024), (1451, 1024)]) \
     | (poly([(628, 140), (775, 140), (775, 268), (628, 268)]) & ~sign)
excl &= ~cabinet
solid = cabinet | sign | (poly([(816, 286), (874, 286), (874, 348), (816, 348)]) & (I.max(axis=2) < 45))
fg = nd.binary_fill_holes(nd.binary_closing(fg | cabinet | solid, iterations=4)) & ~excl
# 2) v95 exact outline: bottom = the tumba's real lower edges (above the LED glow and the floor), traced on the photo;
#    top = the upper convex hull of the glass boxes (straight far rims, no ragged background); objects on top added by box
BOTL = [(88, 500), (566, 967), (880, 991), (1018, 974), (1020, 989), (1078, 989), (1080, 946), (1400, 861), (1402, 870), (1453, 873)]
bot = poly([(0, 500)] + BOTL + [(1535, 873), (1535, 1024), (0, 1024)])
fgc = fg & ~bot
objs = poly([(290, 150), (455, 150), (455, 270), (290, 270)]) | poly([(812, 170), (882, 170), (882, 352), (812, 352)]) | sign
vimg = Image.new('L', (w, h), 0); dv = ImageDraw.Draw(vimg)                     # white vase = two stacked spheres measured on the photo
dv.ellipse((1370 - 19, 268 - 17, 1370 + 19, 268 + 18), fill=255); dv.ellipse((1370 - 26, 300 - 15, 1370 + 26, 300 + 16), fill=255)
vase = np.array(vimg) > 0
glass = fgc & ~objs & ~vase
glass &= ~poly([(975, 0), (1535, 0), (1535, 318), (1345, 316), (978, 276)])          # right box: nothing above its top rim (the grey wall behind the vase)
hull = np.zeros((h, w), np.uint8)
for x0_, x1_ in ((0, 600), (560, 990), (975, w)):                               # one hull per glass box: no bridges over the gaps
    part = glass.copy(); part[:, :x0_] = False; part[:, x1_:] = False
    gy, gx = np.nonzero(part); pts = np.c_[gx, gy].astype(np.int32); cv2.fillPoly(hull, [cv2.convexHull(pts)], 1)
body = (hull > 0) & ~bot
body &= ~poly([(1453, 0), (1535, 0), (1535, 1024), (1453, 1024)]) & ~poly([(0, 0), (84, 0), (84, 1024), (0, 1024)])
full = body | (fgc & objs) | vase
full = nd.binary_fill_holes(nd.binary_opening(full, iterations=1))
ybl = np.interp(np.arange(w), [p_[0] for p_ in BOTL], [p_[1] for p_ in BOTL])         # v96: fill every column down to the tumba's exact lower edge
for x in range(88, 1454):
    col = np.nonzero(full[:, x])[0]
    if len(col) and col[-1] > 400: full[col[0]:int(ybl[x]), x] = True
cs, _ = cv2.findContours(full.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea); ap = cv2.approxPolyDP(c, 1.2, True)
K = 4; big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [ap*K + K//2], 255, lineType=cv2.LINE_AA)
alpha = cv2.resize(big.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
solid = solid | vase
# v96: the LED light strip under the tumba is kept: a band under the lower edge, its alpha from the light itself, fading out
yy_ = np.arange(h)[:, None]; dist_ = yy_ - ybl[None, :]
band = (dist_ >= -1) & (dist_ < 44) & (np.arange(w)[None, :] >= 88) & (np.arange(w)[None, :] <= 1453)
Lg = I.astype(np.float32).mean(axis=2)
line_ = np.clip(1 - np.abs(dist_ - 3.0)/4.0, 0, 1)                                    # v99: a clear LED line, ~5 px, just under the edge
spill_ = 0.95*np.clip(1 - dist_/34, 0, 1)**1.2
ga = np.maximum(line_, spill_)*band
ga = np.clip(ga, 0, 1)
ga = cv2.GaussianBlur(ga.astype(np.float32), (0, 0), 2.0)
glow_a = np.where(alpha > 0.5, 0, ga)
# 3) the dark backdrop seen through the clear glass becomes white (the page), reflections and bottles stay
k = 4; small = cv2.resize(I, (w//k, h//k), interpolation=cv2.INTER_AREA)
ms = cv2.resize(nd.binary_dilation(fg | full, iterations=12).astype(np.uint8)*255, (w//k, h//k), interpolation=cv2.INTER_NEAREST)
small = cv2.resize(Id, (w//k, h//k), interpolation=cv2.INTER_AREA); Bs = cv2.inpaint(small, ms, 9, cv2.INPAINT_TELEA); B = cv2.GaussianBlur(cv2.resize(Bs, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), 6).astype(float)
If = Id.astype(float); diff = np.abs(If - B).max(axis=2)
t = np.clip(1 - (diff - 10)/48, 0, 1)
t = t*(I.astype(np.float32).mean(axis=2) < 175)                                     # v96: bright white panels are never 'see-through'
t = cv2.GaussianBlur(t, (0, 0), 1.0)[..., None]*(1 - solid[..., None])
F = np.clip(If + (246 - B)*t*0.95, 0, 255)
Fs = cv2.GaussianBlur(F, (0, 0), 1.6); w8 = np.clip((t - 0.35)/0.4, 0, 1)                 # see-through glass areas: smooth, no blocky grey
F = F*(1 - w8) + Fs*w8
# v97: flat bright panels from the original, lightly smoothed (no posterised 'map' blotches)
Lo = I.astype(np.float32).mean(axis=2); tex = cv2.GaussianBlur(np.abs(Lo - cv2.GaussianBlur(Lo, (0, 0), 2)), (0, 0), 3)
flatw = (np.clip((Lo - 165)/30, 0, 1)*np.clip((6 - tex)/4, 0, 1))[..., None]
F = F*(1 - flatw) + cv2.GaussianBlur(I.astype(np.float32), (0, 0), 1.4)*flatw
# v97: edge decontamination: the outer 3 px take the colour from 4 px inside (no grey / dark seam along the cut)
inside = alpha > 0.5; dd = nd.distance_transform_edt(inside)
core = dd > 4; ci = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
edge = (dd <= 4)                                                                      # incl. everything outside: no backdrop colour left to bleed in when resizing
F = np.where(edge[..., None], F[ci[0], ci[1]], F)
gw = np.clip(glow_a*1.3, 0, 1)[..., None]
linec = cv2.GaussianBlur((np.clip(1 - np.abs(dist_ - 3.0)/4.0, 0, 1)*band).astype(np.float32), (0, 0), 1.0)[..., None]
glowc = np.array([246, 168, 70])*(1 - linec) + np.array([255, 214, 140])*linec            # hot warm-white line, amber spill
F = F*(1 - gw) + glowc*gw                                        # warm LED light on the white page
alpha = np.maximum(alpha, glow_a*0.88)
F = cv2.resize(F.astype(np.float32), (w*2, h*2), interpolation=cv2.INTER_CUBIC); alpha = np.clip(cv2.resize(alpha, (w*2, h*2), interpolation=cv2.INTER_LINEAR), 0, 1)   # 2x for print
bl = cv2.GaussianBlur(F, (0, 0), 1.2); fw2 = cv2.resize(flatw[..., 0], (w*2, h*2))[..., None]
F = np.clip(F + (F - bl)*0.6*(1 - fw2), 0, 255)                                      # sharpen detail only, not the flat panels
out = np.dstack([F, alpha*255]).astype(np.uint8)
ys, xs = np.where(alpha > 0.02); im = Image.fromarray(out, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
im.save(outp); print(im.size, len(ap), 'vertices')
