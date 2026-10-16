"""Export a fresh, isolated seeded workspace, never arbitrary user sessions."""
import json
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
with httpx.Client(base_url='http://127.0.0.1:8018/api/v1',timeout=30) as c:
    c.post('/demo-sessions').raise_for_status()
    rows=c.get('/tickets').json()['items']
    snapshot={'tickets':[c.get('/tickets/'+t['id']).json() for t in rows],'policies':c.get('/policies').json(),'evaluations':c.get('/evaluations').json()}
    for t in snapshot['tickets']:
        assert t['analysis']['source']=='stored_example'
    (ROOT/'frontend/src/snapshot.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False),'utf-8')
print('Exported curated scenario workspace and measured evaluation reports.')
