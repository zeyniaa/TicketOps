"""Evaluate only supplied annotations. Never manufacture human evaluation results.

Input JSONL: {text, category, expected_policy_ids: ["POL-RUSAK-01"], reviewed_by_human: true}
"""
import argparse,json
from pathlib import Path
from ticketops.seed import POLICY_SEED
from ticketops.models import Policy
from ticketops.inference import retrieve

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('annotations',type=Path);p.add_argument('--allow-synthetic',action='store_true');args=p.parse_args()
    rows=[json.loads(l) for l in args.annotations.read_text('utf-8').splitlines()]
    if not rows: raise SystemExit('No annotations provided.')
    if not args.allow_synthetic and any(not r.get('reviewed_by_human') for r in rows): raise SystemExit('Human-reviewed annotations required. Use --allow-synthetic only for a labeled synthetic smoke test.')
    policies=[Policy(id='POL-'+k,category=c,title=t,body=b,version=1) for k,c,t,b in POLICY_SEED]
    values=[]
    for r in rows:
        expected=set(r['expected_policy_ids'])
        if not expected or not expected.issubset({p.id for p in policies}):raise SystemExit('Invalid expected policy IDs.')
        found={p.id for p in retrieve(policies,r['text'],r['category'],3)}
        values.append(len(expected&found)/len(expected))
    print(json.dumps({'count':len(rows),'recall_at_3':sum(values)/len(values),'all_human_reviewed':all(r.get('reviewed_by_human') for r in rows)}))
