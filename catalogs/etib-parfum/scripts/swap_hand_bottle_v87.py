"""v87: the bottle held in the hands (page 21) is replaced with the owner's new render of the black ETIB PARFUM bottle.
1) new bottle cut from black: luminance > threshold, holes filled, reflection under the base cut off; the clear cap gets
   alpha from its own luminance (glass lets the page through).
2) placement: scale / angle / position fitted by maximising overlap with the old bottle (old bottle = dark or neutral
   non-skin pixels in the hands picture).
3) compositing: hand skin, nails and the woman's fingertip stay on top; old-bottle pixels not covered by the new one
   become transparent; soft contact shadow where fingers touch the glass; warm environment tint on the glass highlights.
Usage: swap_hand_bottle_v87.py <hands_cut_v2.png> <new bottle png> <out.png> [debug dir]"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as nd
src, newp, out = sys.argv[1:4]; dbg = sys.argv[4] if len(sys.argv) > 4 else None
H = np.array(Image.open(src).convert('RGBA')).astype(np.float32)/255; hh, hw = H.shape[:2]
rgb, al = H[..., :3], H[..., 3]
L = rgb.mean(axis=2); sat = rgb.max(axis=2) - rgb.min(axis=2)
hsv = cv2.cvtColor((rgb*255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
box = np.zeros((hh, hw), bool); box[560:1620, 1000:1900] = True
skin = (al > 0.5) & (((hsv[..., 0] < 25) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 40) & (hsv[..., 2] > 70))
skin = nd.binary_opening(skin, iterations=2); skin = nd.binary_closing(skin, iterations=3); skin = nd.binary_fill_holes(skin)
nail = Image.new('L', (hw, hh), 0); ImageDraw.Draw(nail).polygon([(1592, 590), (1708, 590), (1698, 692), (1664, 728), (1624, 737), (1592, 718)], fill=255)
yy_, xx_ = np.mgrid[0:hh, 0:hw]
skin &= ~((yy_ < 960) & (xx_ < 1585))                                               # reflections in the old cap are not skin: above the body only the woman's finger counts
skin &= ~((yy_ < 960) & (xx_ >= 1585) & (yy_ > 745))
skin &= ~((yy_ < 960) & (hsv[..., 2] < 150))                                        # dark old-cap pixels next to the fingertip
tip = Image.new('L', (hw, hh), 0)                                                   # woman's fingertip with the nail, traced on the photo
ImageDraw.Draw(tip).polygon([(1601, 720), (1603, 700), (1612, 668), (1628, 636), (1645, 610), (1662, 592), (1680, 580), (1700, 568), (1730, 555),
                             (1800, 540), (1800, 600), (1785, 622), (1765, 645), (1745, 662), (1722, 678), (1700, 690), (1675, 698), (1655, 701),
                             (1640, 712), (1620, 722), (1606, 724)], fill=255)
nailm = np.array(tip) > 0
skin &= ~((yy_ < 760) & (xx_ > 1540) & (xx_ < 1800) & ~nailm & (yy_ > 560))          # no stray specks around the fingertip
occ = skin | nailm
old = box & (al > 0.5) & ~occ
old = nd.binary_opening(old, iterations=2)
lab, n = nd.label(old); sizes = np.bincount(lab.ravel()); sizes[0] = 0; old = lab == np.argmax(sizes)
# ---- new bottle
B = np.array(Image.open(newp).convert('RGB')).astype(np.float32)/255; bh, bw = B.shape[:2]; BL = B.mean(axis=2)
YB = 1283
m = BL > 14/255; m[YB:] = False; m = nd.binary_closing(m, iterations=4); m = nd.binary_fill_holes(m)
lab, n = nd.label(m); sizes = np.bincount(lab.ravel()); sizes[0] = 0; m = lab == np.argmax(sizes)
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2); m = np.clip((m - 0.5)*2.2 + 0.5, 0, 1); m[YB:] = 0
capzone = np.zeros((bh, bw), np.float32); capzone[100:452, 360:720] = 1; capzone = cv2.GaussianBlur(capzone, (0, 0), 3)
metal = np.zeros((bh, bw), np.float32); metal[150:452, 445:640] = 1; metal[440:510, 420:665] = 1; metal = cv2.GaussianBlur(metal, (0, 0), 2)
glass_a = np.clip(0.25 + BL*2.2, 0, 1)                                         # clear glass: dark parts let the page through
balpha = m*(1 - capzone*(1 - np.maximum(glass_a, metal)))
newm = m > 0.5
def place(s, ang, cx, cy):
    M = cv2.getRotationMatrix2D((bw/2, 505.0), ang, s); M[0, 2] += cx - bw/2; M[1, 2] += cy - 505.0
    return M
Y0, Y1, X0, X1 = 500, 1700, 950, 1950
oldb = old[Y0:Y1, X0:X1]; occb = occ[Y0:Y1, X0:X1]; P = 1500
best = (0, 0.86, -11.0, 1512, 968) if os.environ.get('FIT') == 'fixed' else None     # FIT=fixed: reuse the fitted placement
for s_ in (np.arange(0.84, 1.08, 0.02) if best is None else []):
    for ang in np.arange(-15, -3.9, 1.0):
        Wm = cv2.warpAffine(newm.astype(np.float32), place(s_, ang, P, P), (3000, 3000)) > 0.5
        for cx in range(1360, 1580, 8):
            for cy in range(840, 1040, 8):
                oy, ox = P - cy, P - cx                                             # canvas pixel = page pixel + (oy, ox)
                ww = Wm[Y0 + oy:Y1 + oy, X0 + ox:X1 + ox] & ~occb
                iou = (ww & oldb).sum()/max(1, (ww | oldb).sum())
                if best is None or iou > best[0]: best = (iou, s_, ang, cx, cy)
print('fit', best)
_, s, ang, cx, cy = best
M = place(s, ang, cx, cy)
Bw = cv2.warpAffine(B, M, (hw, hh), flags=cv2.INTER_LANCZOS4)
Aw = cv2.warpAffine(balpha.astype(np.float32), M, (hw, hh), flags=cv2.INTER_LINEAR)
Mw = cv2.warpAffine(m.astype(np.float32), M, (hw, hh), flags=cv2.INTER_LINEAR)
# environment: warm light on the glass highlights, a touch of contrast to sit in the photo
hi = np.clip((Bw.mean(axis=2, keepdims=True) - 0.35)/0.5, 0, 1)
Bw = Bw*(1 - 0.5*hi) + Bw*np.array([1.06, 1.0, 0.90])*0.5*hi
# v88: tone the render down to the photo: lifted blacks, softer highlights, less micro-contrast (the hands are a soft photo)
Bl = cv2.GaussianBlur(Bw, (0, 0), 1.2); Bw = Bl + (Bw - Bl)*0.75
lumB = Bw.mean(axis=2, keepdims=True); Bw = lumB + (Bw - lumB)*0.9
Bw = 0.075 + Bw*0.80; Bw = Bw**1.06
Bw = Bw*np.array([1.02, 1.0, 0.97])                                                    # same warm cast as the skin light
# compositing
occs = cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 1.0)
d_occ = nd.distance_transform_edt(~occ)
shadow = np.clip(1 - d_occ/22, 0, 1)*0.45*(Mw > 0.5)                                  # contact shadow of fingers on the glass
Bw = Bw*(1 - shadow[..., None])
# cast shadow of the woman's fingertip on the cap and of the thumb on the glass (light from the upper left)
cast = np.zeros((hh, hw), np.float32); sh_src = (nailm | skin).astype(np.float32)
M_sh = np.float32([[1, 0, 16], [0, 1, 22]]); cast = cv2.warpAffine(sh_src, M_sh, (hw, hh))
cast = cv2.GaussianBlur(cast, (0, 0), 9)*(1 - occ)*(Mw > 0.5)
Bw = Bw*(1 - 0.55*cast[..., None])
tipsh = cv2.warpAffine(nailm.astype(np.float32), np.float32([[1, 0, -6], [0, 1, 30]]), (hw, hh))        # the fingertip shades the cap right under it
tipsh = cv2.GaussianBlur(tipsh, (0, 0), 14)*(1 - occ)*(Mw > 0.5)
Bw = Bw*(1 - 0.75*np.clip(tipsh*1.4, 0, 1)[..., None])
Aw = np.maximum(Aw, np.clip(tipsh*1.4, 0, 1)*0.6*(Mw > 0.5))                           # the clear glass under the shadow reads darker, not see-through
oldd = nd.binary_dilation(old, iterations=3)
res_rgb = rgb.copy(); res_a = al.copy()
res_a = np.where(oldd & ~occ, 0.0, res_a)                                             # remove the old bottle
soft = cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 0.9)
res_a = np.where(oldd, res_a*np.clip(soft*1.6, 0, 1), res_a)                       # anti-aliased finger edges over the glass
# new bottle under the hands: "over" compositing of old remaining layer over bottle
top_a = res_a*(1 - 0) ; top_rgb = res_rgb
out_a = top_a + Aw*(1 - top_a)
out_rgb = (top_rgb*top_a[..., None] + Bw*Aw[..., None]*(1 - top_a[..., None]))/np.maximum(out_a[..., None], 1e-4)
O = np.dstack([np.clip(out_rgb, 0, 1), np.clip(out_a, 0, 1)])
Image.fromarray((O*255).astype(np.uint8), 'RGBA').save(out); print(out)
if dbg:
    os.makedirs(dbg, exist_ok=True)
    v = np.zeros((hh, hw, 3), np.uint8); v[old] = (255, 0, 0); v[occ] = (0, 200, 0); v[(cv2.warpAffine(newm.astype(np.float32), M, (hw, hh)) > 0.5) & ~occ] += np.uint8([0, 0, 200])
    Image.fromarray(v).crop((950, 500, 1950, 1700)).resize((500, 600)).save(f'{dbg}/fit.png')
