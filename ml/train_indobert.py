"""Colab training; no automatic promotion. Fine-tuning needs the optional training extra.

Usage: python ml/train_indobert.py --learning-rate 2e-5 --seed 42
Repeat candidate 3e-5; select on development, then repeat winner with seeds 17/71.
Test is evaluated by evaluate_indobert.py AFTER selection is frozen.
"""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from datasets import Dataset
from transformers import AutoTokenizer,AutoModelForSequenceClassification,TrainingArguments,Trainer,EarlyStoppingCallback,DataCollatorWithPadding,set_seed
from sklearn.metrics import f1_score,log_loss
from train_baseline import ROOT,read,check_splits

def main(args):
    if not torch.cuda.is_available() and not args.allow_cpu: raise SystemExit('GPU tidak tersedia. Pilih runtime GPU di Colab, atau --allow-cpu untuk eksperimen kecil.')
    set_seed(args.seed)
    splits={s:read(s) for s in ['train','dev','calibration','test']};check_splits(splits)
    labels=sorted({r['label'] for r in splits['train']});label2id={l:i for i,l in enumerate(labels)}
    tokenizer=AutoTokenizer.from_pretrained('indobenchmark/indobert-base-p1',revision=args.revision)
    def dataset(rows):
        d=Dataset.from_list([{'text':r['text'],'labels':label2id[r['label']]} for r in rows])
        return d.map(lambda b:tokenizer(b['text'],truncation=True,max_length=256),batched=True,remove_columns=['text'])
    train=dataset(splits['train']);dev=dataset(splits['dev']);cal=dataset(splits['calibration'])
    model=AutoModelForSequenceClassification.from_pretrained('indobenchmark/indobert-base-p1',revision=args.revision,num_labels=len(labels),id2label=dict(enumerate(labels)),label2id=label2id)
    output=ROOT/'artifacts'/f'indobert-lr{args.learning_rate}-seed{args.seed}'
    training=TrainingArguments(output_dir=str(output/'checkpoints'),learning_rate=args.learning_rate,per_device_train_batch_size=16,per_device_eval_batch_size=16,num_train_epochs=5,weight_decay=.01,eval_strategy='epoch',save_strategy='epoch',save_total_limit=2,load_best_model_at_end=True,metric_for_best_model='macro_f1',greater_is_better=True,fp16=torch.cuda.is_available(),seed=args.seed,report_to='none')
    trainer=Trainer(model=model,args=training,train_dataset=train,eval_dataset=dev,data_collator=DataCollatorWithPadding(tokenizer),processing_class=tokenizer,compute_metrics=lambda p:{'macro_f1':f1_score(p.label_ids,np.argmax(p.predictions,axis=-1),average='macro')},callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
    trainer.train(resume_from_checkpoint=args.resume)
    logits=torch.tensor(trainer.predict(cal).predictions,dtype=torch.float32)
    y=torch.tensor([label2id[r['label']] for r in splits['calibration']])
    logtemp=torch.nn.Parameter(torch.zeros(1));opt=torch.optim.LBFGS([logtemp],lr=.05,max_iter=50)
    def closure():
        opt.zero_grad();loss=torch.nn.functional.cross_entropy(logits/logtemp.exp().clamp(.1,10),y);loss.backward();return loss
    opt.step(closure);temperature=float(logtemp.exp().clamp(.1,10).item())
    development=trainer.evaluate();destination=output/'model';trainer.save_model(str(destination));tokenizer.save_pretrained(str(destination))
    selection={'seed':args.seed,'learning_rate':args.learning_rate,'development_macro_f1':development['eval_macro_f1'],'temperature':temperature,'labels':labels,'base_revision':model.config._commit_hash,'type':'indobert','model_directory':'model','dataset_version':'ticketops-synthetic-bootstrap-v1','human_reviewed':False,'test_evaluated':False}
    (output/'selection.json').write_text(json.dumps(selection,indent=2),'utf-8')
    print(json.dumps(selection))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--learning-rate',type=float,default=2e-5);p.add_argument('--seed',type=int,default=42);p.add_argument('--revision',default='main');p.add_argument('--resume',default=None);p.add_argument('--allow-cpu',action='store_true');main(p.parse_args())
