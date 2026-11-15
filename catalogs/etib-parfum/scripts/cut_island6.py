import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
D, outp = sys.argv[1], sys.argv[2]
I = np.array(Image.open(f'{D}/shops/island6.png').convert('RGB'))
h, w = I.shape[:2]
# 1) object mask: GrabCut on the composite
mask = np.zeros((h, w), np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(cv2.cvtColor(I, cv2.COLOR_RGB2BGR), mask, (55, 140, w - 110, h - 150), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
fg = np.isin(mask, (1, 3))
lab, n = nd.label(fg); sz = nd.sum(fg, lab, range(1, n + 1)); fg = lab == (np.argmax(sz) + 1)
from PIL import ImageDraw
def poly(pts):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255); return np.array(m) > 0
cabinet = poly([(1030, 588), (1456, 538), (1456, 862), (1442, 940), (1030, 978), (1016, 950), (1016, 600)])
solid = cabinet | poly([(638, 150), (764, 150), (764, 336), (638, 336)]) | (poly([(816, 286), (874, 286), (874, 348), (816, 348)]) & (I.max(axis=2) < 45))
fg = nd.binary_fill_holes(nd.binary_closing(fg | cabinet | solid, iterations=4))
# 2) backdrop estimate behind the object (inpaint from the surroundings)
k = 4; small = cv2.resize(I, (w//k, h//k), interpolation=cv2.INTER_AREA)
ms = cv2.resize(nd.binary_dilation(fg | cabinet, iterations=12).astype(np.uint8)*255, (w//k, h//k), interpolation=cv2.INTER_NEAREST)
Bs = cv2.inpaint(small, ms, 9, cv2.INPAINT_TELEA); B = cv2.GaussianBlur(cv2.resize(Bs, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), 6).astype(float)
# 3) clear glass: where the picture equals the backdrop, the object is see-through
If = I.astype(float); diff = np.abs(If - B).max(axis=2)
a = np.clip((diff - 10) / 28, 0, 1)
a = np.maximum(a, (If.max(axis=2) < 28) * (B.max(axis=2) > 45))        # truly black trims stay solid
a = np.maximum(a, solid.astype(float)); a = cv2.GaussianBlur(a, (0, 0), 0.7)
soft = cv2.GaussianBlur(fg.astype(float), (0, 0), 1.0)
alpha = a * soft
F = (If - (1 - alpha[..., None]) * B) / np.maximum(alpha[..., None], 1e-3)  # un-mix the dark backdrop
F = np.clip(F, 0, 255)
out = np.dstack([F, alpha * 255]).astype(np.uint8)
ys, xs = np.where(alpha > 0.02); im = Image.fromarray(out, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
im.save(outp); print(im.size)
