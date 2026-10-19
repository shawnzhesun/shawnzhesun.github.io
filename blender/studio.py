"""Shawn's Studio — a reproducible Blender scene. No external model assets.
Run through scripts/render.py; renders beauty, object IDs and interaction metadata.
"""
import bpy, bmesh, math, json, sys, random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R = math.radians
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build'
OUT.mkdir(exist_ok=True)
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
width = int(args[args.index('--width')+1]) if '--width' in args else 1920
samples = int(args[args.index('--samples')+1]) if '--samples' in args else 64
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
rng = random.Random(1176)
HOT = {'guitar':1,'amp':2,'rack':3,'poster':4,'modern-times':5,'tv':6,'pedals':7,'badge':8,'echo-of-tide':9,'journal':10}
ID_STEP=23  # mask value = id*ID_STEP; must match scripts/pack.py
INKLESS=set()  # tiny details that would turn into noise under the comic ink lines
MATS={}
def linear(x): return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
def color(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (1,3,5))+(1,)
def mat(name,h,rough=.5,metal=0,emit=0,texture=None,noise=False,generated=False,toon=.3):
    if name in MATS:return MATS[name]
    m=bpy.data.materials.new(name); m.diffuse_color=color(h); m.use_nodes=True
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color(h)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Emission Color'].default_value=color(h);p.inputs['Emission Strength'].default_value=emit
    if texture:
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'blender/textures'/texture))
        m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
        if generated:nt.links.new(nt.nodes.new('ShaderNodeTexCoord').outputs['Generated'],t.inputs['Vector'])
        if emit:m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color'])
    if noise:
        n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=95
        b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.21;b.inputs['Distance'].default_value=.025
        m.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
    if toon and not emit and metal<.5:
        # Hard-edged light/shadow terminator: the anime/comic cel look, still lit by the scene.
        cel=nt.nodes.new('ShaderNodeBsdfToon');cel.inputs['Size'].default_value=.55;cel.inputs['Smooth'].default_value=.03
        if texture:nt.links.new(t.outputs['Color'],cel.inputs['Color'])
        else:cel.inputs['Color'].default_value=color(h)
        mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs['Fac'].default_value=toon
        nt.links.new(p.outputs['BSDF'],mx.inputs[1]);nt.links.new(cel.outputs['BSDF'],mx.inputs[2])
        nt.links.new(mx.outputs['Shader'],nt.nodes['Material Output'].inputs['Surface'])
    MATS[name]=m;return m
def mesh(name,bm,m,loc=(0,0,0),rot=(0,0,0),hot=None,parent=None,bevel=0):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=rot
    if m:me.materials.append(m)
    if hot:ob['hot']=hot
    if parent:ob.parent=parent
    if bevel:
        mod=ob.modifiers.new('Soft handmade edges','BEVEL');mod.width=bevel;mod.segments=3
        mod=ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return ob
def box(name,size,loc,m,rot=(0,0,0),hot=None,parent=None,bevel=.025):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=size,verts=bm.verts)
    return mesh(name,bm,m,loc,rot,hot,parent,bevel)
def cyl(name,r,depth,loc,m,rot=(0,0,0),hot=None,parent=None,r2=None,seg=40):
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r if r2 is None else r2,depth=depth)
    for f in bm.faces:f.smooth=abs(f.normal.z)<.9
    return mesh(name,bm,m,loc,rot,hot,parent)
def ball(name,loc,scale,m,hot=None,parent=None):
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=24,v_segments=12,radius=1);bmesh.ops.scale(bm,vec=scale,verts=bm.verts)
    for f in bm.faces:f.smooth=True
    return mesh(name,bm,m,loc,hot=hot,parent=parent)
def line(name,pts,r,m,hot=None,parent=None):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3
    s=cu.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(m)
    if hot:ob['hot']=hot
    if parent:ob.parent=parent
    return ob
def plane(name,w,h,loc,m,rot=(0,0,0),hot=None,parent=None):
    bm=bmesh.new();uv=bm.loops.layers.uv.new()
    face=bm.faces.new([bm.verts.new(v) for v in [(-w/2,0,h/2),(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2)]])
    for l,t in zip(face.loops,[(0,1),(0,0),(1,0),(1,1)]):l[uv].uv=t
    return mesh(name,bm,m,loc,rot,hot,parent)
