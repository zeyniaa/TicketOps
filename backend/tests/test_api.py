from fastapi.testclient import TestClient
from ticketops.main import app
from ticketops.worker import claim_job,process_job
from ticketops.db import Session
from ticketops.models import Job,Draft,Ticket
from conftest import create

def complete(client):
    data=create(client); job=claim_job(); assert job==data['job']['id']; process_job(job)
    t=client.get('/api/v1/tickets/'+data['ticket']['id']).json()
    assert t['job']['status']=='succeeded'
    assert t['drafts'][0]['source']=='template'
    return t

def test_seed_search_and_scope(client):
    response=client.get('/api/v1/tickets');assert response.status_code==200;assert response.json()['total']==12
    assert client.get('/api/v1/tickets?q=pecah').json()['total']==1
    tid=response.json()['items'][0]['id']
    with TestClient(app) as second:
        session=second.post('/api/v1/demo-sessions');assert session.status_code==200
        assert second.get('/api/v1/tickets/'+tid).status_code==404

def test_csrf_origin_validation(client):
    assert client.post('/api/v1/tickets',json={'subject':'Tes','message':'Pesan pelanggan contoh'},headers={'X-CSRF-Token':'invalid'}).status_code==403
    assert client.post('/api/v1/demo-sessions',headers={'Origin':'https://untrusted.example'}).status_code==403
    assert client.post('/api/v1/tickets',json={'subject':' ','message':'x'}).status_code==422

def test_end_to_end_approve_resolve(client):
    t=complete(client);assert t['priority']=='P1';assert t['team']=='billing';assert t['analysis']['needs_review'] is True
    d=t['drafts'][0]
    edit=client.patch('/api/v1/drafts/'+d['id'],json={'version':d['version'],'body':d['body']+' Operator akan membantu menindaklanjuti.'})
    assert edit.status_code==200
    assert client.post('/api/v1/drafts/'+d['id']+'/approve',json={'version':d['version']}).status_code==409
    assert client.post('/api/v1/drafts/'+d['id']+'/approve',json={'version':edit.json()['version']}).status_code==200
    resolved=client.patch('/api/v1/tickets/'+t['id'],json={'revision':t['revision'],'status':'selesai'})
    assert resolved.status_code==200;assert resolved.json()['resolved_at']

def test_correction_invalidates_and_preserves_category(client):
    t=complete(client);d=t['drafts'][0]
    update=client.patch('/api/v1/tickets/'+t['id'],json={'revision':t['revision'],'category':'akun','team':'customer_care'})
    assert update.status_code==200; assert update.json()['revision']==t['revision']+1
    assert client.post('/api/v1/drafts/'+d['id']+'/approve',json={'version':d['version']}).status_code==409
    assert client.patch('/api/v1/tickets/'+t['id'],json={'revision':t['revision'],'priority':'P3'}).status_code==409
    job=client.post('/api/v1/tickets/'+t['id']+'/drafts');assert job.status_code==202
    process_job(claim_job()); updated=client.get('/api/v1/tickets/'+t['id']).json()
    assert updated['category']=='akun';assert updated['drafts'][0]['revision']==updated['revision']

def test_duplicate_analysis_and_stale_job(client):
    data=create(client);tid=data['ticket']['id'];first=data['job']['id']
    assert client.post('/api/v1/tickets/'+tid+'/analyses').json()['id']==first
    j=claim_job();assert j==first;assert claim_job() is None
    client.patch('/api/v1/tickets/'+tid,json={'revision':1,'category':'akun'})
    process_job(j)
    assert client.get('/api/v1/jobs/'+j).json()['status']=='superseded'

def test_cannot_resolve_unapproved(client):
    t=complete(client)
    assert client.patch('/api/v1/tickets/'+t['id'],json={'revision':t['revision'],'status':'selesai'}).status_code==409

def test_cannot_combine_correction_and_resolution(client):
    t=complete(client);d=t['drafts'][0]
    assert client.post('/api/v1/drafts/'+d['id']+'/approve',json={'version':d['version']}).status_code==200
    assert client.patch('/api/v1/tickets/'+t['id'],json={'revision':t['revision'],'category':'akun','status':'selesai'}).status_code==409

def test_queue_limit_and_no_partial_ticket(client):
    for _ in range(5): assert client.post('/api/v1/tickets',json={'subject':'Status pengiriman','message':'Paket saya belum tiba sampai sekarang'}).status_code==202
    assert client.post('/api/v1/tickets',json={'subject':'Status pengiriman','message':'Paket saya belum tiba sampai sekarang'}).status_code==429
    assert client.get('/api/v1/tickets').json()['total']==17

def test_evaluations_health_policies(client):
    assert client.get('/api/v1/health').json()['status']=='ok'
    assert len(client.get('/api/v1/policies').json())==24
    for result in client.get('/api/v1/evaluations').json(): assert result['synthetic'] and result['reviewed_by_human'] is False
