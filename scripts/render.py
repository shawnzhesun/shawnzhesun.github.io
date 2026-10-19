"""Render locally; Blender is never needed by the web host."""
import os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
blender=os.environ.get('BLENDER_BIN') or shutil.which('blender')
if not blender and Path('/Applications/Blender.app/Contents/MacOS/Blender').exists():
    blender='/Applications/Blender.app/Contents/MacOS/Blender'
if not blender:raise SystemExit('Set BLENDER_BIN to your Blender executable.')
subprocess.run([blender,'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'blender/studio.py'),'--',*sys.argv[1:]],cwd=ROOT,check=True)
subprocess.run(['uv','run',str(ROOT/'scripts/pack.py')],cwd=ROOT,check=True)
