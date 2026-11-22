"""v33: V22 Incredible — the white strip under the red base (photo backdrop) is cut off.
Usage: fix_bottles_v33.py <bottles_v27 dir> <out dir>"""
import sys, os, numpy as np
from PIL import Image
src, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
a = np.array(Image.open(f'{src}/V22_ЖЕН.png').convert('RGBA')).astype(np.float32)
al = a[..., 3] > 128; lum = a[..., :3].min(axis=2)
rows = [y for y in range(a.shape[0]) if al[y].any()]
for y in rows[::-1]:                                    # from the bottom up: rows that are mostly white backdrop go
    m = al[y]
    if np.median(lum[y][m]) < 200: break
    a[y, :, 3] = 0
a = a[:y + 1]; a[-1, :, 3] *= 0.6                          # soft last row
Image.fromarray(a.astype(np.uint8), 'RGBA').save(f'{out}/V22_ЖЕН.png'); print('cut at row', y)

# v34: V23 Just a Kiss — the grey bevelled foot (seen from above in the photo) reads as a separate slab: cut it at the body's lower edge
a = np.array(Image.open(f'{src}/V23_ЖЕН.png').convert('RGBA')).astype(np.float32)
al = a[..., 3] > 128; rgb = a[..., :3]
grey = lambda y: abs(float(np.median(rgb[y][al[y]].max(axis=1) - rgb[y][al[y]].min(axis=1)))) < 8 and np.median(rgb[y][al[y]].mean(axis=1)) < 215
rows = [y for y in range(a.shape[0]) if al[y].any()]
y = rows[-1]
while y > rows[0] and grey(y): y -= 1
a = a[:y + 1]; a[-1, :, 3] *= 0.6
Image.fromarray(a.astype(np.uint8), 'RGBA').save(f'{out}/V23_ЖЕН.png'); print('V23 cut at row', y)
