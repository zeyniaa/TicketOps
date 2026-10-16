"""Offline comparison of local LLM classification. No claimed metrics before execution."""
import argparse,json,time
from pathlib import Path
import numpy as np,httpx
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from datetime import datetime,timezone
from train_baseline import ROOT,read

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',default='qwen3:4b');p.add_argument('--url',default='http://127.0.0.1:11434');p.add_argument('--per-class',type=int,default=40);args=p.parse_args()
    rows=read('test');labels=sorted({r['label'] for r in rows});sample=[]
    for label in labels:sample.extend([r for r in rows if r['label']==label][:args.per_class])
    predictions=[];durations=[];failures=0
    with httpx.Client(timeout=180) as c:
        for i,r in enumerate(sample):
            start=time.perf_counter()
            try:
                response=c.post(args.url+'/api/chat',json={'model':args.model,'think':False,'stream':False,'messages':[{'role':'system','content':'Klasifikasikan keluhan pelanggan Indonesia ke satu kategori. Pilih kebutuhan utama. Jika tidak jelas gunakan lainnya. Kategori: '+', '.join(labels)},{'role':'user','content':r['text']}],'format':{'type':'object','properties':{'category':{'type':'string','enum':labels}},'required':['category']},'options':{'temperature':0,'num_ctx':2048,'num_predict':64}});response.raise_for_status();pred=json.loads(response.json()['message']['content'])['category']
                if pred not in labels:raise ValueError()
            except (httpx.HTTPError,ValueError,KeyError):pred='ERROR';failures+=1
            predictions.append(pred);durations.append((time.perf_counter()-start)*1000);print(f'{i+1}/{len(sample)}',flush=True)
    actual=[r['label'] for r in sample]
    # Include ERROR column so failures remain visible, rather than dropping them from the matrix.
    matrix_labels=labels+(['ERROR'] if failures else [])
    report={'id':'qwen-classification-v1','model':args.model+' · zero-shot','dataset_version':'ticketops-synthetic-bootstrap-v1','synthetic':True,'reviewed_by_human':False,'test_count':len(sample),'macro_f1':f1_score(actual,predictions,labels=labels,average='macro',zero_division=0),'accuracy':accuracy_score(actual,predictions),'latency_p50_ms':float(np.percentile(durations,50)),'latency_p95_ms':float(np.percentile(durations,95)),'labels':labels,'confusion_matrix':confusion_matrix(actual,predictions,labels=matrix_labels).tolist(),'matrix_labels':matrix_labels,'per_class':classification_report(actual,predictions,labels=labels,output_dict=True,zero_division=0),'errors':[{'text':r['text'],'expected':r['label'],'predicted':pred} for r,pred in zip(sample,predictions) if r['label']!=pred],'failures':failures,'created_at':datetime.now(timezone.utc).isoformat(),'notes':['Zero-shot prompt frozen before test; no finetuning.','Synthetic evaluation only; no human review.','Inference failures counted as incorrect predictions.','Subset run if per-class < 40; compare only runs using the same test IDs.'],'test_ids':[r['id'] for r in sample]}
    (ROOT/'artifacts/evaluation-qwen-classification-v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
