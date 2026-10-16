"""Exercise real classifier + Ollama through the HTTP API. Stores only synthetic input."""
import json,time,argparse
from pathlib import Path
import httpx

def run(base):
    start=time.perf_counter()
    with httpx.Client(base_url=base,timeout=15) as c:
        c.headers['X-CSRF-Token']=c.post('/demo-sessions').json()['csrf_token']
        r=c.post('/tickets',json={'subject':'Gelas diterima pecah','message':'Halo, dua gelas dalam pesanan saya datang pecah. Kardusnya penyok. Saya ingin mengajukan retur dan punya foto kerusakannya.','order_code':'DEMO-1001','customer':'Pelanggan uji sintetis'})
        r.raise_for_status();data=r.json();print(json.dumps({'ticket_id':data['ticket']['id'],'status':'queued'}),flush=True)
        job_id=data['job']['id']
        for _ in range(420):
            job=c.get('/jobs/'+job_id).json()
            if job['status'] not in ('queued','running'): break
            time.sleep(1)
        t=c.get('/tickets/'+data['ticket']['id']).json()
        if job['status']!='succeeded': raise RuntimeError(str(job))
        d=t['drafts'][0]
        result={'ticket_id':t['id'],'job':job,'analysis':t['analysis'],'draft':d,'elapsed_seconds':round(time.perf_counter()-start,2),'real_llm':d['source']=='ollama','synthetic_input':True}
        out=Path(__file__).resolve().parents[1]/'docs/local-smoke.json';out.write_text(json.dumps(result,indent=2,ensure_ascii=False),'utf-8')
        c.post('/drafts/'+d['id']+'/approve',json={'version':d['version']}).raise_for_status()
        c.patch('/tickets/'+t['id'],json={'revision':t['revision'],'status':'selesai'}).raise_for_status()
        print(json.dumps({'status':'passed','real_llm':result['real_llm'],'elapsed_seconds':result['elapsed_seconds']}),flush=True)
        if not result['real_llm']: raise RuntimeError('End-to-end workflow passed but live Ollama generation fell back to a template. See docs/local-smoke.json.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8018/api/v1');run(p.parse_args().base)
