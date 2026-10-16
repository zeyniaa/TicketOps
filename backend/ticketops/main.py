import json, secrets, uuid
from pathlib import Path
from datetime import timezone
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, update, text
from sqlalchemy.orm import Session as DBSession
from .config import settings, ROOT
from .db import Base, engine, get_db, Session, utcnow
from .models import Workspace,Ticket,Analysis,Draft,Policy,Order,Feedback,Job,AuditEvent,EvaluationRun
from .schemas import CreateTicket,UpdateTicket,UpdateDraft,ApproveDraft
from .seed import seed_policies,seed_workspace,TEAMS
from .inference import manifest

@asynccontextmanager
async def lifespan(app):
    # Alembic is used for deployment; create_all also permits an empty local quickstart.
    Base.metadata.create_all(engine)
    with Session() as db:
        seed_policies(db)
        for file in (ROOT/'ml/artifacts').glob('evaluation-*.json'):
            data=json.loads(file.read_text('utf-8'))
            row=db.get(EvaluationRun,data['id'])
            if row: row.result=data
            else: db.add(EvaluationRun(id=data['id'],result=data))
        db.commit()
    yield

app=FastAPI(title='TicketOps API',version='0.1.0',lifespan=lifespan)
origins=settings.allowed_origins.split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['GET','POST','PATCH'],allow_headers=['Content-Type','X-CSRF-Token','Idempotency-Key'])

@app.middleware('http')
async def request_guard(request,call_next):
    request.state.request_id=uuid.uuid4().hex
    origin=request.headers.get('origin')
    if request.method in ('POST','PATCH','DELETE') and origin and origin not in origins:
        return JSONResponse(status_code=403,content={'code':'ORIGIN_FORBIDDEN','message':'Origin tidak diizinkan.','request_id':request.state.request_id,'retryable':False})
    response=await call_next(request)
    response.headers['X-Request-ID']=request.state.request_id
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(HTTPException)
async def http_error(request,exc):
    detail=exc.detail if isinstance(exc.detail,dict) else {'code':'REQUEST_ERROR','message':str(exc.detail)}
    return JSONResponse(status_code=exc.status_code,content={**detail,'request_id':getattr(request.state,'request_id',''),'retryable':exc.status_code in (429,503)})

@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    return JSONResponse(status_code=422,content={'code':'INVALID_INPUT','message':'Periksa isian formulir. Judul minimal 3 karakter, pesan 10–4.000 karakter.','request_id':request.state.request_id,'retryable':False})

def fail(status,code,message): raise HTTPException(status,detail={'code':code,'message':message})

def workspace(request:Request,db:DBSession=Depends(get_db)):
    row=db.get(Workspace,request.cookies.get('ticketops_session',''))
    if not row: fail(401,'SESSION_REQUIRED','Mulai sesi demo terlebih dahulu.')
    if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('x-csrf-token',''),row.csrf): fail(403,'CSRF_INVALID','Sesi formulir tidak valid. Muat ulang halaman.')
    return row

def owned(db,kind,id,ws):
    row=db.get(kind,id)
    owner=row.workspace_id if row and hasattr(row,'workspace_id') else None
    if isinstance(row,Draft):
        parent=db.get(Ticket,row.ticket_id); owner=parent.workspace_id if parent else None
    if row is None or owner!=ws.id: fail(404,'NOT_FOUND','Data tidak ditemukan.')
    return row

def iso(dt): return dt.replace(tzinfo=timezone.utc).isoformat() if dt and dt.tzinfo is None else dt.isoformat() if dt else None

def job_dict(j): return {'id':j.id,'ticket_id':j.ticket_id,'revision':j.revision,'status':j.status,'stage':j.stage,'attempts':j.attempts,'error':j.error,'created_at':iso(j.created_at)}

def draft_dict(d):
    return {'id':d.id,'ticket_id':d.ticket_id,'revision':d.revision,'body':d.body,'source':d.source,'policy_refs':d.policy_refs,'missing_information':d.missing_information,'review_flags':d.review_flags,'status':d.status,'version':d.version,'model_version':d.model_version,'created_at':iso(d.created_at)}

