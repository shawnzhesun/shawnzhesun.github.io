# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=11,<13", "numpy>=2"]
# ///
"""Textures for the studio: window view, baked terminal frame, a textless amp setlist,
the Tide of Echo wave poster, album sleeves, the backstage badge and the guitar top.
Band artwork, album covers and the portrait come from blender/source/ (supplied by Shawn)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pathlib import Path
import math, random
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'blender/source'; OUT = ROOT/'blender/textures'; WEB = ROOT/'studio/assets'
OUT.mkdir(parents=True, exist_ok=True); (WEB/'albums').mkdir(parents=True, exist_ok=True)
r = random.Random(1987)
FONTS = Path('/System/Library/Fonts/Supplemental')
def font(size, name='Arial Black.ttf'):
    p = FONTS/name
    if not p.exists(): p = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    return ImageFont.truetype(str(p), size)
INK=(14,12,22); NAVY=(24,30,72); BLUE=(42,78,150); CYAN=(72,196,226); ORANGE=(246,122,38)
RED=(212,48,42); YELLOW=(255,198,62); CREAM=(250,230,192); PURPLE=(86,48,112); PLUM=(56,30,70)
def mix(a,b,t): return tuple(round(x+(y-x)*t) for x,y in zip(a,b))
def blob(d, ellipses, fill, ink=INK, w=5):
    """Union of ellipses with one continuous ink outline, like a comic cloud."""
    for x0,y0,x1,y1 in ellipses: d.ellipse((x0-w,y0-w,x1+w,y1+w), fill=ink)
    for e in ellipses: d.ellipse(e, fill=fill)
def halftone(im, box, color, step=12, angle=0.0, size=lambda x,y:3):
    d = ImageDraw.Draw(im); x0,y0,x1,y1 = box
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            rad = size(x,y)
            if rad > .4: d.ellipse((x-rad,y-rad,x+rad,y+rad), fill=color)
def grit(im, n=4000, colors=None):
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x,y = r.randrange(im.width), r.randrange(im.height)
        d.line((x,y,x+r.randrange(1,6),y+r.randrange(-1,2)), fill=r.choice(colors or [INK, CREAM]), width=1)
    return im

# --- Graphic papers (the amp setlist uses one): no words, only bold shapes. ----------
def flyer(i):
    w,h=600,800; bg=[YELLOW,CYAN,RED,CREAM,ORANGE,NAVY][i]
    im=Image.new('RGB',(w,h),bg); d=ImageDraw.Draw(im)
    if i==0:   # a curling wave
        halftone(im,(20,20,w,h),mix(bg,ORANGE,.6),14,size=lambda x,y:1+4*y/h)
        for k in range(7):
            rad=250-k*30; d.arc((80+k*12,170+k*22,80+k*12+rad*2,170+k*22+rad*2),150,400,fill=INK if k%2==0 else BLUE,width=16)
        blob(d,[(60+k*80,600-20*math.sin(k),180+k*80,700) for k in range(6)],CREAM,w=6)
    elif i==1: # an echo, rippling out
        for k in range(10): rad=40+k*30; d.ellipse((300-rad,400-rad,300+rad,400+rad),outline=INK if k%2 else NAVY,width=10)
        d.ellipse((265,365,335,435),fill=RED,outline=INK,width=8)
    elif i==2: # starburst
        pts=[(300+(260 if k%2==0 else 120)*math.cos(k*math.pi/9),400+(260 if k%2==0 else 120)*math.sin(k*math.pi/9)) for k in range(18)]
        d.polygon(pts,fill=INK); d.polygon([(300+(x-300)*.9,400+(y-400)*.9) for x,y in pts],fill=YELLOW)
        d.polygon([(330,170),(230,420),(310,420),(260,640),(390,360),(305,360)],fill=INK)
        d.polygon([(326,200),(248,410),(320,410),(282,590),(372,372),(296,372)],fill=CREAM)
    elif i==3: # halftone sun over the sea
        halftone(im,(30,60,w-30,520),ORANGE,13,size=lambda x,y:max(0,6.5-math.hypot(x-300,y-330)/38))
        d.ellipse((150,180,450,480),outline=INK,width=10)
        for k in range(8): d.line((40,540+k*30,560,540+k*30),fill=BLUE if k%2 else INK,width=10)
    elif i==4: # speed lines and a star
        for k in range(36): a=k*math.tau/36; d.line((300,400,300+700*math.cos(a),400+700*math.sin(a)),fill=mix(ORANGE,RED,.6),width=10)
        pts=[(300+(170 if k%2==0 else 70)*math.cos(-math.pi/2+k*math.pi/5),400+(170 if k%2==0 else 70)*math.sin(-math.pi/2+k*math.pi/5)) for k in range(10)]
        d.polygon(pts,fill=INK); d.polygon([(300+(x-300)*.82,400+(y-400)*.82) for x,y in pts],fill=YELLOW)
    else:      # sound waveform
        for j in range(6):
            pts=[(30+k*6,180+j*90+50*math.sin(k*.21+j)*math.sin(k*.05)) for k in range(91)]
            d.line(pts,fill=CYAN if j%2 else ORANGE,width=9)
    d.rectangle((14,14,w-14,h-14),outline=INK,width=14)
    grit(im,2600,[INK,CREAM,mix(bg,INK,.3)])
    return im
for i in range(6): flyer(i).save(OUT/f'flyer-{i}.png')
# --- Tide of Echo poster: the band's ocean, inked, under the band's own logo. -------
W,H=900,1250
src=Image.open(SRC/'echo-of-tide.png').convert('RGB')
# Left of the album's figure: the breaking wave and open water only, no title.
wave=src.crop((0,120,860,120+round(860*H/W*.80))).resize((W,round(H*.80)),Image.Resampling.LANCZOS)
wave=ImageOps.autocontrast(wave,cutoff=1); wave=Image.blend(wave,ImageOps.posterize(wave,3),.35)
poster=Image.new('RGB',(W,H),(30,26,70)); poster.paste(wave,(0,H-wave.height))
d=ImageDraw.Draw(poster)
for y in range(0,H-wave.height+40):
    d.line((0,y,W,y),fill=mix((22,20,58),(60,46,104),y/(H-wave.height+40)))
fade=Image.linear_gradient('L').resize((W,90)); poster.paste(Image.new('RGB',(W,90),(60,46,104)),(0,H-wave.height),ImageOps.invert(fade))
halftone(poster,(0,0,W,H-wave.height+30),(86,64,132),16,size=lambda x,y:2.5)
for k in range(5): d.arc((W//2-80-k*55,880-k*45,W//2+80+k*55,1040+k*45),200,340,fill=(170,226,250),width=6)
logo=Image.open(SRC/'tide-of-echo-logo.png'); logo=logo.resize((780,round(780*logo.height/logo.width)),Image.Resampling.LANCZOS)
shadow=Image.new('RGBA',logo.size,INK+(0,)); shadow.putalpha(logo.getchannel('A').filter(ImageFilter.MaxFilter(9)))
poster.paste(shadow,(66,64),shadow); poster.paste(logo,(60,56),logo)
d.rectangle((0,0,W-1,H-1),outline=INK,width=22); d.rectangle((26,26,W-27,H-27),outline=CREAM,width=5)
poster.save(OUT/'tide-of-echo.png')

# --- Album sleeves (exact supplied covers). ------------------------------------------
for key,name in [('modern-times','modern-times.png'),('echo-of-tide','echo-of-tide.png'),('journal','journal.png')]:
    cover=Image.open(SRC/name).convert('RGB')
    cover.resize((1024,1024),Image.Resampling.LANCZOS).save(OUT/f'album-{key}.png')
    cover.resize((640,640),Image.Resampling.LANCZOS).save(WEB/'albums'/f'{key}.webp',quality=86,method=6)

# --- Badge: black card, Shawn's portrait and name. -----------------------------------
face=Image.open(SRC/'shawn.png').convert('RGB')
face.resize((560,560),Image.Resampling.LANCZOS).save(WEB/'shawn.webp',quality=86,method=6)
w,h=600,880; im=Image.new('RGB',(w,h),(16,16,18)); d=ImageDraw.Draw(im)
d.rounded_rectangle((230,40,370,66),13,fill=(4,4,6),outline=(58,58,62),width=3)   # lanyard slot
photo=face.crop((60,0,740,680)).resize((500,500),Image.Resampling.LANCZOS)
im.paste(photo,(50,120))
d.text((w//2,722),'SHAWN SUN',font=font(70),fill=(246,244,238),anchor='mm')
im.save(OUT/'badge.png')

# --- Guitar top: flame maple in a charcoal burst, figure running with the grain. ----
gw,gh=1024,1400
y,x=np.mgrid[0:gh,0:gw].astype(np.float32); u=x/gw; v=y/gh
rng=np.random.default_rng(5)
streak=np.convolve(rng.random(gw*2),np.ones(5)/5,'same')            # irregular figure, one value per column
warp=(np.sin(v*7+u*3)*.018+np.sin(v*23+u*11)*.006)*gw                  # gentle ripple along the grain
idx=np.clip(((x+warp)/4+gw*.5).astype(int),0,gw*2-1)   # ~50 streaks across the body
flame=np.clip((streak[idx]-.42)*3.2,0,1)*(.75+.25*np.sin(v*140+np.sin(u*40)*3))
burst=np.clip((np.hypot((u-.5)/.5,(v-.5)/.55)-.34)/.5,0,1)**1.2
lo=np.array([22,22,26],np.float32); hi=np.array([236,233,224],np.float32)
col=lo+(hi-lo)*((.14+.86*flame[...,None])*(1-.93*burst[...,None]))   # light silver figure, dark burst edges
Image.fromarray(col.astype(np.uint8)).save(OUT/'guitar-top.png')
# --- Window: the supplied dusk photo, cropped to the window's near-square opening. ------
view=Image.open(SRC/'window-view.png').convert('RGB')
vh=view.height; vw=round(vh*5.1/5.3); x0=round((view.width-vw)*.62)
view.crop((x0,0,x0+vw,vh)).resize((1300,round(1300*5.3/5.1)),Image.Resampling.LANCZOS).save(OUT/'window-view.png')

# --- Baked terminal frame for the TV (the page animates a live version on top). ------
def terminal(w=1920,h=1080,seed=3):
    rr=random.Random(seed); im=Image.new('RGB',(w,h),(9,13,20)); d=ImageDraw.Draw(im)
    mono=lambda sz:ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',sz)
    G,C,A,P,DIM,FG=(126,231,135),(121,192,255),(242,204,96),(255,123,114),(70,84,104),(201,209,217)
    f=mono(26); fs=mono(22)
    d.rectangle((0,0,w,52),fill=(22,27,34)); d.text((24,12),'shawn@studio: ~/command-center',font=f,fill=G); d.text((w-200,12),'19:42:07',font=f,fill=A)
    panes=[(20,72,940,560,'SYSTEMS'),(960,72,1900,560,'MIX BUS'),(20,580,1180,1000,'LOG · tail -f studio.log'),(1200,580,1900,1000,'TRAFFIC')]
    for x0,y0,x1,y1,t in panes:
        d.rectangle((x0,y0,x1,y1),outline=C,width=3); d.rectangle((x0+18,y0-14,x0+30+len(t)*16,y0+14),fill=(9,13,20)); d.text((x0+24,y0-14),t,font=fs,fill=C)
    for i,(k,v) in enumerate([('cpu',.62),('gpu',.81),('mem',.47),('disk',.33),('net',.56)]):
        y=120+i*84; d.text((50,y),k.ljust(5),font=f,fill=FG); n=36
        for j in range(n): d.rectangle((150+j*20,y+4,150+j*20+14,y+34),fill=(G if j/n<.6 else A if j/n<.85 else P) if j<v*n else (28,36,48))
        d.text((880-60,y),f'{int(v*100)}%',font=f,fill=FG)
    for k in range(12):
        x=1000+k*72; lvl=rr.uniform(.3,.95)
        for j in range(16):
            yy=520-j*26; d.rectangle((x,yy-20,x+50,yy),fill=(G if j<10 else A if j<14 else P) if j<lvl*16 else (28,36,48))
    log=['render  view 12/25  ok','mix     bounce  journal_v3.wav','sync    tide-of-echo/stems  ↑ 2.1 GB','build   site  ✓ 412 ms','deploy  shawnzhesun.github.io  ok','agent   eval run 0419  pass 47/50','tune    E standard  ✓','backup  sessions → nas  ok']
    for i,line in enumerate(log): d.text((50,620+i*44),f'[19:4{i}:{rr.randint(10,59)}] ',font=fs,fill=DIM); d.text((280,620+i*44),line,font=fs,fill=[G,C,FG,A][i%4])
    d.text((50,620+8*44),'$ █',font=fs,fill=G)
    pts=[(1230+i*11,960-120-110*math.sin(i*.17)*math.sin(i*.05)-rr.uniform(0,60)) for i in range(60)]
    d.line(pts,fill=C,width=4); d.line([(1230,960),(1880,960)],fill=DIM,width=2)
    return im
terminal().save(OUT/'terminal.png')
print('Created comic textures, poster, badge, album sleeves and guitar top in',OUT)
