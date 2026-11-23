"""v66: C27 a little more saturated (owner's request): saturation +18 %, slight contrast lift; outline as in v65.
Usage: prepare_bottles_v66.py <bottles_v65/C27_ЖЕН.png> <out dir>"""
import sys, os, numpy as np
from PIL import Image, ImageEnhance
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
im = Image.open(SRC).convert('RGBA'); a = im.getchannel('A')
rgb = ImageEnhance.Color(im.convert('RGB')).enhance(1.18)
rgb = ImageEnhance.Contrast(rgb).enhance(1.04)
out = rgb.convert('RGBA'); out.putalpha(a); out.save(f'{OUT}/C27_ЖЕН.png'); print('C27_ЖЕН.png', im.size)
