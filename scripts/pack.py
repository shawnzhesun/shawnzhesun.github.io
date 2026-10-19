# /// script
# dependencies = ["pillow>=11,<13", "numpy>=2"]
# ///
"""Package the rendered camera arc; publish its manifest only after all frames exist."""
from pathlib import Path
from PIL import Image, ImageEnhance
import json, shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'build/scene.json').read_text())
out=ROOT/'studio/assets';views=out/'views';views.mkdir(exist_ok=True)
def comic(im):
    """Punchier comic grade plus a faint screentone in the deepest shadows."""
    im=ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.12)).enhance(1.06)
    a=np.asarray(im).astype(np.float32)/255
    lum=a@np.array([.299,.587,.114],np.float32)
    h,w=lum.shape;y,x=np.mgrid[0:h,0:w]
    step=max(4,round(w/400))
    # 45-degree dot grid; dots only show where the image is already dark.
    u=((x+y)%step-step/2)/step;v=((x-y)%step-step/2)/step
    dots=(np.hypot(u,v)<.28).astype(np.float32)
    shade=np.clip((.16-lum)/.16,0,1)*.12
    a*=1-(dots*shade)[...,None]
    return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
for f in meta['frames']:
    i=f['index'];im=comic(Image.open(ROOT/'build/views'/f'{i:02d}.png').convert('RGB'))
    im.save(out/f['image'],quality=86,method=6)
    im.resize((1100,round(1100*im.height/im.width)),Image.Resampling.LANCZOS).save(out/f['small'],quality=82,method=6)
    mask=Image.open(ROOT/'build/views'/f'{i:02d}-mask.png').convert('RGB').getchannel('R')
    step,top=meta['idStep'],max(h['id'] for h in f['hotspots'].values())
    mask=mask.point(lambda x:max(0,min(top,round(x/step))))
    mask.save(out/f['mask'],optimize=True)
center=meta['frames'][meta['defaultView']]
shutil.copyfile(out/center['image'],out/'studio.webp')
shutil.copyfile(out/center['small'],out/'studio-small.webp')
shutil.copyfile(out/center['mask'],out/'hotspots.png')
poster=Image.open(ROOT/'blender/textures/tide-of-echo.png')
poster.resize((540,750),Image.Resampling.LANCZOS).save(out/'poster.webp',quality=86)
(out/'scene.json').write_text(json.dumps(meta,indent=2))
print('Packaged',len(meta['frames']),'camera views; desktop arc',round(sum((out/f['image']).stat().st_size for f in meta['frames'])/1024**2,2),'MiB')
