import os
os.environ['TICKETOPS_DATABASE_URL']='sqlite:///./work/test-ticketops.db'
os.environ['TICKETOPS_LLM_ENABLED']='false'
import pytest
from fastapi.testclient import TestClient
from ticketops.main import app
from ticketops.db import Base,engine

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        session=c.post('/api/v1/demo-sessions').json()
        c.headers['X-CSRF-Token']=session['csrf_token']
        yield c

def create(client, message='Saldo terpotong tetapi pesanan saya gagal diproses.',order='DEMO-1002'):
    return client.post('/api/v1/tickets',json={'subject':'Keluhan pembayaran pelanggan','message':message,'order_code':order}).json()
