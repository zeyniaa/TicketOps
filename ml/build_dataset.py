import json, hashlib, random
from pathlib import Path
from seed_data import SCENARIOS

ROOT=Path(__file__).resolve().parent

def build(output=ROOT/'data/generated'):
    output.mkdir(parents=True,exist_ok=True)
    # Family grouping happens before augmentation. Wrapper changes cannot create independent test families.
    prefixes=['','Halo kak, ','Mohon bantu, ','Permisi, ','Kak, ']
    suffixes=['',' ya.',' mohon dicek.',' tolong bantu saya.',' Terima kasih.']
    counts={'train':20,'dev':5,'calibration':5,'test':5}
    summary={}
    for split,n in counts.items():
        rows=[]
        for category,groups in SCENARIOS.items():
            for index,scenario in enumerate(groups[split]):
                family=f'{category}:{split}:{index}'
                variants=[(p,s) for p in prefixes for s in suffixes]
                random.Random(family).shuffle(variants)
                for j,(prefix,suffix) in enumerate(variants[:n]):
                    text=prefix+scenario+suffix
                    rows.append({'id':hashlib.sha256(text.encode()).hexdigest()[:16],'text':text,'label':category,'family_id':family,'split':split,'source':'agent_authored_synthetic','reviewed_by_human':False})
        random.Random(42).shuffle(rows)
        (output/f'{split}.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n','utf-8')
        summary[split]={'rows':len(rows),'families':len({r['family_id'] for r in rows})}
    (output/'metadata.json').write_text(json.dumps({'version':'ticketops-synthetic-bootstrap-v1','synthetic':True,'reviewed_by_human':False,'splits':summary,'limitations':['Surface variants within a family are correlated.','No natural customer data.','Labels and scenarios authored by an AI coding agent.','Human review and independently collected test data are required before production claims.']},indent=2),'utf-8')
    print(json.dumps(summary))

if __name__=='__main__': build()
