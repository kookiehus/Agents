"""v90 (v86 with a neutral black instead of teal): background field of page 21 in the light of the premium cover photo: amber backdrop light from the upper left
(sampled from the photo: ~150/88/38) falling off softly into deep teal-black (~2/24/27), soft vignette and fine
luminance grain like the photo (no flat radial blob). Writes ed/<name>.jpg in the sizes the build uses.
Usage: field_v86.py <data dir>"""
import sys, numpy as np, cv2
from PIL import Image
D = sys.argv[1]
AMB = np.array([150, 88, 38])/255; MID = np.array([40, 29, 20])/255; DARK = np.array([9, 10, 9])/255   # v90: near-neutral black like the premium cover, no blue
for name, w, h in (('field90', 620, 360), ('field90_hi', 1860, 1080)):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u, v = xx/w, yy/h
    d = np.sqrt(((u + 0.05)/1.05)**2 + ((v + 0.10)/0.95)**2)              # distance from a light just off the upper-left corner
    t1 = np.clip(d/0.62, 0, 1); t1 = t1*t1*(3 - 2*t1)                         # amber -> mid
    t2 = np.clip((d - 0.45)/0.75, 0, 1); t2 = t2*t2*(3 - 2*t2)                # mid -> teal-black
    rgb = AMB*(1 - t1[..., None]) + MID*t1[..., None]
    rgb = rgb*(1 - t2[..., None]) + DARK*t2[..., None]
    rng = np.random.RandomState(7)
    low = cv2.GaussianBlur(rng.randn(h, w).astype(np.float32), (0, 0), w/40)*0.9          # gentle uneven light, like a real backdrop
    rgb = rgb*(1 + 0.06*low[..., None])
    vig = 1 - 0.28*np.clip(np.sqrt((u - 0.35)**2 + (v - 0.4)**2) - 0.35, 0, 1)**1.4
    rgb = rgb*vig[..., None]
    g = rng.randn(h, w).astype(np.float32)*(0.020 if w > 1000 else 0.010)                 # fine film grain
    rgb = rgb + g[..., None]*(0.4 + 0.6*rgb.mean(axis=2, keepdims=True)/0.5)
    Image.fromarray((np.clip(rgb, 0, 1)*255).astype(np.uint8)).save(f'{D}/ed/{name}.jpg', quality=95); print(name)
