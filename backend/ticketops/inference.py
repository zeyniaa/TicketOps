import json, re, time
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
from rank_bm25 import BM25Okapi
from .config import settings, ROOT
from .seed import TEAMS

def tokenize(text): return re.findall(r'\w+', text.lower())

@lru_cache(maxsize=2)
def load_bundle(path):
    if not Path(path).exists(): return None
    return joblib.load(path)

@lru_cache(maxsize=2)
def load_transformer(path):
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(2)
    return AutoTokenizer.from_pretrained(path, local_files_only=True), AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).eval()

def manifest():
    p=Path(settings.manifest_path)
    return json.loads(p.read_text('utf-8')) if p.exists() else {'version':'unavailable','type':'unavailable','review_required':True}

def classify(text):
    start=time.perf_counter(); m=manifest()
    if m.get('type')=='indobert':
        import torch
        path=Path(m['model_path'])
        tok, model=load_transformer(str(path if path.is_absolute() else ROOT/path))
        with torch.inference_mode(): logits=model(**tok(text,return_tensors='pt',truncation=True,max_length=256)).logits[0]/m.get('temperature',1)
        probs=torch.softmax(logits,dim=-1).numpy(); labels=np.array(m['labels'])
    else:
        bundle=load_bundle(settings.model_path)
        if bundle is None: raise RuntimeError('CLASSIFIER_NOT_READY')
        model=bundle['model']; probs=model.predict_proba([text])[0]; labels=model.classes_
    ranking=np.argsort(probs)[::-1]; best=int(ranking[0]); score=float(probs[best]); category=str(labels[best])
    margin=score-float(probs[ranking[1]])
    review=bool(m.get('review_required',True) or category=='lainnya' or score<m.get('threshold',.8) or margin<m.get('margin',.15))
    return {'category':category,'score':round(score,4),'calibration':m.get('calibration','uncalibrated'),'needs_review':review,'classifier_version':m['version'],'source':'inference','suggested_team':TEAMS[category],'top_classes':[{'category':str(labels[i]),'score':round(float(probs[i]),4)} for i in ranking[:3]],'latency_ms':round((time.perf_counter()-start)*1000)}

def routing(category, facts=None):
    facts=facts or {}
    if facts.get('payment_status')=='charged' and facts.get('status')=='failed':
        return 'billing','P1','Data pesanan simulasi menunjukkan dana terpotong dan pesanan gagal.'
    if facts.get('overdue_hours',0)>48:
        return 'logistik','P1','Data pesanan simulasi melewati estimasi lebih dari 48 jam.'
    if category in ('barang_rusak','barang_tidak_sesuai','retur_refund'):
        return TEAMS[category],'P2','Keluhan barang atau retur memerlukan pemeriksaan tim retur.'
    return TEAMS[category],'P3','Belum ada kondisi eskalasi terverifikasi pada data pesanan.'

def retrieve(policies, text, category, limit=3):
    if not policies: return []
    corpus=[tokenize(p.title+' '+p.body) for p in policies]
    scores=BM25Okapi(corpus).get_scores(tokenize(text))
    scores=np.array([float(s)+(4 if p.category==category else 0) for p,s in zip(policies,scores)])
    return [policies[int(i)] for i in np.argsort(scores)[::-1][:limit]]