def ticket_dict(db,t,detail=False):
    a=db.scalar(select(Analysis).where(Analysis.ticket_id==t.id).order_by(Analysis.created_at.desc()).limit(1))
    j=db.scalar(select(Job).where(Job.ticket_id==t.id).order_by(Job.created_at.desc()).limit(1))
    result={'id':t.id,'number':t.number,'subject':t.subject,'message':t.message,'customer':t.customer,'order_code':t.order_code,'status':t.status,'category':t.category,'team':t.team,'priority':t.priority,'revision':t.revision,'created_at':iso(t.created_at),'updated_at':iso(t.updated_at),'resolved_at':iso(t.resolved_at),'analysis':a.result if a else None,'analysis_revision':a.revision if a else None,'job':job_dict(j) if j else None}
    if detail:
        result['drafts']=[draft_dict(d) for d in db.scalars(select(Draft).where(Draft.ticket_id==t.id).order_by(Draft.created_at.desc()))]
        result['events']=[{'id':e.id,'action':e.action,'detail':e.detail,'created_at':iso(e.created_at)} for e in db.scalars(select(AuditEvent).where(AuditEvent.ticket_id==t.id).order_by(AuditEvent.created_at.desc()))]
        o=db.scalar(select(Order).where(Order.workspace_id==t.workspace_id,Order.code==t.order_code)) if t.order_code else None
        result['order']=o.facts if o else None
    return result

def enqueue(db,t,kind):
    active=db.scalar(select(Job).where(Job.ticket_id==t.id,Job.revision==t.revision,Job.status.in_(['queued','running'])))
    if active: return active
    count=db.scalar(select(func.count()).select_from(Job).where(Job.workspace_id==t.workspace_id,Job.status.in_(['queued','running'])))
    if count>=5: fail(429,'QUEUE_FULL','Maksimal lima pekerjaan aktif per sesi. Tunggu pekerjaan selesai.')
    job=Job(workspace_id=t.workspace_id,ticket_id=t.id,revision=t.revision,kind=kind)
    db.add(job); db.flush(); return job

@app.post('/api/v1/demo-sessions')
def create_session(request:Request,response:Response,db:DBSession=Depends(get_db)):
    existing=db.get(Workspace,request.cookies.get('ticketops_session',''))
    if existing: return {'csrf_token':existing.csrf,'workspace_id':existing.id}
    ws=Workspace(); db.add(ws); db.flush(); seed_workspace(db,ws.id)
    response.set_cookie('ticketops_session',ws.id,httponly=True,samesite='lax',secure=settings.secure_cookies,max_age=86400)
    return {'csrf_token':ws.csrf,'workspace_id':ws.id}

@app.get('/api/v1/tickets')
def tickets(q:str=Query('',max_length=200),status:str='',category:str='',priority:str='',team:str='',page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),ws=Depends(workspace),db:DBSession=Depends(get_db)):
    stmt=select(Ticket).where(Ticket.workspace_id==ws.id)
    if q: stmt=stmt.where(Ticket.subject.icontains(q)|Ticket.message.icontains(q)|Ticket.customer.icontains(q)|Ticket.order_code.icontains(q))
    for field,value in [('status',status),('category',category),('priority',priority),('team',team)]:
        if value: stmt=stmt.where(getattr(Ticket,field)==value)
    total=db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows=db.scalars(stmt.order_by(Ticket.priority,Ticket.created_at).offset((page-1)*limit).limit(limit))
    return {'items':[ticket_dict(db,t) for t in rows],'total':total,'page':page,'limit':limit}

