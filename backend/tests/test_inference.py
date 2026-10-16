import pytest
from ticketops.inference import classify,routing,retrieve
from ticketops.drafting import validated_output
from ticketops.models import Policy

def test_verified_priority():
    assert routing('pembayaran',{'payment_status':'charged','status':'failed'})[1]=='P1'
    assert routing('pembayaran',{})[1]=='P3'
    assert routing('status_pengiriman',{'overdue_hours':72})[1]=='P1'
    assert routing('barang_rusak')[1]=='P2'

def test_bootstrap_always_reviewed():
    result=classify('Saya tidak bisa login karena lupa kata sandi akun toko')
    assert result['source']=='inference';assert result['needs_review'] is True
    assert 0<=result['score']<=1

def test_unknown_source_and_unsafe_action_rejected():
    p=Policy(id='POL-RETUR-01',version=1,category='retur_refund',title='Retur',body='Operator memeriksa pengajuan.')
    body='Terima kasih telah menghubungi kami. Kami memahami Anda ingin memeriksa pengajuan retur untuk pesanan tersebut. Mohon informasikan nomor pesanan dan alasan pengajuan agar operator dapat memeriksa informasi yang relevan. Tim kami perlu meninjau kelengkapan informasi terlebih dahulu sebelum menyampaikan langkah penanganan berikutnya.'
    with pytest.raises(ValueError,match='UNKNOWN_POLICY'): validated_output({'draft':body,'policy_ids':['MADE-UP:v1']},[p])
    with pytest.raises(ValueError,match='UNSUPPORTED_ACTION'): validated_output({'draft':body+' Pengembalian dana sudah diproses ke rekening Anda.','policy_ids':['POL-RETUR-01:v1']},[p])
    valid=validated_output({'draft':body,'policy_ids':['POL-RETUR-01:v1']},[p])
    assert valid['source']=='ollama'

def test_short_instruction_echo_rejected():
    p=Policy(id='POL-RETUR-01',version=1,category='retur_refund',title='Retur',body='Operator memeriksa pengajuan.')
    with pytest.raises(ValueError): validated_output({'draft':'Sopan, 60-120 kata, bukan menyalin kebijakan','policy_ids':['POL-RETUR-01:v1']},[p])

def test_retrieval_category_boost():
    rows=[Policy(id='a',category='akun',title='Login akun',body='Lupa sandi login'),Policy(id='b',category='retur_refund',title='Retur dana',body='Pengajuan pengembalian dana')]
    assert retrieve(rows,'ingin pengembalian','retur_refund',1)[0].id=='b'
