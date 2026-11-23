"""v55: ETIB PARFUM house bottle made whiter (the owner found it grey). Neutral (unsaturated) glass is lifted with a
soft curve towards white; gold logo, collar and pump (saturated) are left as they were; the clear cap is lifted less.
Usage: prepare_bottles_v55.py <bottles_v54/ETIB_white.png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
im = Image.open(SRC).convert('RGBA'); a = np.array(im).astype(np.float32)/255
rgb, al = a[..., :3], a[..., 3]
g = rgb.mean(axis=2); tex = np.sqrt(np.maximum(cv2.GaussianBlur(g*g, (0, 0), 2.5) - cv2.GaussianBlur(g, (0, 0), 2.5)**2, 0))
smooth_w = np.clip(1 - (tex - 0.012)/0.02, 0, 1)*(al > 0.99)   # flat frosted areas only (sparkles, logo and edges keep their detail)
rgb = rgb*(1 - smooth_w[..., None]) + cv2.GaussianBlur(rgb, (0, 0), 4.0)*smooth_w[..., None]
mx, mn = rgb.max(axis=2), rgb.min(axis=2); sat = (mx - mn)/np.maximum(mx, 1e-3)
neutral = np.clip(1 - sat/0.22, 0, 1)                       # 1 on white / grey glass, 0 on gold
h = rgb.shape[0]; ys = np.arange(h)[:, None]
body = (ys > 0.235*h).astype(np.float32)                    # below the collar: frosted body; above: clear glass cap
amt = neutral*(0.35 + 0.65*body)
G = 2.5
lift = rgb*G/(1 + (G - 1)*rgb)                              # smooth shoulder: greys go towards white, no clipped / blotchy whites
cool = np.array([0.995, 0.995, 1.0])                        # clean white, not cream
new = rgb*(1 - amt[..., None]) + np.clip(lift*cool, 0, 1)*amt[..., None]
Image.fromarray((np.dstack([np.clip(new, 0, 1), al])*255).astype(np.uint8), 'RGBA').save(f'{OUT}/ETIB_white.png'); print('ETIB_white.png', im.size)
