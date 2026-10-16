# Verifikasi penyerahan

Tanggal: 16 Oktober 2026, Asia/Bangkok.

## Dijalankan dan lolos

- Build produksi React/TypeScript melalui helper Sites; bundle dipecah menjadi React, forms, charts, dan aplikasi.
- 14 pengujian backend: alur lengkap, sesi terisolasi, CSRF/Origin, validasi input, antrean, deduplikasi job, revisi kedaluwarsa, koreksi, persetujuan, dan pemeriksaan draf.
- 4 pengujian frontend adapter: filter, stale draft, approval/version checks, serta penolakan inferensi bebas dalam showcase.
- Migrasi SQLite kosong: upgrade, downgrade, lalu upgrade; 11 tabel termasuk tabel versi Alembic.
- Rebuild dan import paket backend setelah konfigurasi package discovery diperjelas.
- Seluruh modul Python dan sel kode notebook berhasil dikompilasi.
- Smoke HTTP dengan classifier terlatih dan Qwen3 4B nyata sampai persetujuan dan penyelesaian. Hasil terakhir: 73 kata, 3 referensi kebijakan, sekitar 61,69 detik. Lihat `local-smoke.json`.
- Alur UI lokal: filter kategori, membuat tiket, menerima analisis dan draf Qwen, menyetujui, serta menyelesaikan tiket.
- Build showcase diuji pada viewport desktop 1440×1000 dan ponsel 390×844. Tidak ada overflow horizontal halaman. Detail ponsel memakai tab.
- Inbox, ringkasan, kebijakan, evaluasi, dan status sistem tersedia. Metrik default sesuai classifier terkalibrasi yang digunakan.

## Temuan yang diperbaiki

- Draf JSON yang mengulang instruksi pendek sekarang ditolak; generation melakukan satu percobaan perbaikan, kemudian memakai template berlabel bila tetap gagal.
- Approval draf lama setelah koreksi ditolak. Koreksi tidak dapat digabung dengan penyelesaian untuk melewati review.
- Lebar grafik skor memakai angka CSS, bukan persen dengan koma lokal.
- Font lokal dapat disajikan dari dependency root dalam development.
- Tabel ponsel membatasi elemen aksesibilitasnya agar tidak memperlebar halaman.

## Belum diverifikasi

- Docker/PostgreSQL tidak dijalankan karena Docker tidak tersedia di mesin ini.
- Training IndoBERT di Colab dan benchmark klasifikasi Qwen penuh belum dijalankan. Skrip serta notebook disertakan tanpa skor rekaan.
- Tidak ada evaluasi kualitas manusia atau pengujian pada keluhan pelanggan nyata.
- TestClient mengeluarkan satu peringatan deprecation dari versi Starlette tentang adapter HTTPX; seluruh assertion lulus.

Benchmark sintetis awal: macro-F1 0,744 pada 320 baris dari 64 keluarga test. Target 0,80 belum tercapai. Model tidak dianggap siap produksi.
