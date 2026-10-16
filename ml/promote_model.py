"""Local-only promotion gate: development improvement AND measured laptop CPU latency."""
import argparse,json,time
from pathlib import Path
import numpy as np
from evaluate_indobert import Predictor
from train_baseline import ROOT,read

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);args=p.parse_args()
    baseline=json.loads((ROOT/'artifacts/manifest.json').read_text('utf-8'))
    if baseline['type']!='tfidf': raise SystemExit('Restore baseline manifest before comparing a new promotion.')
    m=Predictor(args.candidate);m.predict(['Paket belum tiba'])
    durations=[]
    for r in read('dev')[:40]:
        start=time.perf_counter();m.predict([r['text']]);durations.append((time.perf_counter()-start)*1000)
    p95=float(np.percentile(durations,95));gain=m.selection['development_macro_f1']-baseline['development_macro_f1']
    if gain<.02 or p95>3000: raise SystemExit(f'Candidate not promoted: development gain={gain:.4f}; CPU p95={p95:.1f}ms. Baseline preserved.')
    model_path=(args.candidate/'model').resolve().relative_to(ROOT.parent).as_posix()
    manifest={'type':'indobert','version':'indobert-bootstrap-v1','model_path':model_path,'labels':m.selection['labels'],'temperature':m.selection['temperature'],'calibration':'temperature_scaled','threshold':.95,'margin':.3,'review_required':True,'development_macro_f1':m.selection['development_macro_f1'],'cpu_p95_ms':p95,'dataset_version':m.selection['dataset_version']}
    (ROOT/'artifacts/manifest-baseline.json').write_text(json.dumps(baseline,indent=2),'utf-8')
    (ROOT/'artifacts/manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8');print('Promoted. Restart API and worker to load the new manifest.')
