"""Evaluate a frozen candidate on held-out test. Run after candidate selection."""
import argparse,json,time
from pathlib import Path
import torch,numpy as np
from transformers import AutoTokenizer,AutoModelForSequenceClassification
from train_baseline import evaluate,read,ROOT

class Predictor:
    def __init__(self,path):
        self.selection=json.loads((path/'selection.json').read_text('utf-8'));self.classes_=np.array(self.selection['labels'])
        self.tokenizer=AutoTokenizer.from_pretrained(path/'model',local_files_only=True)
        self.model=AutoModelForSequenceClassification.from_pretrained(path/'model',local_files_only=True).eval()
        torch.set_num_threads(2)
    def predict_proba(self,texts):
        result=[]
        with torch.inference_mode():
            for i in range(0,len(texts),16):
                logits=self.model(**self.tokenizer(texts[i:i+16],padding=True,truncation=True,max_length=256,return_tensors='pt')).logits
                result.extend(torch.softmax(logits/self.selection['temperature'],dim=-1).numpy())
        return np.array(result)
    def predict(self,texts):return self.classes_[self.predict_proba(texts).argmax(axis=1)]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);args=p.parse_args();m=Predictor(args.candidate)
    r=evaluate(m,read('test'),'indobert-frozen-seed'+str(m.selection['seed']),['Candidate selected on development before this test run.','All data are synthetic and not human reviewed.','CPU inference benchmark; model promotion is a separate local command.'])
    r['model']='IndoBERT · seed '+str(m.selection['seed']);r['temperature']=m.selection['temperature']
    output=ROOT/'artifacts'/('evaluation-'+r['id']+'.json');output.write_text(json.dumps(r,indent=2,ensure_ascii=False),'utf-8');print(output)
