"""Blender geometry checks for the guitar's placement, independent of the web UI.
blender --background build/studio.blend --python-exit-code 1 --python scripts/check_model.py
These validate clearance and a support footprint, not a rigid-body simulation.
"""
import bpy, json
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dg=bpy.context.evaluated_depsgraph_get()
def bounds(objects):
    pts=[]
    for obj in objects:
        ev=obj.evaluated_get(dg)
        if ev.type not in {'MESH','CURVE','FONT'}:continue
        mesh=ev.to_mesh()
        pts.extend(ev.matrix_world@v.co for v in mesh.vertices)
        ev.to_mesh_clear()
    return ([min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)])
def overlaps(a,b):return all(a[0][i]<b[1][i] and a[1][i]>b[0][i] for i in range(3))
guitar=bounds([o for o in bpy.data.objects if o.get('hot')=='guitar'])
amp=bounds([o for o in bpy.data.objects if o.name=='VOX cabinet'])
desk=bounds([o for o in bpy.data.objects if o.name=='Desktop'])
assert guitar[0][2]>.035,('Guitar intersects the floor',guitar)
assert not overlaps(guitar,amp),'Guitar intersects the amplifier'
assert not overlaps(guitar,desk),'Guitar intersects the desk'
ratio=(guitar[1][2]-guitar[0][2])/(guitar[1][0]-guitar[0][0])
assert 2.5<ratio<3.8,('Unexpected guitar silhouette proportions',ratio)
assert len([o for o in bpy.data.objects if o.name.startswith('Fret ')])==22
assert len([o for o in bpy.data.objects if o.name.startswith('Individual guitar string')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('Tripod steel foot')])==3
placement=json.loads((ROOT/'build/guitar-placement.json').read_text())
assert placement['massInsideFootprint']
report={'guitarBounds':guitar,'clearOfFloor':True,'clearOfAmp':True,'clearOfDesk':True,'heightToWidth':ratio,'sixStrings':True,'frets':22,'tripodFeet':3,'approximateMassInsideFootprint':True}
(ROOT/'build/model-check.json').write_text(json.dumps(report,indent=2))
print('MODEL_CHECK_PASS',json.dumps(report))
