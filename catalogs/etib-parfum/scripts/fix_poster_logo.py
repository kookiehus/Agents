import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
D, out, ang, cx, cy, lw = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
im = np.array(Image.open(f'{D}/poster_wood_src.png').convert('RGB'))
x0, y0, x1, y1 = 540, 722, 672, 835
reg = im[y0:y1, x0:x1].astype(float); lum = reg.mean(axis=2)
bg = nd.median_filter(lum, size=15)
m = (lum < bg - 14)
m = nd.binary_opening(m, iterations=1); m = nd.binary_dilation(m, iterations=3)
mask = np.zeros(im.shape[:2], np.uint8); mask[y0:y1, x0:x1] = m*255
yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
mask[yy > 839 - (xx - 575)*0.3] = 0                                   # keep the ETIB PARFUM text below the mark
clean = cv2.inpaint(im, mask, 6, cv2.INPAINT_TELEA)
# colour of the embossed print: dark pixels of the old mark
col = reg[(lum < bg - 30)].mean(axis=0) if (lum < bg - 30).any() else np.array([120, 70, 30.])
lg = Image.open(f'{D}/logo.png').convert('RGBA'); a = lg.getchannel('A')
k = lw/lg.width; a = a.resize((round(lg.width*k*4), round(lg.height*k*4)), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True).resize((round(lg.width*k*4)//4*0 + 1, 1)) if False else a
A = a.resize((round(lg.width*k*4), round(lg.height*k*4)), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
A = A.resize((A.width//4, A.height//4), Image.LANCZOS)
al = np.array(A).astype(float)/255*0.92
h, w = al.shape; px, py = round(cx - w/2), round(cy - h/2)
canvas = clean.astype(float)
sub = canvas[py:py+h, px:px+w]
hi = np.zeros_like(al); hi[1:, 1:] = al[:-1, :-1]                        # soft light edge below-right, like an engraving
hi = np.clip(hi - al, 0, 1)*0.35
sub[:] = sub*(1 - al[..., None]) + col*al[..., None]
sub[:] = sub*(1 - hi[..., None]) + np.array([255, 235, 205.])*hi[..., None]
Image.fromarray(np.clip(canvas, 0, 255).astype('uint8')).save(out)
Image.fromarray(np.clip(canvas, 0, 255).astype('uint8')).crop((500, 690, 800, 900)).resize((1200, 840), Image.LANCZOS).save(out.replace('.png', '_zoom.png'))
print('colour', col.round())