def text(name,body,loc,size,m,hot=None,parent=None,align='CENTER',rot=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x=align;cu.extrude=.0005
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rot;cu.materials.append(m)
    if hot:ob['hot']=hot
    if parent:ob.parent=parent
    return ob
def empty(name,loc=(0,0,0),rot=(0,0,0)):
    ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rot;return ob
def silhouette(name,coords,depth,m,parent,hot,front=-.13,sharp=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='2D';cu.resolution_u=16;cu.fill_mode='BOTH';cu.extrude=depth/2;cu.bevel_depth=.025;cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(coords)-1)
    # Straight-sided parts (neck, fingerboard) need VECTOR handles; AUTO would balloon them into an oval.
    kind='VECTOR' if sharp else 'AUTO'
    for p,co in zip(sp.bezier_points,coords):p.co=(co[0],co[1],0);p.handle_left_type=kind;p.handle_right_type=kind
    sp.use_cyclic_u=True
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.rotation_euler=(math.pi/2,0,0);ob.location=(0,front,0);ob.parent=parent;cu.materials.append(m);ob['hot']=hot;return ob
# Saturated, high-contrast comic palette: warm sunset key against deep indigo shadow.
wood=mat('Warm walnut','#4a2618',noise=True)
woodlight=mat('Golden oak','#a65a2a',noise=True)
black=mat('Soft charcoal leather','#1b1c2c',noise=True)
metal=mat('Brushed black metal','#262a3a',.32,.6)
cream=mat('Ivory','#f4e2b8',.38)
gold=mat('Aged brass','#e0a43c',.3,.7)
silver=mat('Nickel hardware','#cdd6dc',.22,.85)
teal=mat('Petrol blue','#24708c',.3,.18)
red=mat('Terracotta','#c8432a',noise=True)
led=mat('Amber pilot lamps','#ffd699',.25,emit=2.2)
greenled=mat('Green status lamps','#b6daaa',emit=1.3)
# Architecture: a complete room, framed as a quiet cutaway.
box('Foundation',(30,30,.26),(0,0,-.22),wood)
for j in range(18):
    y=-3.35+j*.39
    for k in range(7):
        x=-5.83+k*1.96+( .98 if j%2 else 0)
        left=max(-5.8,x-.97);right=min(5.8,x+.97)
        if right<=left:continue
        c=rng.choice(['#5a2c1c','#6b3420','#7a3d22','#4e2618','#84442a'])
        box('Oak floorboard',(right-left,.376,.07),((left+right)/2,y,-.04),mat('Floor '+c,c,noise=True),bevel=.008)
wall=mat('Aged graphite plaster','#4a2a26',noise=True)
box('Back plaster',(30,.2,15),(0,3.5,6.9),mat('Matte black wall','#121214',.95,toon=.15))
box('Right wall',(.2,25,15),(5.9,-8,6.9),wall)
box('Floor beyond rug',(30,30,.08),(0,-9,-.1),wood)
box('Ceiling',(12,7.4,.2),(0,0,7.5),black)  # only over the room, so the low sun can reach in
for x in [-5.6,-2.6,.2,3,5.6]:box('Wall timber',(.11,.13,6.5),(x,3.34,3.2),wood)
box('Baseboard',(11.6,.18,.25),(0,3.26,.15),wood)
box('Picture rail',(11.6,.13,.1),(0,3.25,6.1),wood)
# Tall side window, with a luminous urban dusk outside.
window=mat('Evening outside','#ffffff',emit=1.0,texture='window-view.png',toon=0)
plane('Window view',5.1,5.3,(-5.77,.55,3.25),window,rot=(0,0,math.pi/2))
for yy in [-2.0,-.35,1.35,3.15]:box('Window mullion',(.15,.10,5.6),(-5.61,yy,3.2),metal)
for zz in [.45,2.9,5.95]:box('Window horizontal',(.18,5.5,.12),(-5.61,.55,zz),metal)
box('Window sill',(.48,5.6,.14),(-5.47,.55,.53),wood)
# Rug.
plane('Woven studio rug',8.6,4.9,(.05,-.7,.018),mat('Persian rug','#ffffff',texture='rug.png',noise=True),rot=(-math.pi/2,0,0))
for x in [-4.27,4.37]:
    for y in [i*.055-3.12 for i in range(90)]:line('Rug fringe',[(x,y,.025),(x+(-.1 if x<0 else .1),y,.028)],.008,cream)
# Television, intentionally containing original artwork rather than borrowed anime imagery.
# Desk monitor on a stand, centered on the desk between the speakers (gap x -1.47..2.28).
MX,MY,MZ,MW,MH=.4,2.2,4.76,2.62,1.5
box('TV chassis',(MW,.12,MH),(MX,MY,MZ),metal,hot='tv',bevel=.05)
box('Monitor stand neck',(.22,.08,1.2),(MX,MY+.1,3.45),metal,hot='tv',bevel=.02)
box('Monitor stand base',(.95,.55,.05),(MX,MY,2.86),metal,hot='tv',bevel=.02)
MONITOR=[Vector((MX+dx*MW/2,MY-.06,MZ+dz*MH/2)) for dx,dz in [(-1,1),(1,1),(1,-1),(-1,-1)]]
# The screen holds a baked terminal frame; the page animates a live one over the projected corners.
SW,SH=2.5,2.5*9/16
plane('TV terminal',SW,SH,(MX,MY-.062,MZ+.02),mat('Terminal screen','#ffffff',emit=1.0,texture='terminal.png',toon=0),hot='tv')
SCREEN=[Vector((MX+dx*SW/2,MY-.066,MZ+.02+dz*SH/2)) for dx,dz in [(-1,1),(1,1),(1,-1),(-1,-1)]]
ball('TV standby',(MX+MW/2-.1,MY-.065,MZ-MH/2+.04),(.014,.008,.008),led,hot='tv')
# Poster, with bevelled wooden frame.
box('Tide of Echo frame',(1.75,.14,2.43),(3.95,3.23,4.55),woodlight,hot='poster')
plane('Tide of Echo artwork',1.59,2.21,(3.95,3.149,4.55),mat('Band poster ink','#ffffff',texture='tide-of-echo.png'),hot='poster')
# Three album sleeves (Modern Times, Echo of Tide, Journal), each with its record sliding out.
ALBUMS=[(-4.42,5.02,'modern-times'),(-3.18,5.02,'echo-of-tide'),(-3.82,3.74,'journal')]
for i,(x,z,key) in enumerate(ALBUMS):
    size=1.02
    box('Album sleeve card',(size+.03,.03,size+.03),(x,3.235,z),black,hot=key,bevel=.004)
    plane('Album cover '+key,size,size,(x,3.217,z),mat('Album '+key,'#ffffff',.6,texture=f'album-{key}.png',toon=.1),hot=key)
    rx_,rz_=x+.36,z+.05
    cyl('Vinyl record',.47,.02,(rx_,3.262,rz_),black,rot=(math.pi/2,0,0),hot=key,seg=80)
    for rr in [.24,.32,.40]:
        pts=[(rx_+rr*math.cos(a*math.tau/96),3.250,rz_+rr*math.sin(a*math.tau/96)) for a in range(97)]
        INKLESS.add(line('Pressed grooves',pts,.003,metal,hot=key).name)
# Desk and studio rack.
box('Desktop',(6.1,1.6,.19),(.4,1.63,2.74),woodlight,bevel=.055)
box('Desk dark edge',(6.12,.07,.10),(.4,.81,2.68),wood)
for x in [-2.38,3.18]:
    for y in [1.08,2.1]:box('Desk legs',(.12,.12,2.6),(x,y,1.31),metal)
rx=.27; front=.34
for x in [rx-1.21,rx+1.21]:box('Rack oak side',(.17,1.43,2.57),(x,1.0,1.37),woodlight,hot='rack')
box('Rack base',(2.58,1.5,.18),(rx,1,.16),wood,hot='rack')
box('Rack dark interior',(2.28,1.28,2.41),(rx,1.08,1.43),black,hot='rack')
for x in [rx-1.09,rx+1.09]:box('Rack rail',(.08,.05,2.38),(x,front-.015,1.43),metal,hot='rack')
def knob(x,z,r=.073,m=black):
    cyl('Machined knob',r,.076,(x,front-.092,z),m,rot=(math.pi/2,0,0),hot='rack')
    box('Knob position',(.009,.006,r*.55),(x,front-.133,z+r*.42),cream,hot='rack',bevel=.001)
def meter(x,z,w=.36,h=.23):
    box('VU frame',(w+.055,.025,h+.05),(x,front-.055,z),black,hot='rack',bevel=.012)
    plane('VU amber glass',w,h,(x,front-.072,z),mat('VU paper','#e4bc76',emit=.18),hot='rack')
    for k in range(9):
        xx=x-w*.36+k*w*.09
        line('VU tick',[(xx,front-.081,z+h*.12),(xx,front-.081,z+h*.27)],.002,black,hot='rack')
    line('VU needle',[(x,front-.084,z-h*.36),(x+w*.19,front-.084,z+h*.24)],.006,red,hot='rack')
    text('VU label','VU',(x,front-.085,z-h*.27),.036,black,hot='rack')
for i,(z,h,c,label) in enumerate([(2.4,.28,'#3c4341','POWER / CONDITIONER'),(2.02,.4,'#5b7088','1073  /  MIC PRE & EQ'),(1.49,.58,'#2c2e30','1176'),(.98,.38,'#c2b090','BUS COMPRESSOR'),(.52,.4,'#b8b8b0','LA-2A  /  LEVELING AMPLIFIER')]):
    m=mat('Rack face '+str(i),c,.4,.5)
    box('Rack unit '+label,(2.13,.12,h),(rx,front+.02,z),m,hot='rack',bevel=.013)
    for x in [rx-.99,rx+.99]:
        for zz in [z-h/2+.055,z+h/2-.055]:
            cyl('Rack mounting screw',.025,.012,(x,front-.052,zz),silver,rot=(math.pi/2,0,0),hot='rack',seg=12)
    if i==0:
        for x in [rx-.6,rx-.42,rx-.24]:ball('Rack power LED',(x,front-.048,z),(.018,.01,.018),greenled,hot='rack')
        text('Power label',label,(rx+.29,front-.053,z-.018),.056,cream,hot='rack')
    elif i==2:
        knob(rx-.73,z,.105);knob(rx-.35,z,.105);knob(rx+.05,z,.057);knob(rx+.27,z,.057);meter(rx+.67,z+.05,.39,.28)
        text('1176 brand','1176',(rx+.64,front-.086,z-.225),.1,cream,hot='rack')
        text('1176 input','INPUT     OUTPUT',(rx-.53,front-.085,z-.20),.043,cream,hot='rack')
    elif i==3:
        meter(rx-.65,z,.28,.18);meter(rx+.65,z,.28,.18)
        for x in [rx-.18,rx+.18]:knob(x,z,.07)
        text('Rack unit caption',label,(rx,front-.062,z-h*.38),.04,black,hot='rack')
    elif i==4:
        knob(rx-.72,z+.02,.1);meter(rx,z+.03,.34,.22);knob(rx+.72,z+.02,.1)
        text('Rack unit caption',label,(rx,front-.062,z-h*.38),.04,black,hot='rack')
    else:
        for x in [rx-.76,rx-.39,rx,rx+.39,rx+.76]:knob(x,z,.072,red)
        text('Rack unit caption',label,(rx,front-.062,z-h*.36),.043,cream,hot='rack')
# Nearfield monitors with clearly visible woofer/tweeter geometry.
for x in [-1.98,2.79]:
    box('Monitor isolation pad',(1.13,.92,.09),(x,1.64,2.88),black)
    box('Studio monitor',(1.02,.85,1.39),(x,1.64,3.6),black,bevel=.085)
    for z,r in [(3.35,.33),(3.97,.135)]:
        cyl('Speaker rubber surround',r+.04,.035,(x,1.195,z),metal,rot=(math.pi/2,0,0))
        cyl('Speaker cone',r,.062,(x,1.168,z),cream if r>.2 else silver,rot=(math.pi/2,0,0),r2=r*.66)
        ball('Speaker dustcap',(x,1.119,z),(r*.37,.061,r*.37),gold if r>.2 else black)
    ball('Monitor power',(x+.35,1.193,3.02),(.016,.01,.016),greenled)
    text('Monitor badge','NEARFIELD',(x,1.188,3.045),.042,silver)
# Vox combo. Cloth is texture mapped for a recognizable diamond grille.
ax=-3.25;ay=-.05
box('VOX cabinet',(2.1,.88,1.65),(ax,ay,.93),black,hot='amp',bevel=.09)
box('Amp gold piping',(1.97,.022,1.51),(ax,ay-.453,.93),gold,hot='amp',bevel=.035)
box('Amp face',(1.90,.025,1.45),(ax,ay-.475,.93),black,hot='amp',bevel=.027)
plane('Diamond grille',1.83,1.06,(ax,ay-.494,.75),mat('Vox grille','#ffffff',texture='grille.png'),hot='amp')
text('VOX logotype','VOX',(ax+.42,ay-.5,1.43),.24,gold,hot='amp')
box('Amp handle',( .61,.18,.08),(ax,ay,1.84),black,hot='amp')
for x in [ax-.37,ax+.37]:box('Handle bracket',(.1,.21,.07),(x,ay,1.81),gold,hot='amp')
for x in [ax-.82,ax+.82]:box('Amp feet',(.18,.5,.15),(x,ay,.1),black,hot='amp')
# Shawn's guitar: a Suhr-style S body with a flame maple top in charcoal burst, white
# pearloid HSS pickguard, roasted maple neck, rosewood board and chrome hardware.
# The outline is original S-style geometry normalized to a 3.6-unit instrument.
g=empty('Stratocaster',(-3.67,-1.43,.265),(R(-7),R(-4),0))
S=.003
# u runs from the strap button to the nut; v runs treble to bass across the body.
def gp(u,v):return ((v-195)*S,u*S)
def gxyz(u,v,y=-.245):
    x,z=gp(u,v);return (x,y,z)
outline=[(8,196),(10,116),(31,52),(74,9),(124,1),(178,10),(235,31),(286,50),(329,57),(365,50),(416,36),(473,25),(521,29),(550,43),(565,63),(559,79),(519,84),(489,99),(475,121),(474,146),(483,158),(445,162),(405,162),(401,216),(414,228),(414,266),(424,291),(447,310),(478,318),(490,329),(486,345),(466,357),(435,365),(404,359),(367,345),(328,333),(288,333),(250,342),(205,363),(159,381),(109,390),(65,379),(31,354),(16,319),(10,262)]
flame=mat('Charcoal burst flame maple','#ffffff',.16,texture='guitar-top.png',generated=True,toon=.25)
flame.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.8
body=silhouette('S-style offset double-cut body',[gp(u,v) for u,v in outline],.135,flame,g,'guitar',front=-.13)
body.data.bevel_depth=.022
pickguard=[(153,330),(174,287),(180,246),(167,227),(180,187),(177,146),(189,119),(211,104),(241,104),(278,117),(316,130),(360,137),(400,135),(437,130),(447,137),(438,159),(402,162),(399,219),(405,228),(402,267),(414,298),(440,324),(474,330),(468,342),(437,345),(399,334),(365,319),(331,317),(298,321),(267,332),(232,349),(186,367),(155,366),(132,357)]
pearl=mat('White pearloid','#eef0ec',.22,toon=.3);nt=pearl.node_tree
swirl=nt.nodes.new('ShaderNodeTexNoise');swirl.inputs['Scale'].default_value=22;swirl.inputs['Detail'].default_value=8;swirl.inputs['Distortion'].default_value=3
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=color('#b9c4cc');ramp.color_ramp.elements[1].color=color('#fbfbf6');ramp.color_ramp.elements[0].position=.38;ramp.color_ramp.elements[1].position=.62
nt.links.new(swirl.outputs['Fac'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
nt.links.new(ramp.outputs['Color'],next(n for n in nt.nodes if n.type=='BSDF_TOON').inputs['Color'])
guard=silhouette('HSS white pearloid pickguard',[gp(u,v) for u,v in pickguard],.004,pearl,g,'guitar',front=-.226);guard.data.bevel_depth=.002
roasted=mat('Roasted maple','#c27a34',.35,noise=True)
# Neck narrows from its heel (56 mm equivalent) to a 42 mm nut. Same scale ratio as body.
neck=silhouette('Tapered roasted maple neck',[gp(u,v) for u,v in [(398,161),(975,174),(978,219),(399,228)]],.075,roasted,g,'guitar',front=-.143,sharp=True);neck.data.bevel_depth=.008
board=silhouette('Rosewood fingerboard',[gp(u,v) for u,v in [(400,163),(975,176),(977,217),(400,225)]],.009,mat('Rosewood','#3a2218',.45,noise=True),g,'guitar',front=-.222,sharp=True);board.data.bevel_depth=.003
# Equal temperament: fret spacing contracts toward the body, rather than the nut.
nut=976;bridge=174;scale=nut-bridge
for n in range(1,23):
    u=nut-scale*(1-2**(-n/12));half=(21+(nut-u)/(nut-400)*10)*S
    x,z=gp(u,195)
    box('Fret %02d'%n,(half*2,.013,.005),(0,-.239,z),silver,hot='guitar',parent=g,bevel=.001)
    if n in [3,5,7,9,12,15,17,19,21]:
        next_u=nut-scale*(1-2**(-(n-1)/12));zz=(u+next_u)*.5*S
        for xx in ([-.033,.033] if n==12 else [0]):ball('Pearloid position marker',(xx,-.239,zz),(.009,.003,.009),cream,hot='guitar',parent=g)
box('Bone nut',(.135,.035,.012),(0,-.234,nut*S),cream,hot='guitar',parent=g,bevel=.002)
headcoords=[(975,175),(996,151),(1030,160),(1080,173),(1130,185),(1174,193),(1195,214),(1199,241),(1186,259),(1160,263),(1138,254),(1127,239),(1094,244),(1050,251),(1025,247),(1000,232),(977,221)]
head=silhouette('Small six-inline headstock',[gp(u,v) for u,v in headcoords],.058,roasted,g,'guitar',front=-.16);head.data.bevel_depth=.006
for i in range(6):
    u=1022+i*29;v=170+i*6.5;x,z=gp(u,v)
    cyl('Tuner winding post',.013,.037,(x,-.221,z),silver,rot=(math.pi/2,0,0),hot='guitar',parent=g,seg=24)
    cyl('Tuner washer',.024,.008,(x,-.207,z),silver,rot=(math.pi/2,0,0),hot='guitar',parent=g)
    line('Tuning machine shaft',[(x,-.145,z),(x-.075,-.145,z)],.011,silver,hot='guitar',parent=g)
    ball('Tuning machine key',(x-.079,-.145,z),(.019,.017,.032),silver,hot='guitar',parent=g)
logo=text('Headstock logo','Suhr',gxyz(1085,236,-.19),.075,black,hot='guitar',parent=g)
script=Path('/System/Library/Fonts/Supplemental/Brush Script.ttf')
if script.exists():logo.data.font=bpy.data.fonts.load(str(script))
logo.rotation_euler=(math.pi/2,-math.pi/2,0)  # reads along the headstock
INKLESS.add(logo.name)
# HSS: two white single coils and a white bridge humbucker.
pickup=mat('White pickup cover','#f3f1ea',.3)
for i,u in enumerate([304,375]):
    x,z=gp(u,194)
    box('Single coil '+str(i),(.263,.028,.061),(x,-.251,z),pickup,hot='guitar',parent=g,bevel=.026)
    for k in range(6):ball('Six pickup polepieces',((k-2.5)*.0375,-.270,z),(.008,.004,.008),silver,hot='guitar',parent=g)
for k,du in enumerate([-11,11]):
    x,z=gp(228+du,194)
    box('Humbucker coil '+str(k),(.25,.03,.062),(x,-.252,z),pickup,hot='guitar',parent=g,bevel=.02)
    for j in range(6):ball('Humbucker pole',((j-2.5)*.0375,-.272,z),(.008,.004,.008),silver,hot='guitar',parent=g)
box('Humbucker ring',(.29,.012,.15),gxyz(228,194,-.238),pickup,hot='guitar',parent=g,bevel=.01)
box('Two-point vibrato bridge',(.272,.027,.20),gxyz(170,195,-.246),silver,hot='guitar',parent=g,bevel=.006)
for i in range(6):
    x=(i-2.5)*.039
    box('Individual bent steel saddle',(.033,.016,.084),(x,-.267,174*S),silver,hot='guitar',parent=g,bevel=.003)
    line('Individual guitar string',[(x,-.277,156*S),(x,-.275,232*S),(x*.49,-.251,976*S),gxyz(1022+i*29,170+i*6.5,-.243)],.0015,silver,hot='guitar',parent=g)
for u,v in [(205,282),(168,330)]:
    x,z=gp(u,v);cyl('Volume / tone knob',.041,.036,(x,-.258,z),pickup,rot=(math.pi/2,0,0),hot='guitar',parent=g,r2=.034)
    cyl('Knob top',.03,.002,(x,-.277,z),silver,rot=(math.pi/2,0,0),hot='guitar',parent=g)
# Oval recessed jack and five-way switch on the treble side.
x,z=gp(112,307);jack=ball('Oval recessed output jack',(x,-.218,z),(.062,.016,.116),silver,hot='guitar',parent=g);jack.rotation_euler[1]=R(-38)
ball('Jack socket',gxyz(113,307,-.239),(.019,.012,.025),black,hot='guitar',parent=g)
line('Five way blade switch',[gxyz(260,291,-.239),gxyz(254,296,-.29)],.006,silver,hot='guitar',parent=g)
ball('Switch tip',gxyz(254,296,-.292),(.014,.018,.022),cream,hot='guitar',parent=g)
line('Tremolo arm',[gxyz(170,239,-.28),gxyz(231,269,-.37),gxyz(285,273,-.37)],.007,silver,hot='guitar',parent=g)
line('Tremolo ivory tip',[gxyz(279,273,-.37),gxyz(314,273,-.37)],.012,cream,hot='guitar',parent=g)
for u,v in [(253,112),(190,135),(438,141),(403,236),(458,336),(386,329),(270,295),(210,327),(145,358),(220,243),(320,142)]:
    x,z=gp(u,v);cyl('Pickguard screw',.006,.003,(x,-.233,z),silver,rot=(math.pi/2,0,0),hot='guitar',parent=g,seg=12)
# Tube stand: two bottom cradles, rear mast and a padded neck yoke.
# Its pads share exact transformed coordinates with the supported instrument.
bpy.context.view_layer.update()
def gw(x,y,z):return tuple(g.matrix_world@Vector((x,y,z)))
stand_hub=(-3.67,-1.11,.16)
feet=[(-4.30,-1.92,.045),(-3.03,-1.92,.045),(-3.67,-.52,.045)]
for foot in feet:
    line('Tripod steel foot',[stand_hub,foot],.031,metal)
    ball('Non-slip rubber foot',foot,(.085,.10,.035),black)
for side in [-1,1]:
    # Lower bout contour at +/- .24 rests on a padded cradle at z=.035.
    p=gw(side*.24,-.135,.035)
    line('Stand lower fork',[stand_hub,(p[0],p[1]+.08,p[2]-.018),(p[0],p[1]-.10,p[2]-.018),(p[0],p[1]-.15,p[2]+.06)],.027,black)
neck_center=gw(0,-.105,1.50)
line('Stand rear mast',[stand_hub,(-3.67,-.89,neck_center[2]),(neck_center[0],neck_center[1]+.08,neck_center[2])],.029,metal)
for side in [-1,1]:
    line('Padded neck support',[(neck_center[0],neck_center[1]+.08,neck_center[2]),(neck_center[0]+side*.103,neck_center[1]+.04,neck_center[2]),(neck_center[0]+side*.103,neck_center[1]-.17,neck_center[2]+.01)],.02,black)
# Confirm a plausible static placement (not a rigid-body simulation).
com=g.matrix_world@Vector((0,-.13,1.08))
def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
signs=[cross(feet[i],feet[(i+1)%3],com) for i in range(3)]
assert all(v>=0 for v in signs) or all(v<=0 for v in signs),'Guitar mass projection must lie inside tripod footprint'
assert min(gw(x,-.13,z)[2] for x,z in [gp(u,v) for u,v in outline])>.06,'Guitar must clear the floor'
(OUT/'guitar-placement.json').write_text(json.dumps({'approximateCenterOfMass':list(com),'standFeet':feet,'massInsideFootprint':True,'backLeanDegrees':7,'floorClearanceChecked':True,'reference':'Suhr-style S body; original geometry'},indent=2))

# Pedalboard, stomp switches and patch cables.
box('Pedal flight case',(3.0,1.25,.19),(-.95,-2.02,.18),black,hot='pedals')
for y in [-2.67,-1.38]:box('Board metal edging',(3.08,.055,.14),(-.95,y,.23),silver,hot='pedals',bevel=.006)
for x in [-2.48,.58]:box('Board corner protector',(.065,1.3,.14),(x,-2.02,.23),silver,hot='pedals')
for x,y,c,label,ink in [(-1.95,-2.2,'#2f6fb0','COMP','#f4e2b8'),(-1.25,-2.2,'#1a1a1c','DRIVE','#f4e2b8'),(-.55,-2.2,'#e9dfc4','OCD','#1b1c2c')]:
    pm=mat(label,c,.4,.1)
    box(label+' stompbox',(.53,.48,.18),(x,y,.39),pm,hot='pedals',bevel=.035)
    for xx in [x-.14,x+.14]:cyl('Pedal knob',.046,.056,(xx,y+.12,.51),black if c!='#1a1a1c' else cream,hot='pedals')
    cyl('Footswitch',.039,.06,(x,y-.14,.52),silver,hot='pedals')
    ball('Pedal LED',(x+.15,y-.14,.485),(.015,.015,.01),led,hot='pedals')
    text('Pedal label',label,(x,y-.02,.49),.05,mat('Pedal ink '+ink,ink),hot='pedals',rot=(0,0,0))
# Two larger Strymon-style units: knob row, three footswitches, small display.
for x,c,label in [(-1.75,'#2c4f86','DELAY'),(-.6,'#3d4048','REVERB')]:
    y=-1.62;pm=mat('Strymon '+label,c,.35,.25)
    box(label+' workstation',(1.0,.5,.17),(x,y,.385),pm,hot='pedals',bevel=.03)
    for k in range(6):cyl('Pedal knob',.035,.045,(x-.37+k*.148,y+.13,.49),black,hot='pedals')
    for k in range(3):cyl('Footswitch',.036,.05,(x-.3+k*.3,y-.15,.5),silver,hot='pedals')
    box('Pedal display',(.16,.04,.008),(x,y-.02,.474),mat('Pedal display','#7fe0ff',emit=1.5),hot='pedals')
    text('Pedal label',label,(x,y+.04,.475),.045,cream,hot='pedals',rot=(0,0,0))
for x in [-1.72,-1.02]:line('Patch cable',[(x,-2.15,.4),(x-.03,-2.55,.32),(x+.21,-2.54,.32),(x+.21,-2.15,.4)],.018,black,hot='pedals')
line('Instrument cable',[gw(*gxyz(113,307,-.28)),(-3.8,-1.83,.10),(-3.1,-2.85,.045),(-1.8,-3.0,.04),(-1.5,-2.9,.05),(-2.5,-1.7,.2)],.025,black)
line('Amp cable',[(-3.9,-.6,1.5),(-4.2,-.9,.06),(-2.8,-1.1,.05),(-2.6,-2.15,.1)],.021,black)
# Desk lamp, books, cup and small personal details.
cyl('Lamp base',.29,.06,(.95,1.68,2.87),metal)
line('Lamp arm',[(.95,1.68,2.91),(1.02,1.66,3.38),(.85,1.58,3.7),(.59,1.42,3.79)],.037,metal)
cyl('Lamp shade',.34,.28,(.59,1.42,3.72),gold,r2=.10)
cyl('Lamp warm interior',.30,.025,(.59,1.42,3.576),led)
for i,c in enumerate(['#567c78','#b08a5d','#a3624d']):
    box('Book cover',(.79,.49,.065),(-.53,1.62,2.88+i*.08),mat('Book '+c,c),rot=(0,0,R(i*7-8)))
cyl('Coffee mug',.115,.21,(1.57,1.19,2.96),cream)
cyl('Coffee surface',.095,.006,(1.57,1.19,3.068),mat('Coffee','#4b3327'))
line('Mug handle',[(1.67,1.19,3.03),(1.78,1.19,3.02),(1.78,1.19,2.92),(1.67,1.19,2.91)],.022,cream)
# Plant next to the window.
cyl('Terracotta planter',.37,.55,(-4.71,2.39,.3),red,r2=.46)
soil=mat('Soil','#3e4032');cyl('Plant soil',.43,.025,(-4.71,2.39,.59),soil)
leafm=[mat('Leaf '+str(i),c,.65) for i,c in enumerate(['#536f55','#71805a','#849365'])]
for i in range(19):
    a=i*2.399;z=.9+i*.092;dx=math.cos(a)*rng.uniform(.4,.85);dy=math.sin(a)*rng.uniform(.35,.65)
    line('Plant stem',[(-4.71,2.39,.52),(-4.7,2.39,z),(-4.71+dx,2.39+dy,z+.15)],.011,leafm[0])
    ob=ball('Plant leaf',(-4.71+dx,2.39+dy,z+.19),(.32,.12,.025),leafm[i%3]);ob.rotation_euler=(R(20),R(-20),a)
# Stool: keep the room open so the recording equipment stays visible.
for x in [3.25,4.02]:
    for y in [-.77,.02]:line('Stool leg',[(x,y,.07),(3.64+(x-3.64)*.75,-.37+(y+.37)*.75,1.38)],.035,metal)
box('Studio stool seat',(1.15,1.03,.18),(3.64,-.37,1.45),mat('Cognac leather','#94684b',noise=True),bevel=.1)
line('Stool backrest',[(3.11,-.05,1.42),(3.15,.16,2.13),(3.64,.20,2.25),(4.12,.16,2.13),(4.17,-.05,1.42)],.039,metal)
box('Stool back cushion',(.91,.13,.38),(3.64,.19,2.04),MATS['Cognac leather'],bevel=.09)
# Acoustic slats on the right create rhythm without hard graphic contrast.
for x in [4.95+i*.09 for i in range(7)]:box('Acoustic timber',(.035,.21,2.2),(x,3.25,1.68),woodlight)
# Copper service pipes frame the back wall.
copper=mat('Oxidized copper','#947448',.43,.65,noise=True)
patina=mat('Verdigris copper','#477a76',.55,.4,noise=True)
for x in [-5.24,5.33]:
    line('Exposed copper riser',[(x,3.06,.2),(x,3.06,5.86),(x-.30,3.06,6.14),(x-1,3.06,6.14)],.065,copper)
    for z in [.5,2.18,4.15,5.6]:
        cyl('Pipe collar',.095,.12,(x,3.06,z),gold)
        box('Pipe wall bracket',(.28,.17,.11),(x,3.22,z),metal)
# A little neon: one warm tube on the right, cool accents on the rack.
cyan=mat('Cyan neon glass','#56d9ed',emit=3.6)
magenta=mat('Sunset orange neon glass','#ff7a2a',emit=3.2)
line('Rack cyan strip',[(-.97,.29,.29),(-.97,.29,2.52)],.010,cyan,hot='rack')
line('Desk orange strip',[(-2.58,.777,2.64),(3.4,.777,2.64)],.009,magenta)
# Desk gear: compact synth, cassette stack, cable coils and fluorescent tape labels.
box('Desktop synth',(1.17,.42,.08),(-.49,1.15,2.88),black,rot=(R(8),0,0))
for i in range(18):
    x=-1.02+i*.06;box('Synth white key',(.052,.24,.018),(x,1.07,2.93),cream,bevel=.001)
    if i%7 not in [2,6]:box('Synth black key',(.029,.13,.02),(x+.032,1.12,2.96),black,bevel=.001)
for x in [-.86,-.64,-.42,-.2]:cyl('Synth knob',.025,.027,(x,1.31,2.946),gold)
for i in range(3):
    box('Cassette shell',(.29,.19,.036),(1.52,1.98,2.87+i*.042),[red,teal,cream][i])
    for x in [1.45,1.58]:cyl('Tape spool',.035,.005,(x,1.98,2.89+i*.042),black)
for x in [-2.22,2.87]:
    for a in range(3):
        pts=[(x+(.12+a*.017)*math.cos(t*math.tau/48),.93+(.12+a*.017)*math.sin(t*math.tau/48),2.85+a*.012) for t in range(49)]
        line('Coiled desk cable',pts,.011,black)
# Industrial case details give the rack real fasteners and dents.
for x in [-.99,1.53]:
    for z in [.3,2.57]:
        box('Rack corner iron',(.20,.04,.22),(x,.255,z),metal,hot='rack',bevel=.008)
        for dx in [-.06,.06]:cyl('Corner iron bolt',.017,.015,(x+dx,.224,z),silver,rot=(math.pi/2,0,0),hot='rack',seg=8)
for x in [-2.45,-1.5,-.5,.5,1.5,2.5,3.33]:
    box('Desk edge hazard stripe',(.19,.014,.075),(x,.766,2.69),mat('Hazard yellow','#d6bb52'),rot=(0,R(-24),0),bevel=.001)
# Wear marks and taped setlists are modeled in the room, not a page overlay.
for i in range(90):
    x=rng.uniform(-2.45,3.2);y=rng.uniform(.9,2.30)
    line('Desktop fine scratch',[(x,y,2.84),(x+rng.uniform(.02,.1),y+.008,2.84)],.0018,cream)
# Record shelf on the right wall, spines out, like a real listening room.
shelf=mat('Shelf timber','#7a3a1e',noise=True)
for z in [.1,1.05,2.0,2.95,3.9]:box('Record shelf board',(.9,2.6,.07),(5.35,.15,z),shelf,bevel=.01)
for y in [1.45]:box('Record shelf side',(.9,.07,3.87),(5.35,y,2.0),shelf,bevel=.01)
spines=['#e8462e','#f2b632','#2b6fd6','#f4e2b8','#1b1c2c','#3aa6a0','#ff7a2a','#7b46b8','#d8322a']
for z in [.13,1.08,2.03,2.98]:
    y=-1.08
    while y<1.36:
        w=rng.uniform(.035,.07);h=rng.uniform(.62,.86)
        box('Record spine',(.78,w,h),(5.36,y+w/2,z+h/2+.035),mat('Spine '+(c:=rng.choice(spines)),c,.5),bevel=.004)
        y+=w+.004
# Name badge: a lanyard draped over the desk edge, Shawn's black badge hanging in front.
lanyard=mat('Red lanyard','#d8322a',.6)
bx=2.15
for side in [-1,1]:
    line('Badge lanyard',[(bx+side*.24,1.18,2.85),(bx+side*.19,.80,2.86),(bx+side*.08,.745,2.5),(bx+side*.015,.735,2.24)],.018,lanyard,hot='badge')
box('Badge clip',(.07,.03,.09),(bx,.735,2.19),silver,hot='badge',bevel=.006)
cardrot=(0,R(-4),0)
box('Badge card',(.6,.014,.88),(bx,.735,1.71),black,rot=cardrot,hot='badge',bevel=.012)
plane('Badge art',.58,.85,(bx,.726,1.71),mat('Badge art','#ffffff',.5,texture='badge.png',toon=.25),rot=cardrot,hot='badge')
plane('Setlist taped to amplifier',.32,.44,(-4.02,-.56,1.23),mat('Amp setlist','#ffffff',texture='flyer-3.png'),rot=(0,R(-8),0),hot='amp')

# Lights: an orange sunset key from the window, deep indigo fill, crisp cel shadows.
def light(name,typ,loc,power,h,size=1,target=None):
    d=bpy.data.lights.new(name,typ);d.energy=power;d.color=color(h)[:3]
    if typ=='AREA':d.shape='DISK';d.size=size
    if typ=='POINT':d.shadow_soft_size=size
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob);ob.location=loc
    if target:ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
light('Sunset key through window','AREA',(-5.3,-.8,4.6),1300,'#ff7428',1.4,(.5,1.2,1.4))
light('Indigo camera fill','AREA',(1,-7,6.5),520,'#3a4ee0',6,(0,1,2))
sun=bpy.data.lights.new('Low sunset sun','SUN');sun.energy=2.6;sun.color=color('#ff9248')[:3];sun.angle=R(1.5)
ob=bpy.data.objects.new('Low sunset sun',sun);bpy.context.collection.objects.link(ob);ob.rotation_euler=Vector((.9,1.6,-.62)).to_track_quat('-Z','Y').to_euler()
light('Desk lamp glow','POINT',(.59,1.42,3.48),45,'#ffc070',.15)
light('TV glow','AREA',(MX,MY-.35,MZ),60,'#7fd0ff',1.5,(MX,-1,MZ-.6))
light('Right cyan rim','AREA',(5.3,.6,4.6),520,'#38b4ff',1.6,(0,.6,2))

scene=bpy.context.scene
scene.world.color=(.05,.04,.1);scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=color('#232860')
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
# Front-on perspective camera, aimed at the center of the monitoring position.
def arg(name,default):return float(args[args.index(name)+1]) if name in args else default
cam_z=arg('--cam-z',5.0);lens=arg('--lens',33)
bpy.ops.object.camera_add(location=(.27,-12.8,cam_z));cam=bpy.context.object
cam.data.type='PERSP';cam.data.lens=lens;cam.data.sensor_width=36
scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True
scene.render.use_persistent_data=True
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
    for device in pref.devices:device.use=device.type=='METAL'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=width;scene.render.resolution_y=round(width*9/16);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.1
try:scene.view_settings.look='AgX - Punchy'
except TypeError:pass
# Comic ink: bold Freestyle outlines on silhouettes, borders and creases.
ink=bpy.data.collections.new('Inkless');scene.collection.children.link(ink)
SKIP=('Rug fringe','Desktop fine scratch','Pressed grooves','Gauge scale','VU tick','Six pickup polepieces','Humbucker pole','Pickguard screw','Fret ','Individual guitar string','Wah rubber tread','Pearloid position marker','Synth white key','Synth black key','Tape spool','Corner iron bolt','Rack mounting screw','Knob position','Tuner')
for ob in bpy.data.objects:
    if ob.type=='FONT' or ob.name in INKLESS or ob.name.startswith(SKIP):ink.objects.link(ob)
scene.render.use_freestyle=True;scene.render.line_thickness_mode='ABSOLUTE'
fs=bpy.context.view_layer.freestyle_settings;fs.crease_angle=R(128)
ls=fs.linesets[0] if len(fs.linesets) else fs.linesets.new('Ink')
ls.select_by_visibility=True;ls.select_by_edge_types=True;ls.select_silhouette=True;ls.select_border=True;ls.select_crease=True
ls.select_by_collection=True;ls.collection=ink;ls.collection_negation='EXCLUSIVE'
ls.linestyle.color=(.012,.008,.02);ls.linestyle.thickness=arg('--ink',2.0)*width/1920;ls.linestyle.thickness_position='CENTER'
scene.render.film_transparent=False
bpy.context.view_layer.update()
anchors={**{key:Vector((x,3.2,z)) for x,z,key in ALBUMS},'badge':Vector((bx,.72,1.75)),'guitar':g.matrix_world@Vector((0,-.25,1.2)),'amp':Vector((-2.78,-.55,1.43)),'rack':Vector((.9,.2,1.5)),'poster':Vector((3.95,3.1,4.6)),'tv':Vector((MX,MY-.07,MZ)),'pedals':Vector((-.55,-2.2,.5))}
count=int(args[args.index('--views')+1]) if '--views' in args else 25
if count<1 or count%2==0:raise ValueError('--views must be a positive odd number')
angles=[0] if count==1 else [-6+12*i/(count-1) for i in range(count)]
center=count//2; target=Vector((.27,1.25,arg('--target-z',2.55)));radius=arg('--radius',14.05)
frames=[]
for i,angle in enumerate(angles):
    a=R(angle);cam.location=(target.x+radius*math.sin(a),target.y-radius*math.cos(a),cam_z)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
    def project(v):
        p=world_to_camera_view(scene,cam,v);return [round(p.x,6),round(1-p.y,6)]
    frames.append({'index':i,'angle':angle,'image':f'views/{i:02d}.webp','small':f'views/{i:02d}-small.webp','mask':f'views/{i:02d}-mask.png','hotspots':{k:{'id':HOT[k],'anchor':project(v)} for k,v in anchors.items()},'screen':[project(v) for v in SCREEN],'monitor':[project(v) for v in MONITOR]})
metadata={'version':3,'idStep':ID_STEP,'width':width,'height':scene.render.resolution_y,'defaultView':center,'rotationRange':[-6,6] if count>1 else [0,0],'frames':frames,'hotspots':frames[center]['hotspots']}
(OUT/'scene.json').write_text(json.dumps(metadata,indent=2))
# Render central view first for quick art direction; then alternate outwards.
order=[center]+[i for step in range(1,center+1) for i in [center-step,center+step]]
(OUT/'views').mkdir(exist_ok=True)
for i in order:
    a=R(angles[i]);cam.location=(target.x+radius*math.sin(a),target.y-radius*math.cos(a),cam_z)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    if i==center:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'studio.blend'))
    scene.render.filepath=str(OUT/'views'/f'{i:02d}.png');bpy.ops.render.render(write_still=True)
    print('BEAUTY_VIEW',i,flush=True)
if '--no-masks' in args:raise SystemExit(0)
# Each camera has its own pixel-exact object mask and projected hotspots.
scene.render.use_freestyle=False
ids={}
for i in range(len(HOT)+1):
    m=bpy.data.materials.new('ID '+str(i));m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(linear(i*ID_STEP/255),0,0,1);e.inputs[1].default_value=1;nt.links.new(e.outputs[0],out.inputs[0]);ids[i]=m
for ob in list(bpy.data.objects):
    if ob.type in {'MESH','CURVE','FONT'}:
        ob.data.materials.clear();ob.data.materials.append(ids[HOT.get(ob.get('hot'),0)])
scene.world.node_tree.nodes['Background'].inputs[1].default_value=0
scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.cycles.filter_width=.01
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.resolution_percentage=50
for i in order:
    a=R(angles[i]);cam.location=(target.x+radius*math.sin(a),target.y-radius*math.cos(a),cam_z)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/'views'/f'{i:02d}-mask.png');bpy.ops.render.render(write_still=True)
print('STUDIO_RENDER_COMPLETE',flush=True)
