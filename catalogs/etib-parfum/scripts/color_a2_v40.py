"""v40: A2 colour correction — the glass read greyish next to the other bottles.
Whites lifted (levels), gentle S-curve for contrast, lilac juice a little richer, slight cool-neutral balance.
Blacks of the rose cap stay as they are. Usage: color_a2_v40.py <in png> <out png>"""
import sys, numpy as np
from PIL import Image
src, out = sys.argv[1:3]
im = np.array(Image.open(src).convert('RGBA')).astype(np.float32)/255
rgb, a = im[..., :3], im[..., 3]
m = a > 0.9
lum = rgb.mean(axis=2)
lo, hi = np.percentile(lum[m], 1.5), np.percentile(lum[m], 97)
rgb = np.clip((rgb - lo)/(hi - lo)*(0.97 - 0.02) + 0.02, 0, 1)                # levels: whites to near white
t = rgb; rgb = t + 0.35*(t*t*(3 - 2*t) - t)                                     # soft S-curve
g = rgb.mean(axis=2, keepdims=True)
sat = 1.0 + 0.25*np.clip((g - 0.15)/0.3, 0, 1)                                  # richer lilac, black cap untouched
rgb = np.clip(g + (rgb - g)*sat, 0, 1)
rgb = rgb*np.array([0.995, 0.995, 1.0])                                         # keep the glass clean, slightly cool
Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])*255).astype(np.uint8), 'RGBA').save(out)
