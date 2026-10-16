import argparse, json, time, platform, subprocess
from datetime import datetime, timezone
from pathlib import Path
import joblib, numpy as np
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import f1_score,accuracy_score,classification_report,confusion_matrix,log_loss
from sklearn.model_selection import GroupKFold

ROOT=Path(__file__).resolve().parent
def read(split): return [json.loads(l) for l in (ROOT/f'data/generated/{split}.jsonl').read_text('utf-8').splitlines()]
def fields(rows): return [r['text'] for r in rows],[r['label'] for r in rows]

def check_splits(splits):
    seen_text=set();seen_family=set()
    for name,rows in splits.items():
        texts={r['text'].lower().strip() for r in rows}; families={r['family_id'] for r in rows}
        if seen_text&texts or seen_family&families: raise ValueError('Cross-split leakage: '+name)
        seen_text|=texts;seen_family|=families

def model(c,word=True,char=True):
    features=[]
    if word: features.append(('word',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=20000)))
    if char: features.append(('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,max_features=30000)))
    return Pipeline([('features',FeatureUnion(features)),('classifier',LogisticRegression(C=c,max_iter=1500,random_state=42))])

def evaluate(m,rows,name,notes):
    x,y=fields(rows); m.predict([x[0]])
    durations=[]
    for text in x:
        start=time.perf_counter();m.predict([text]);durations.append((time.perf_counter()-start)*1000)
    pred=m.predict(x); labels=list(m.classes_)
    return {'id':name,'model':'TF-IDF word + char · sigmoid' if 'calibrated' in name else 'TF-IDF word + char · baseline','dataset_version':'ticketops-synthetic-bootstrap-v1','synthetic':True,'reviewed_by_human':False,'test_count':len(rows),'test_family_count':len({r['family_id'] for r in rows}),'macro_f1':f1_score(y,pred,average='macro'),'accuracy':accuracy_score(y,pred),'latency_p50_ms':float(np.percentile(durations,50)),'latency_p95_ms':float(np.percentile(durations,95)),'labels':labels,'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),'per_class':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),'errors':[{'text':a,'expected':b,'predicted':str(c)} for a,b,c in zip(x,y,pred) if b!=c][:20],'created_at':datetime.now(timezone.utc).isoformat(),'notes':notes,'host':platform.platform()}

def train():
    from build_dataset import build
    if not (ROOT/'data/generated/train.jsonl').exists(): build()
    splits={s:read(s) for s in ['train','dev','calibration','test']};check_splits(splits)
    x,y=fields(splits['train']);dx,dy=fields(splits['dev']);cx,cy=fields(splits['calibration'])
    candidates=[]
    for c in [.5,1,2]:
        m=model(c);m.fit(x,y);candidates.append((f1_score(dy,m.predict(dx),average='macro'),c,m))
    score,c,best=max(candidates,key=lambda x:x[0])
    calibrated=CalibratedClassifierCV(FrozenEstimator(best),method='sigmoid');calibrated.fit(cx,cy)
    probs=calibrated.predict_proba(dx);ranking=np.sort(probs,axis=1);pred=calibrated.classes_[probs.argmax(axis=1)]
    choice=None
    for threshold in np.arange(.7,.951,.05):
        for margin in np.arange(.1,.301,.05):
            mask=(ranking[:,-1]>=threshold)&((ranking[:,-1]-ranking[:,-2])>=margin)&(pred!='lainnya')
            if mask.sum()>=10:
                precision=float(np.mean(pred[mask]==np.array(dy)[mask]));coverage=float(mask.mean())
                if precision>=.9 and (not choice or coverage>choice['coverage']): choice={'threshold':round(float(threshold),2),'margin':round(float(margin),2),'precision':precision,'coverage':coverage}
    output=ROOT/'artifacts';output.mkdir(exist_ok=True)
    joblib.dump({'model':calibrated,'version':'tfidf-bootstrap-v1'},output/'baseline.joblib')
    calibration={'log_loss_before':log_loss(cy,best.predict_proba(cx)),'log_loss_after':log_loss(cy,calibrated.predict_proba(cx))}
    manifest={'version':'tfidf-bootstrap-v1','type':'tfidf','calibration':'sigmoid','dataset_version':'ticketops-synthetic-bootstrap-v1','review_required':True,'threshold':choice['threshold'] if choice else .95,'margin':choice['margin'] if choice else .3,'development_selection':choice,'C':c,'development_macro_f1':score,'calibration_metrics':calibration,'reason':'Bootstrap data is AI-authored, synthetic and not human reviewed; every category requires operator review.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
    notes=['Semua contoh dibuat secara sintetis oleh coding agent dan belum ditinjau manusia.','Split dipisahkan berdasarkan keluarga skenario sebelum augmentasi. Variasi dalam satu keluarga saling berkorelasi.','Test memuat 64 keluarga skenario independen; 320 baris bukan 320 skenario independen.','Hyperparameter dipilih di development; kalibrasi memakai split terpisah. Test hanya digunakan setelah konfigurasi dipilih.','IndoBERT dan pembanding Qwen belum dimasukkan sebelum training atau benchmark benar-benar dijalankan.']
    for name,m in [('tfidf-bootstrap-v1',best),('tfidf-calibrated-v1',calibrated)]:
        report=evaluate(m,splits['test'],name,notes)
        (output/f'evaluation-{name}.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),'utf-8')
    print(json.dumps({'status':'trained','C':c,'development_macro_f1':score,'review_required':True,'calibration':calibration}))

if __name__=='__main__': train()
