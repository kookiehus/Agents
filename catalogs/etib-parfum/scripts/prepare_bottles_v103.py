"""v103: owner's photo for K5 Kilian Good Girl Gone Bad.
Exact geometry instead of a free cut-out: body = rounded rectangle, collar and cap = rectangles fitted to the
rembg cut-out. The peach studio backdrop that shows through the clear glass is neutralised (gold cap and plate kept).
Usage: prepare_bottles_v103.py <K5.jpg> <rembg cut-out png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); K = 4
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]

def rrect(x0, y0, x1, y1, r):
    m = np.zeros((h*K, w*K), np.uint8)
    cv2.rectangle(m, (int((x0 + r)*K), int(y0*K)), (int((x1 - r)*K), int(y1*K)), 255, -1)
    cv2.rectangle(m, (int(x0*K), int((y0 + r)*K)), (int(x1*K), int((y1 - r)*K)), 255, -1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cv2.circle(m, (int(cx*K), int(cy*K)), int(r*K), 255, -1, lineType=cv2.LINE_AA)
    return cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)

body = rrect(260.0, 289.5, 609.5, 816.5, 13)
collar = rrect(374.5, 255.0, 497.5, 292.0, 1)
cap = rrect(368.0, 116.5, 505.0, 260.0, 4)
a = np.maximum(np.maximum(body, collar), cap)

# neutralise the backdrop seen through the glass: everything in the body except the gold plate
hsv = cv2.cvtColor((rgb*255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
plate = np.zeros((h, w), np.float32); plate[377:578, 357:512] = 1; plate = cv2.GaussianBlur(plate, (0, 0), 1.5)
glass = (body > 0)*(1 - plate)*(1 - np.maximum(cap, collar))
lum = rgb.mean(2, keepdims=True)
neutral = np.clip(lum*np.array([1.0, 0.995, 0.985]) + 0.03, 0, 1)        # barely warm, lifted
rgb = rgb*(1 - glass[..., None]*0.85) + neutral*glass[..., None]*0.85
# outermost 2 px of the glass taken from 3 px inside (no backdrop halo)
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
from scipy import ndimage as nd
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)

ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = ImageEnhance.Contrast(img.convert('RGB')).enhance(1.04).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/K5_ПРЕ.png'); print('K5_ПРЕ.png', img.size)
