"""v146: G25 My Way — cap and collar left half mirrored from the clean right half (no light sliver);
D14 Sauvage Elixir — bottom pulled in 3 px (no light fringe); B5 Byredo — shoulder corners beside the cap pulled in 3 px.
Usage: fix_bottles_v146.py <v145 dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
def load(n): return np.array(Image.open(f'{SRC}/{n}.png').convert('RGBA')).astype(np.float32)
def save(im, n): Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/{n}.png')
im = load('G25'); h, w = im.shape[:2]; AX = 239.5                         # cap + collar: the left half mirrors the clean right half
xs = np.arange(w); mx = np.clip(np.round(2*AX - xs).astype(int), 0, w - 1)
left = xs < AX; a = im[..., 3].copy(); a[:332, left] = a[:332, mx[left]]; im[..., 3] = a; save(im, 'G25')
im = load('D14_МУЖ'); h, w = im.shape[:2]; K = 4                         # bottom: clean rounded rectangle 10 px above the old light rim
m = np.zeros((h*K, w*K), np.uint8); q = lambda v: int(round(v*K)); x0, x1, y1, r = 4.0, 499.0, 893.0, 44
cv2.rectangle(m, (q(x0), 0), (q(x1), q(y1 - r)), 255, -1); cv2.rectangle(m, (q(x0 + r), 0), (q(x1 - r), q(y1)), 255, -1)
for cx in (x0 + r, x1 - r): cv2.circle(m, (q(cx), q(y1 - r)), q(r), 255, -1, lineType=cv2.LINE_AA)
clip = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255; clip[:700] = 1
im[..., 3] *= clip; save(im, 'D14_МУЖ')
im = load('B5'); er = cv2.erode(im[..., 3], np.ones((7, 7), np.uint8)); im[318:376, :, 3] = np.minimum(im[318:376, :, 3], er[318:376]); save(im, 'B5')
print('ok')
