"""Versioned, fictional store policies and demo records. No customer data."""
from datetime import timedelta
from sqlalchemy import select
from .db import utcnow
from .models import Policy, Order, Ticket, Analysis, Draft, AuditEvent

LABELS = {'status_pengiriman':'Status pengiriman','barang_rusak':'Barang rusak','barang_tidak_sesuai':'Barang tidak sesuai','retur_refund':'Retur & refund','pembatalan':'Pembatalan','pembayaran':'Pembayaran','akun':'Akun','lainnya':'Lainnya'}
TEAMS = {'status_pengiriman':'logistik','barang_rusak':'retur','barang_tidak_sesuai':'retur','retur_refund':'retur','pembatalan':'customer_care','pembayaran':'billing','akun':'customer_care','lainnya':'customer_care'}
POLICY_SEED = [
('KIRIM-01','status_pengiriman','Lacak perjalanan pesanan','Periksa nomor pesanan dan status pengiriman sebelum menjawab. Bila nomor pesanan belum tersedia, minta nomor pesanan. Jangan mengarang nomor resi atau posisi paket.'),
('KIRIM-02','status_pengiriman','Keterlambatan pengiriman','Tanggal perkiraan adalah estimasi. Jika data pesanan menunjukkan keterlambatan lebih dari 48 jam dari estimasi, eskalasi ke tim logistik dengan prioritas P1. Jangan menjanjikan tanggal tiba baru tanpa konfirmasi.'),
('KIRIM-03','status_pengiriman','Paket berstatus diterima','Jika pelanggan belum menerima paket meski status diterima, minta konfirmasi penerima dan eskalasi ke logistik. Jangan menyatakan paket hilang sebelum pemeriksaan.'),
('RUSAK-01','barang_rusak','Laporan barang rusak','Minta foto kerusakan, kemasan, dan nomor pesanan. Operator memeriksa bukti sebelum menyetujui retur. Jangan menyatakan pengembalian dana sudah diproses.'),
('RUSAK-02','barang_rusak','Batas pelaporan kerusakan','Dalam kebijakan toko simulasi ini, laporan kerusakan diajukan paling lambat tujuh hari setelah barang diterima. Jika tanggal penerimaan belum diketahui, minta informasi tambahan.'),
('RUSAK-03','barang_rusak','Keputusan penanganan kerusakan','Tim retur memeriksa apakah penggantian atau pengembalian sesuai kebijakan. Draf hanya menjelaskan langkah pemeriksaan dan tidak menyetujui transaksi.'),
('SESUAI-01','barang_tidak_sesuai','Varian atau barang berbeda','Minta foto barang, label kemasan, dan rincian barang yang dipesan. Cocokkan warna, ukuran, serta jumlah dengan data pesanan sebelum menilai ketidaksesuaian.'),
('SESUAI-02','barang_tidak_sesuai','Kekurangan isi paket','Minta foto isi paket dan daftar item yang belum diterima. Tim retur memverifikasi pengemasan. Jangan menjanjikan pengiriman ulang sebelum pemeriksaan.'),
('SESUAI-03','barang_tidak_sesuai','Ongkos retur ketidaksesuaian','Ongkos retur ditentukan setelah kesalahan pengiriman terverifikasi. Jangan meminta pelanggan membayar atau menjanjikan penggantian biaya sebelum keputusan operator.'),
('RETUR-01','retur_refund','Persyaratan pengajuan retur','Minta nomor pesanan, alasan retur, dan kondisi barang. Tim retur akan memeriksa kelayakan permintaan berdasarkan bukti dan kebijakan toko simulasi.'),
('RETUR-02','retur_refund','Status pengembalian dana','Status pengembalian dana hanya boleh disebut jika tersedia pada data pesanan. Jika belum tersedia, sampaikan bahwa operator perlu memeriksa; jangan memberi tanggal pencairan pasti.'),
('RETUR-03','retur_refund','Langkah sebelum mengirim retur','Pelanggan menunggu instruksi alamat dan nomor pengajuan dari operator sebelum mengirim barang. Sistem AI tidak membuat persetujuan retur.'),
('BATAL-01','pembatalan','Permintaan pembatalan','Periksa status pesanan. Pembatalan pesanan yang belum dikirim perlu persetujuan operator. Jangan menyatakan pesanan sudah dibatalkan.'),
('BATAL-02','pembatalan','Pesanan yang telah dikirim','Jika pesanan telah dikirim, pembatalan langsung belum dapat dipastikan. Operator menjelaskan opsi berdasarkan kondisi pesanan dan kebijakan retur.'),
('BATAL-03','pembatalan','Perubahan pesanan','Perubahan alamat atau item memerlukan pemeriksaan status pemrosesan. Minta nomor pesanan dan perubahan yang diinginkan tanpa meminta data pembayaran rahasia.'),
('BAYAR-01','pembayaran','Dana terpotong, pesanan gagal','Jika data pesanan simulasi membuktikan dana terpotong dan status pesanan gagal, tandai prioritas P1 untuk billing. Minta nomor pesanan dan referensi transaksi yang sudah disamarkan.'),
('BAYAR-02','pembayaran','Verifikasi pembayaran','Jangan meminta PIN, OTP, kata sandi, CVV, atau nomor kartu lengkap. Jika bukti bayar diperlukan, minta pelanggan menyamarkan informasi sensitif.'),
('BAYAR-03','pembayaran','Pembayaran belum terkonfirmasi','Tim billing harus memeriksa status transaksi. Draf tidak dapat memastikan pembayaran berhasil atau dana dikembalikan tanpa data yang mendukung.'),
('AKUN-01','akun','Kesulitan masuk akun','Arahkan pengguna memakai fitur lupa kata sandi pada situs toko. Jangan meminta kata sandi atau OTP. Jika akses tetap bermasalah, eskalasi ke customer care.'),
('AKUN-02','akun','Perubahan informasi akun','Perubahan email dan nomor telepon membutuhkan verifikasi melalui kanal resmi toko. Draf tidak boleh menyatakan perubahan telah dilakukan.'),
('AKUN-03','akun','Aktivitas akun tidak dikenal','Minta pengguna mengganti kata sandi melalui kanal resmi dan hubungi customer care. Jangan meminta pengguna membagikan kode keamanan.'),
('UMUM-01','lainnya','Informasi belum cukup','Jika masalah belum jelas, minta pelanggan menjelaskan kendala utama dan nomor pesanan bila berkaitan dengan pembelian. Tandai untuk pemeriksaan operator.'),
('UMUM-02','lainnya','Lebih dari satu masalah','Jika ada beberapa permintaan yang tidak dapat dipisahkan, minta operator menentukan kebutuhan utama. Jangan membuat keputusan transaksi otomatis.'),
('UMUM-03','lainnya','Batas layanan demo','Seluruh nama, pesanan, dan kebijakan dalam demo adalah simulasi. Operator meninjau semua draf sebelum persetujuan dalam aplikasi. Tidak ada pesan eksternal yang dikirim.'),
]

