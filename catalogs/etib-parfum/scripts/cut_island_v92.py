"""v92: island cut-out with a clean straight-segment outline (no ragged see-through edges); glass shows the white page.
Usage: cut_island_v92.py <photo> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
src, outp = sys.argv[1], sys.argv[2]
I = np.array(Image.open(src).convert('RGB'))
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
# 2) clean outline: the GrabCut silhouette is turned into straight segments (approxPolyDP) and drawn anti-aliased at 4x
cs, _ = cv2.findContours(fg.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea); ap = cv2.approxPolyDP(c, 2.2, True)
K = 4; big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [ap*K + K//2], 255, lineType=cv2.LINE_AA)
alpha = cv2.resize(big.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
# 3) the dark backdrop seen through the clear glass becomes white (the page), reflections and bottles stay
k = 4; small = cv2.resize(I, (w//k, h//k), interpolation=cv2.INTER_AREA)
ms = cv2.resize(nd.binary_dilation(fg, iterations=12).astype(np.uint8)*255, (w//k, h//k), interpolation=cv2.INTER_NEAREST)
Bs = cv2.inpaint(small, ms, 9, cv2.INPAINT_TELEA); B = cv2.GaussianBlur(cv2.resize(Bs, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), 6).astype(float)
If = I.astype(float); diff = np.abs(If - B).max(axis=2)
t = np.clip(1 - (diff - 6)/34, 0, 1)
t = cv2.GaussianBlur(t, (0, 0), 1.0)[..., None]*(1 - solid[..., None])
F = np.clip(If + (246 - B)*t*0.92, 0, 255)
out = np.dstack([F, alpha*255]).astype(np.uint8)
ys, xs = np.where(alpha > 0.02); im = Image.fromarray(out, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
im.save(outp); print(im.size, len(ap), 'vertices')