@app.post('/api/v1/tickets',status_code=202)
def create_ticket(data:CreateTicket,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    db.get(Workspace,ws.id,with_for_update=True)
    count=db.scalar(select(func.count()).select_from(Ticket).where(Ticket.workspace_id==ws.id))
    if count>=20: fail(429,'TICKET_LIMIT','Demo dibatasi 20 tiket per sesi.')
    number=(db.scalar(select(func.max(Ticket.number)).where(Ticket.workspace_id==ws.id)) or 1000)+1
    t=Ticket(workspace_id=ws.id,number=number,**data.model_dump()); db.add(t); db.flush()
    job=enqueue(db,t,'analysis'); db.add(AuditEvent(ticket_id=t.id,action='Tiket dibuat',detail={})); db.commit()
    return {'ticket':ticket_dict(db,t,True),'job':job_dict(job)}

@app.get('/api/v1/tickets/{ticket_id}')
def ticket(ticket_id:str,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    return ticket_dict(db,owned(db,Ticket,ticket_id,ws),True)

@app.patch('/api/v1/tickets/{ticket_id}')
def update_ticket(ticket_id:str,data:UpdateTicket,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    t=owned(db,Ticket,ticket_id,ws)
    values=data.model_dump(exclude_none=True,exclude={'revision','reason'})
    if not values: return ticket_dict(db,t,True)
    changes={k:{'before':getattr(t,k),'after':v} for k,v in values.items() if getattr(t,k)!=v}
    if not changes: return ticket_dict(db,t,True)
    if any(k in changes for k in ('category','team','priority')) and data.status in ('disetujui','selesai'):
        fail(409,'DRAFT_REVIEW_REQUIRED','Simpan koreksi terlebih dahulu, lalu buat dan tinjau draf baru sebelum menyelesaikan tiket.')
    if data.status in ('disetujui','selesai'):
        latest=db.scalar(select(Draft).where(Draft.ticket_id==t.id,Draft.revision==t.revision).order_by(Draft.created_at.desc()).limit(1))
        if not latest or latest.status!='approved': fail(409,'APPROVAL_REQUIRED','Setujui draf terbaru sebelum menyelesaikan tiket.')
    is_content=any(k in changes for k in ('category','team','priority'))
    updated={**values,'updated_at':utcnow()}
    if is_content: updated['revision']=t.revision+1; updated['status']='ditinjau'; updated['resolved_at']=None
    if data.status=='selesai': updated['resolved_at']=utcnow()
    elif data.status: updated['resolved_at']=None
    res=db.execute(update(Ticket).where(Ticket.id==t.id,Ticket.revision==data.revision).values(**updated))
    if not res.rowcount: db.rollback(); fail(409,'REVISION_CONFLICT','Tiket berubah di tab lain. Muat ulang sebelum menyimpan.')
    if is_content:
        db.add(Feedback(ticket_id=t.id,changes=changes,reason=data.reason))
        db.execute(update(Draft).where(Draft.ticket_id==t.id).values(status='stale'))
    db.add(AuditEvent(ticket_id=t.id,action='Koreksi operator' if is_content else 'Status diperbarui',detail=changes)); db.commit(); db.refresh(t)
    return ticket_dict(db,t,True)

@app.post('/api/v1/tickets/{ticket_id}/analyses',status_code=202)
@app.post('/api/v1/tickets/{ticket_id}/drafts',status_code=202)
def analyze(ticket_id:str,request:Request,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    t=owned(db,Ticket,ticket_id,ws)
    active=db.scalar(select(Job).where(Job.ticket_id==t.id,Job.revision==t.revision,Job.status.in_(['queued','running'])))
    if active: return job_dict(active)
    t.revision+=1; t.status='ditinjau'; t.resolved_at=None; t.updated_at=utcnow()
    db.execute(update(Draft).where(Draft.ticket_id==t.id).values(status='stale'))
    job=enqueue(db,t,'draft' if request.url.path.endswith('drafts') else 'analysis'); db.commit(); return job_dict(job)

@app.patch('/api/v1/drafts/{draft_id}')
def edit_draft(draft_id:str,data:UpdateDraft,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    d=owned(db,Draft,draft_id,ws); t=db.get(Ticket,d.ticket_id,with_for_update=True)
    latest=db.scalar(select(Draft.id).where(Draft.ticket_id==t.id).order_by(Draft.created_at.desc()).limit(1))
    if d.revision!=t.revision or latest!=d.id: fail(409,'DRAFT_STALE','Buat ulang draf untuk revisi tiket terbaru.')
    res=db.execute(update(Draft).where(Draft.id==d.id,Draft.version==data.version).values(body=data.body,status='draft',version=Draft.version+1))
    if not res.rowcount: db.rollback(); fail(409,'VERSION_CONFLICT','Draf berubah di tab lain. Muat ulang.')
    t.status='ditinjau'; t.resolved_at=None
    db.add(AuditEvent(ticket_id=t.id,action='Draf diedit operator',detail={})); db.commit(); db.refresh(d); return draft_dict(d)

@app.post('/api/v1/drafts/{draft_id}/approve')
def approve(draft_id:str,data:ApproveDraft,ws=Depends(workspace),db:DBSession=Depends(get_db)):
    d=owned(db,Draft,draft_id,ws); t=db.get(Ticket,d.ticket_id,with_for_update=True)
    latest=db.scalar(select(Draft.id).where(Draft.ticket_id==t.id).order_by(Draft.created_at.desc()).limit(1))
    active=db.scalar(select(Job.id).where(Job.ticket_id==t.id,Job.status.in_(['queued','running'])))
    if d.revision!=t.revision or d.status=='stale' or latest!=d.id or active: fail(409,'DRAFT_STALE','Draf belum sesuai revisi terbaru atau analisis masih berjalan.')
    res=db.execute(update(Draft).where(Draft.id==d.id,Draft.version==data.version).values(status='approved',version=Draft.version+1))
    if not res.rowcount: db.rollback(); fail(409,'VERSION_CONFLICT','Draf berubah. Muat ulang sebelum menyetujui.')
    t.status='disetujui'; db.add(AuditEvent(ticket_id=t.id,action='Draf disetujui dalam aplikasi',detail={'draft_id':d.id})); db.commit(); db.refresh(d); return draft_dict(d)

@app.get('/api/v1/jobs/{job_id}')
def job(job_id:str,ws=Depends(workspace),db:DBSession=Depends(get_db)): return job_dict(owned(db,Job,job_id,ws))

@app.get('/api/v1/policies')
def policies(db:DBSession=Depends(get_db)):
    return [{'id':p.id,'title':p.title,'body':p.body,'category':p.category,'version':p.version} for p in db.scalars(select(Policy).order_by(Policy.id))]

@app.get('/api/v1/overview')
def overview(ws=Depends(workspace),db:DBSession=Depends(get_db)):
    rows=list(db.scalars(select(Ticket).where(Ticket.workspace_id==ws.id)))
    ids=[t.id for t in rows]; corrections=db.scalar(select(func.count()).select_from(Feedback).where(Feedback.ticket_id.in_(ids))) or 0
    return {'total':len(rows),'new':sum(t.status=='baru' for t in rows),'review':sum(t.status=='ditinjau' for t in rows),'resolved':sum(t.status=='selesai' for t in rows),'approved':sum(t.status=='disetujui' for t in rows),'corrections':corrections,'categories':{k:sum(t.category==k for t in rows) for k in TEAMS},'daily':[{'date':day,'count':sum(iso(t.created_at)[:10]==day for t in rows)} for day in sorted({iso(t.created_at)[:10] for t in rows})]}

@app.get('/api/v1/evaluations')
def evaluations(db:DBSession=Depends(get_db)): return [e.result for e in db.scalars(select(EvaluationRun))]

@app.get('/api/v1/evaluations/{evaluation_id}')
def evaluation(evaluation_id:str,db:DBSession=Depends(get_db)):
    e=db.get(EvaluationRun,evaluation_id)
    if not e: fail(404,'NOT_FOUND','Eksperimen belum tersedia.')
    return e.result

@app.get('/api/v1/health')
def health(db:DBSession=Depends(get_db)):
    db.execute(text('SELECT 1')); return {'status':'ok','database':engine.dialect.name}

@app.get('/api/v1/readiness')
async def readiness(db:DBSession=Depends(get_db)):
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r=await client.get(settings.ollama_url+'/api/tags'); r.raise_for_status()
            names=[m['name'] for m in r.json().get('models',[])]
            llm=settings.llm_enabled and settings.ollama_model in names
    except (httpx.HTTPError,ValueError,KeyError): llm=False
    running=db.scalar(select(func.count()).select_from(Job).where(Job.status.in_(['queued','running'])))
    m=manifest()
    return {'api':'ready','database':engine.dialect.name,'classifier':m,'ollama':llm,'llm_model':settings.ollama_model,'queue':running,'mode':'local_inference','version':'0.1.0'}

if (ROOT/'dist').exists():
    app.mount('/',StaticFiles(directory=ROOT/'dist',html=True),name='frontend')
