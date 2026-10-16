"""Portable source deliverable with measured bootstrap artifacts; no runtimes or secrets."""
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT.parent/'ticketops-source.zip'
EXCLUDE={'.git','.venv','node_modules','work','__pycache__','.pytest_cache','dist','.sites-runtime','.openai','ticketops_backend.egg-info'}
with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED) as z:
    for path in ROOT.rglob('*'):
        relative=path.relative_to(ROOT)
        if any(p in EXCLUDE for p in relative.parts) or not path.is_file():continue
        if path.name=='.env' or path.suffix in ('.db','.pyc') or path.name.endswith(('.db-shm','.db-wal','.tsbuildinfo')):continue
        if 'checkpoints' in relative.parts:continue
        z.write(path,Path('ticketops')/relative)
print(OUTPUT)
