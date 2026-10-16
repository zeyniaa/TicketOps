# Evaluasi dan langkah peningkatan

Baseline, kalibrasi, serta data split dapat direproduksi melalui `python ml/train_baseline.py`. Dua laporan tersimpan adalah classifier yang sama sebelum dan sesudah kalibrasi, bukan dua arsitektur yang berbeda.

## Pengujian lanjutan yang disiapkan

1. Ganti data sintetis dengan data berizin atau contoh independen yang ditinjau manusia. Pertahankan grup skenario saat membagi split.
2. Training IndoBERT pada dua learning rate, pilih dengan development, lalu uji stabilitas seed. Test tetap dibekukan.
3. Jalankan pembanding klasifikasi Qwen pada ID test yang sama. Gunakan jumlah per-kelas yang sama ketika membandingkan; benchmark subset tidak setara dengan benchmark penuh.
4. Anotasikan 80 kasus retrieval dengan `expected_policy_ids`, lalu ukur Recall@3.
5. Tinjau 80 draf menggunakan rubrik: dukungan fakta, kesesuaian kebijakan, informasi yang belum ada, permintaan rahasia, klaim transaksi, dan keterbacaan. Nilai manusia, bukan penilaian LLM sendiri, menentukan hasil referensi.

## Target dan status

| Ukuran | Target desain | Status awal |
|---|---:|---|
| Classifier macro-F1 | >=0,80 | 0,744 pada bootstrap sintetis; belum tercapai |
| Precision prediksi lolos threshold | >=0,90 | Threshold di development saja; seluruh prediksi tetap ditinjau |
| Retrieval Recall@3 | >=0,90 | Harness tersedia; anotasi manusia belum tersedia |
| Draf tanpa klaim tak didukung | >=90% | Rubrik tersedia; penilaian manusia belum tersedia |

Satu smoke test LLM berhasil tidak membuktikan kualitas draf secara umum. Jangan mengklaim pengurangan workload atau penghematan biaya tanpa pengukuran pengguna nyata.
