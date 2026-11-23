"""v77: award medals from the owner's sharper picture (medali.png, grey backdrop). Each medal = fitted circle
(least squares on its visible outline), drawn anti-aliased at 4x; the grey backdrop is removed. The overlap order of the
picture is kept (it is one flat image). Output replaces awards/medals.png.
Usage: prepare_medals_v77.py <medali.png> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
src, out = sys.argv[1:3]
im = np.array(Image.open(src).convert('RGB')).astype(np.float32)/255; h, w = im.shape[:2]
sat = im.max(axis=2) - im.min(axis=2)
m = sat > 28/255; m = nd.binary_opening(m, iterations=2); m = nd.binary_fill_holes(m)
edge = m & ~nd.binary_erosion(m, iterations=1); ey, ex = np.nonzero(edge)
def fit(sel):
    P = np.c_[ex[sel], ey[sel]].astype(float); A = np.c_[2*P[:, 0], 2*P[:, 1], np.ones(len(P))]
    cx, cy, c0 = np.linalg.lstsq(A, (P**2).sum(1), rcond=None)[0]; return cx, cy, np.sqrt(c0 + cx**2 + cy**2)
inner = (ey > 12) & (ey < h - 12)
circles = [fit(inner & (ex < 540)), fit(inner & (ex > 600) & (ex < 1110) & ((ey < 120) | (ey > 520))), fit(inner & (ex > 1150))]
K = 4; big = np.zeros((h*K, w*K), np.uint8)
for cx, cy, R in circles:
    print('circle %.1f %.1f %.1f' % (cx, cy, R)); cv2.circle(big, (int(round(cx*K)), int(round(cy*K))), int((R - 1.0)*K), 255, -1, lineType=cv2.LINE_AA)
a = cv2.resize(big.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
d = nd.distance_transform_edt(a > 0.5); band = 3
idx = nd.distance_transform_edt(~(d > band), return_distances=False, return_indices=True)
t = np.clip((band + 1 - d)/band, 0, 1)[..., None]; rgb = im*(1 - t) + im[idx[0], idx[1]]*t       # no grey fringe on the rim
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])*255).astype(np.uint8), 'RGBA')
k = 2036/w; img = img.resize((2036, round(h*k)), Image.LANCZOS)                                     # same width as the old medals.png
c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.0, 30, 2))
Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(out); print(out, img.size)
