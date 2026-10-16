"""Single AI worker. PostgreSQL uses SKIP LOCKED; SQLite claims with compare-and-swap."""
import logging, time
from datetime import timedelta
from sqlalchemy import select, update
from .db import Session, utcnow, engine
from .models import Job, Ticket, Analysis, Draft, Policy, Order, AuditEvent, Feedback
from .inference import classify, retrieve, routing
from .drafting import make_draft
from .config import settings

log=logging.getLogger('ticketops.worker')

def claim_job():
    with Session() as db:
        stale=utcnow()-timedelta(seconds=settings.worker_lease_seconds)
        db.execute(update(Job).where(Job.status=='running',Job.claimed_at<stale,Job.attempts<3).values(status='queued',stage='Menunggu percobaan ulang'))
        db.execute(update(Job).where(Job.status=='running',Job.claimed_at<stale,Job.attempts>=3).values(status='failed',error='WORKER_INTERRUPTED',stage='Gagal',finished_at=utcnow()))
        stmt=select(Job).where(Job.status=='queued').order_by(Job.created_at).limit(1)
        if engine.dialect.name=='postgresql': stmt=stmt.with_for_update(skip_locked=True)
        job=db.scalar(stmt)
        if not job: db.commit(); return None
        result=db.execute(update(Job).where(Job.id==job.id,Job.status=='queued').values(status='running',stage='Mengelompokkan',claimed_at=utcnow(),attempts=Job.attempts+1))
        db.commit()
        return job.id if result.rowcount else None

def stage(job_id, name):
    with Session() as db:
        db.execute(update(Job).where(Job.id==job_id,Job.status=='running').values(stage=name)); db.commit()

def process_job(job_id):
    start=time.perf_counter()
    try:
        with Session() as db:
            job=db.get(Job,job_id); t=db.get(Ticket,job.ticket_id)
            if t.revision!=job.revision:
                job.status='superseded'; job.stage='Digantikan revisi baru'; job.finished_at=utcnow(); db.commit(); return
            text=t.subject+'\n'+t.message
            previous=db.scalar(select(Analysis).where(Analysis.ticket_id==t.id).order_by(Analysis.created_at.desc()).limit(1))
            result=classify(text) if job.kind=='analysis' or not previous else dict(previous.result)
            corrected=any('category' in f.changes for f in db.scalars(select(Feedback).where(Feedback.ticket_id==t.id)))
            category=t.category if (corrected or job.kind=='draft') and t.category else result['category']
            order=db.scalar(select(Order).where(Order.workspace_id==t.workspace_id,Order.code==t.order_code)) if t.order_code else None
            facts=order.facts if order else None
            team,priority,reason=routing(category,facts)
            result.update(suggested_team=team,suggested_priority=priority,priority_reason=reason)
            policies=retrieve(list(db.scalars(select(Policy))),text,category)
            revision=job.revision
            # Publish classifier result early; generation may be slow on CPU.
            if not db.scalar(select(Analysis).where(Analysis.ticket_id==t.id,Analysis.revision==revision)):
                db.add(Analysis(ticket_id=t.id,revision=revision,result=result,latency_ms=result.get('latency_ms',0)))
            if not corrected and job.kind=='analysis': t.category=category; t.team=team; t.priority=priority
            db.commit()
        stage(job_id,'Membaca kebijakan')
        stage(job_id,'Menyusun draf')
        draft=make_draft(text,category,policies,facts)
        with Session() as db:
            job=db.get(Job,job_id); t=db.get(Ticket,job.ticket_id,with_for_update=True)
            if t.revision!=revision:
                job.status='superseded'; job.stage='Digantikan revisi baru'
            else:
                db.add(Draft(ticket_id=t.id,revision=revision,**draft))
                if t.status=='baru': t.status='ditinjau'
                t.updated_at=utcnow()
                job.status='succeeded'; job.stage='Siap diperiksa'
                db.add(AuditEvent(ticket_id=t.id,action='Analisis selesai',detail={'source':draft['source'],'revision':revision,'elapsed_ms':round((time.perf_counter()-start)*1000)}))
            job.finished_at=utcnow(); db.commit()
    except Exception as exc:
        log.error('job_failed job=%s type=%s',job_id,type(exc).__name__)
        with Session() as db:
            job=db.get(Job,job_id)
            if job: job.status='failed'; job.stage='Gagal'; job.error='CLASSIFIER_NOT_READY' if str(exc)=='CLASSIFIER_NOT_READY' else 'ANALYSIS_FAILED'; job.finished_at=utcnow(); db.commit()

def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        job_id=claim_job()
        if job_id: process_job(job_id)
        else: time.sleep(1)

if __name__=='__main__': main()
