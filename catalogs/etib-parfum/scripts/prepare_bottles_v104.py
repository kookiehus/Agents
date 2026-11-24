"""v104: S2 Scandalous — the dark strip under the faceted glass removed. The bottom is cut at the real lower edge of
the last row of facets (y=830 in the v53 file) with rounded corners that follow the side bevels.
Usage: prepare_bottles_v104.py <data dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
D, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True); K = 4
im = Image.open(f'{D}/bottles_v53/S2_ЖЕН.png').convert('RGBA'); arr = np.array(im).astype(np.float32)/255
h, w = arr.shape[:2]; YB, R = 830.0, 44
m = np.zeros((h*K, w*K), np.uint8)
x0, x1 = 0.0, 486.0
cv2.rectangle(m, (0, 0), (int(x1*K), int((YB - R)*K)), 255, -1)
cv2.rectangle(m, (int((x0 + R)*K), 0), (int((x1 - R)*K), int(YB*K)), 255, -1)
for cx in (x0 + R, x1 - R): cv2.circle(m, (int(cx*K), int((YB - R)*K)), int(R*K), 255, -1, lineType=cv2.LINE_AA)
clip = cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
clip[:700] = 1; clip[:, 486:] = np.maximum(clip[:, 486:], (np.arange(h) < 700)[:, None])
arr[..., 3] *= clip
ys = np.where(arr[..., 3].max(1) > 0.02)[0]; arr = arr[:ys.max() + 1]
Image.fromarray((np.clip(arr, 0, 1)*255).astype(np.uint8), 'RGBA').save(f'{OUT}/S2_ЖЕН.png'); print('S2_ЖЕН.png', arr.shape)
