# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=11,<13"]
# ///
"""Rug and amp grille cloth for the Blender studio (deterministic)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, random
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'blender/textures'
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(1176)
FONTS = Path('/System/Library/Fonts/Supplemental')
def font(size, bold=False):
    choices = [FONTS / ('Arial Bold.ttf' if bold else 'Arial.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    return ImageFont.truetype(str(next(p for p in choices if p.exists())), size)
def mix(a,b,t): return tuple(round(x+(y-x)*t) for x,y in zip(a,b))
def grain(im, amount=6):
    p=im.load()
    for y in range(im.height):
        for x in range(im.width):
            v=rng.randint(-amount,amount)
            p[x,y]=tuple(max(0,min(255,c+v)) for c in p[x,y][:3])
    return im
# Handwoven rug, with a distressed geometric border.
im=Image.new('RGB',(1600,1000),(178,46,34));d=ImageDraw.Draw(im)
for inset,c in [(18,(22,24,58)),(44,(240,150,52)),(60,(26,40,96)),(90,(226,96,40)),(112,(22,24,58)),(140,(150,32,30))]:
    d.rectangle((inset,inset,1600-inset,1000-inset),outline=c,width=15)
for x in range(180,1490,170):
    for y in range(180,870,160):
        d.polygon([(x,y-48),(x+60,y),(x,y+48),(x-60,y)],outline=(246,170,60),width=8)
        d.polygon([(x,y-22),(x+28,y),(x,y+22),(x-28,y)],fill=(28,44,108))
for i in range(40000):
    x,y=rng.randrange(1600),rng.randrange(1000)
    d.line((x,y,x+rng.randrange(1,7),y),fill=rng.choice([(196,64,40),(120,30,30),(230,110,50),(40,40,90)]),width=1)
grain(im,8).save(OUT/'rug.png')
# Amp's woven diamond cloth.
im=Image.new('RGB',(768,768),(68,50,38));d=ImageDraw.Draw(im)
for a in range(-768,1536,64):
    d.line((a,0,a+768,768),fill=(169,131,80),width=5)
    d.line((a,0,a-768,768),fill=(169,131,80),width=5)
for i in range(0,768,5):d.line((0,i,768,i),fill=(86,67,46),width=1)
grain(im,5).save(OUT/'grille.png')
print('Created rug and grille textures in',OUT)