def seed_policies(db):
    for key, category, title, body in POLICY_SEED:
        if not db.get(Policy, 'POL-'+key): db.add(Policy(id='POL-'+key, category=category, title=title, body=body))
    db.commit()

DEMO_TICKETS = [
('Nadia Putri','Barang datang pecah, ingin mengajukan retur','Halo kak, paket gelas saya sudah sampai tapi dua gelasnya pecah. Kemasan luar juga penyok. Bisa bantu proses retur?','barang_rusak','P2','ditinjau','DEMO-1001'),
('Rizky Pratama','Pembayaran terpotong, pesanan masih gagal','Saldo saya sudah terpotong untuk pesanan ini, tetapi di aplikasi tertulis pesanan gagal. Mohon bantu cek ya.','pembayaran','P1','baru','DEMO-1002'),
('Alya Safitri','Paket belum sampai melewati estimasi','Pesanan saya seharusnya sampai tiga hari lalu, tapi belum ada kabar. Bisa tolong cek posisi paketnya?','status_pengiriman','P1','baru','DEMO-1003'),
('Dimas Saputra','Warna sepatu berbeda dengan pesanan','Saya pesan sepatu hitam ukuran 42, yang datang malah putih ukuran 40. Saya ingin menukar barangnya.','barang_tidak_sesuai','P2','ditinjau','DEMO-1004'),
('Sinta Dewi','Menanyakan status refund','Permintaan retur saya sudah diperiksa. Bagaimana cara mengecek status pengembalian dananya?','retur_refund','P2','disetujui','DEMO-1005'),
('Fajar Maulana','Ingin membatalkan pesanan','Kak, saya salah pilih ukuran. Pesanan belum dikirim, apakah masih bisa dibatalkan?','pembatalan','P3','baru','DEMO-1006'),
('Maya Lestari','Tidak bisa masuk ke akun','Saya sudah mencoba login beberapa kali tetapi selalu gagal. Emailnya masih aktif. Bagaimana memulihkan akun saya?','akun','P3','selesai',None),
('Bagas Aditya','Minta bantuan untuk pesanan','Halo kak, saya mau bertanya tentang pesanan saya. Bisa bantu?','lainnya','P3','baru',None),
('Intan Permata','Barang kurang satu item','Dalam satu paket seharusnya ada tiga kaus, tetapi saya hanya menerima dua. Mohon diperiksa.','barang_tidak_sesuai','P2','ditinjau',None),
('Arif Hidayat','Perubahan alamat sebelum dikirim','Saya ingin mengganti alamat pesanan karena salah pilih alamat kantor. Pesanannya belum dikirim.','pembatalan','P3','selesai',None),
('Putri Ananda','Nomor resi belum muncul','Pesanan saya sudah diproses kemarin, tapi nomor resinya belum muncul. Apakah bisa dicek?','status_pengiriman','P3','disetujui',None),
('Rama Wijaya','Bukti transfer belum terkonfirmasi','Saya transfer tadi pagi tetapi pembayaran masih menunggu. Mohon bantu verifikasi transaksinya.','pembayaran','P3','baru',None),
]

