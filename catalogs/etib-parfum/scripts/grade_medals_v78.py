"""v78: colour work and quality for the award medals (medals_v77.png): light denoise, 2x upscale for print,
medal 1 ('Номер один', bronze-brown) warmed and brightened towards the gold of the other two, all three a touch more
contrast and clarity (local contrast), fine unsharp mask.
Usage: grade_medals_v78.py <medals_v77.png> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image
src, out = sys.argv[1:3]
im = Image.open(src).convert('RGBA'); a = np.array(im).astype(np.float32)/255
rgb, al = a[..., :3], a[..., 3]; h, w = al.shape
u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8)
rgb = cv2.fastNlMeansDenoisingColored(u8, None, 2, 2, 5, 15).astype(np.float32)/255
K = 2; rgb = cv2.resize(rgb, (w*K, h*K), interpolation=cv2.INTER_LANCZOS4); al = cv2.resize(al, (w*K, h*K), interpolation=cv2.INTER_LANCZOS4)
h, w = al.shape; xx = np.arange(w)[None, :]/w
m1 = np.clip((0.30 - xx)/0.04 + 0.5, 0, 1)[..., None]                        # medal 1 = left ~30 % of the strip, soft transition
warm = np.clip(rgb*np.array([1.10, 1.03, 0.90])*1.08, 0, 1)                    # bronze -> warmer, brighter gold
lum = warm.mean(axis=2, keepdims=True); warm = np.clip(lum + (warm - lum)*1.12, 0, 1)
rgb = rgb*(1 - m1) + warm*m1
blur = cv2.GaussianBlur(rgb, (0, 0), 12); rgb = np.clip(rgb + (rgb - blur)*0.35, 0, 1)   # clarity
rgb = np.clip((rgb - 0.5)*1.05 + 0.5, 0, 1)
blur = cv2.GaussianBlur(rgb, (0, 0), 1.4); rgb = np.clip(rgb + (rgb - blur)*0.8, 0, 1)   # fine sharpening
Image.fromarray((np.dstack([rgb, np.clip(al, 0, 1)])*255).astype(np.uint8), 'RGBA').save(out); print(out, (w, h))
