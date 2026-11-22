"""v27: owner's new photos for C36 (Clinique Happy for Men) and N2 (Vertus Narcos'is), cut with rembg,
inside filled (clear glass must not let the old backdrop through), outline smoothed, edges un-haloed.
Usage: prepare_bottles_v27.py <uploads dir> <out dir>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
UP, OUT = sys.argv[1:3]; sess = new_session('isnet-general-use')
for code, sec in [('C36', 'МУЖ'), ('N2', 'УНИ')]:
    src = Image.open(f'{UP}/{code}.png').convert('RGB'); o = remove(src, session=sess)
    rgb = np.array(src).astype(np.float32)/255; a = np.array(o.getchannel('A')).astype(np.float32)/255
    m = a > 0.5; lab, n = nd.label(m)
    if n > 1: sz = nd.sum(m, lab, range(1, n + 1)); a = a*nd.binary_dilation(lab == (np.argmax(sz) + 1), iterations=3)
    inside = nd.binary_fill_holes(nd.binary_erosion(a > 0.5, iterations=2)); a = np.maximum(a, nd.binary_erosion(inside, iterations=2).astype(np.float32))
    a = np.clip((cv2.GaussianBlur(a, (0, 0), 0.9) - 0.5)*1.8 + 0.5, 0, 1)
    solid = a > 0.97; idx = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    w = np.clip((0.97 - a)/0.5, 0, 1)[..., None]; rgb = rgb*(1 - w) + rgb[idx[0], idx[1]]*w
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    k = 900/im.height
    if k > 1: im = im.resize((round(im.width*k), 900), Image.LANCZOS); c = im.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); im = Image.merge('RGBA', (*c.split(), im.getchannel('A')))
    im.save(f'{OUT}/{code}_{sec}.png'); print(code, im.size)
