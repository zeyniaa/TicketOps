"""Portable source deliverable with measured bootstrap artifacts; no runtimes or secrets."""
import zipfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT.parent/'ticketops-source.zip'
EXCLUDE={'.git','.venv','node_modules','work','__pycache__','.pytest_cache','dist','.sites-runtime','.openai','ticketops_backend.egg-info'}
with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED) as z:
    for folder,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in EXCLUDE and d!='checkpoints']
        for name in files:
            path=Path(folder)/name;relative=path.relative_to(ROOT)
            if path.name=='.env' or path.suffix in ('.db','.pyc') or path.name.endswith(('.db-shm','.db-wal','.tsbuildinfo')):continue
            z.write(path,Path('ticketops')/relative)
print(OUTPUT)
