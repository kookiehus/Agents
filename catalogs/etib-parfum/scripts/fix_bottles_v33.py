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