def seed_workspace(db, workspace_id):
    for i in range(1,7):
        db.add(Order(workspace_id=workspace_id, code=f'DEMO-100{i}', facts={'simulated':True,'status':'failed' if i==2 else 'delivered' if i in (1,4,5) else 'shipping' if i==3 else 'processing','payment_status':'charged' if i==2 else 'paid','overdue_hours':72 if i==3 else 0,'item':'Pesanan contoh '+str(i)}))
    for index, (name,title,message,category,priority,status,code) in enumerate(DEMO_TICKETS):
        t=Ticket(workspace_id=workspace_id,number=1042-index,subject=title,message=message,customer=name,category=category,team=TEAMS[category],priority=priority,status=status,order_code=code,created_at=utcnow()-timedelta(hours=index*3+1),resolved_at=utcnow() if status=='selesai' else None)
        db.add(t); db.flush()
        db.add(Analysis(ticket_id=t.id,revision=1,result={'category':category,'score':None,'calibration':'not_applicable','needs_review':True,'classifier_version':'curated-scenario-v1','source':'stored_example','suggested_team':TEAMS[category],'suggested_priority':priority,'priority_reason':'Contoh prioritas yang ditetapkan dalam skenario demo.'}))
        p=next(p for p in db.scalars(select(Policy).where(Policy.category==category)))
        body='Terima kasih sudah menghubungi kami. '+p.body+' Kami akan membantu memeriksa informasi yang tersedia sebelum menentukan langkah selanjutnya.'
        db.add(Draft(ticket_id=t.id,revision=1,body=body,source='stored_example',policy_refs=[{'id':p.id,'version':1,'title':p.title,'body':p.body}],status='approved' if status in ('disetujui','selesai') else 'draft',model_version='curated-scenario-v1'))
        db.add(AuditEvent(ticket_id=t.id,action='Contoh tiket dimuat',detail={'simulated':True}))
    db.commit()
