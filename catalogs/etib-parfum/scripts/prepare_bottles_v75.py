"""v75: G4 Giorgio Armani Acqua di Gioia from the owner's photo (clear glass on white).
Mask = everything that differs from the white; the outline is the convex hull of each part (ball cap, neck, rounded-square
body), so the clear glass edge is smooth with no bites. Light background seen through the thick glass walls is toned
down to grey glass; soft contrast and sharpening, no levels stretch.
Usage: prepare_bottles_v75.py <uploads dir with G4.jpg> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
UP, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
im = np.array(Image.open(f'{UP}/G4.jpg').convert('RGB')).astype(np.float32)/255; h, w = im.shape[:2]
m = (1 - im.min(axis=2)) > 8/255; m = nd.binary_closing(m, iterations=3); m = nd.binary_fill_holes(m)
lab, n = nd.label(m); m = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
def hull(rows):
    part = np.zeros_like(m); part[rows] = m[rows]
    pts = np.argwhere(part)[:, ::-1].astype(np.int32)
    out = np.zeros((h*4, w*4), np.uint8); cv2.fillPoly(out, [cv2.convexHull(pts*4 + 2)], 255)
    return cv2.resize(out.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
ys = np.where(m.any(axis=1))[0]
sh = np.zeros_like(m); sh[232:330] = m[232:330]                                  # shoulders are concave: take them from the mask (smoothed)
sh = cv2.GaussianBlur(nd.binary_opening(sh, iterations=2).astype(np.float32), (0, 0), 2.0)
body = hull(slice(320, ys[-1] + 1)); body[:300] = 0
a = np.maximum.reduce([hull(slice(ys[0], 186)), hull(slice(180, 238)), sh, body])
a = cv2.GaussianBlur(a, (0, 0), 0.8); a = np.clip((a - 0.5)*1.8 + 0.5, 0, 1)
d = nd.distance_transform_edt(a > 0.5)
white = (im.min(axis=2) > 0.86) & (d < 46) & (np.arange(h)[:, None] > 240)          # white backdrop seen through the glass walls
wgt = cv2.GaussianBlur((white*np.clip((46 - d)/46, 0, 1)).astype(np.float32), (0, 0), 2.5)[..., None]
rgb = im*(1 - wgt*0.40) + np.array([0.20, 0.23, 0.23])*wgt*0.40
edge = np.clip((3 - d)/3, 0, 1)[..., None]*(a > 0.02)[..., None]                    # outer 3 px: a touch darker glass edge
rgb = rgb*(1 - 0.25*edge)
ys_, xs_ = np.where(a > 0.02); y0, y1, x0, x1 = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = ImageEnhance.Contrast(img.convert('RGB')).enhance(1.06).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/G4_ЖЕН.png'); print('G4_ЖЕН.png', img.size)
