Pembaruan 6 November 2026: adapter TikTok Dinda tersedia pada sesi Hermes manual.
AI menyusun kelompok balasan, kode mengurus inbox/requests/komentar, verifikasi,
satu klik kirim dan antrean tahan retry. Empat belas tes lulus; scan dan draf pada
browser asli lulus. Pengiriman live melalui adapter baru belum diuji karena item
tersedia sudah dibalas; tidak ada pesan tambahan dikirim saat pembangunan adapter.
Panduan: docs/tiktok-adapter.md; bukti: operations/reports/dinda-tiktok-adapter-2026-11-06.json.
Scheduler dan publikasi konten tetap nonaktif. Bagian di bawah memuat riwayat pilot.

# AI Influencer — setup Hermes, dibangun melalui Codex

Status operasi 9 November 2026 dan langkah pengajuan yang berlaku ada di
[Kontrol produksi](docs/production-controls.md). Riset tetap berjalan, sementara
generasi dan publikasi dijeda untuk rekonsiliasi.

Pembaruan tim 7 November 2026: Agent Sales ditambahkan memakai profil Hermes
`sales-toko`, model DeepSeek Flash. Peran: roles/sales.md; pengaturan:
config/sales.json. Penambahan ini hanya menyiapkan agen dan tugas internal;
koneksi/pairing WhatsApp tetap ditunda, balasan pelanggan dan scheduler nonaktif.

Status terbaru 5 November 2026: PILOT DINDA BERHASIL DARI GENERATE SAMPAI PENGIRIMAN REVIEW;
PUBLIKASI DAN JADWAL RUTIN BELUM AKTIF.

Pengguna mengizinkan pilot terkontrol maksimal 25 kredit. Hermes sendiri telah
membaca Flow, menyiapkan referensi/prompt, menjalankan satu generasi dan mengunduh
hasil 720p enam detik. Biaya aktual 10 kredit; saldo akun flow_1 setelahnya 458.
Codex memeriksa master dan tiga frame hasil, melakukan editing lokal tanpa audio,
serta mengirim file final dan kartu review ke Telegram. Callback ACC pengguna telah
diterima; satu keputusan tersimpan, hash paket diperiksa ulang, kartu diperbarui
menjadi ACC tersimpan dan tombol dihapus. Tidak ada publikasi terpicu.

Laporan lengkap: docs/pilot-2026-11-05.md. Media:
characters/dinda/content/dinda-technical-pilot-2026-11-05/v1.mp4.
FFmpeg lokal: tools/ffmpeg-runtime; penyiapan ulang tanpa download:
python3 scripts/prepare_media_runtime.py. Editor: python3 -m app.media --help.
Riset: app/research.py dan shared/research/references.sqlite (terpisah dari cerita).

TikTok Studio akun Dinda telah diuji lewat Codex sampai menyimpan draf Only you
dengan label AI. Pencarian sound tersedia, tetapi sound referensi LEU belum ditemukan
secara tepat; attachment/potongan sound dan posting belum teruji. Draf uji bukan
publikasi. Tidak ada kejadian canon baru. Gate generasi baru ditutup sesudah submit;
sisa izin 15 kredit tidak dipakai otomatis. Telegram aktif hanya melalui adapter
sekali panggil; tidak ada daemon proyek. Worker uji Dinda telah dihentikan.

Bagian di bawah memuat catatan fondasi historis; status terbaru di atas mengunggulinya.

Tiga profil: characters/nara, characters/dinda, characters/rania.
Aturan proyek: AGENTS.md. Pengaturan: config/project.json dan config/hermes.json.
Panduan Hermes: docs/hermes-setup.md.
Sembilan skill tambahan per profil sudah dipasang; penggunaan/status: docs/hermes-skills.md.
Database: operations/production.sqlite. Skema dasar: operations/schema.sql; migrasi:
operations/migrations/002_telegram_review.sql dan 003_autopilot.sql (schema aktif v3).
Keputusan terbaru: docs/decisions.md. Alur berikutnya: docs/workflow.md.
Brief historis: docs/brief-original.md.

Tidak ada server, scheduler, bot atau worker browser proyek yang berjalan.
Konektor Chrome Dinda sudah terpasang dan lulus uji baca MCP; sesi tes sudah ditutup.
Adapter review Telegram sudah dibuat, diuji offline, belum diuji end-to-end.
Token valid dan satu penerima sudah dipasangkan. Tidak ada perubahan global Codex/Hermes.
Perintah jaringan adapter memeriksa flag Telegram dan diblokir selama flag nonaktif.
Alur lokal app/autopilot.py memeriksa flag, profil, bukti tren, biaya, dan duplikasi
sebelum membuat reservasi generasi. Generate di Flow memerlukan interaksi browser
Hermes yang belum diuji pada akun. Belum ada adapter publikasi.
Tiga profil Hermes disiapkan nonaktif. Codex adalah pelaksana pembangunan setup.
Tidak ada worker Hermes atau jadwal produksi yang dijalankan oleh proyek.

Yang masih dibutuhkan sebelum produksi:
- uji model Hermes memakai konektor baca Dinda; referensi gambar sudah dipilih;
- tiga akun Flow dan pemetaan proyek/karakter, login oleh pengguna;
- batas kredit uji, lalu pilot Omni Flash x1 dengan durasi native model;
- aktivasi dan uji Telegram end-to-end setelah diizinkan;
- uji browser Flow, generasi, download, QA, serta jalur publikasi yang didukung.

## Foto identitas sekali di awal

Masukkan foto ke FOTO_KARAKTER/Nara, FOTO_KARAKTER/Dinda, FOTO_KARAKTER/Rania.
Semua 33 foto yang diberikan sudah dikatalogkan; acuan wajah/tubuh dipilih Codex.
Nama utama.jpg/png/webp bersifat opsional jika pengguna ingin mengganti pilihan. Folder ini
bahan identitas tetap; pengguna tidak diminta menambahkan foto konten atau caption harian.
Perintah python3 -m app.autopilot sync-references mengenali foto tanpa membuka jaringan.
Codex memeriksa gambar sebelum menandainya sebagai referensi terverifikasi.

## Alur harian agen pelaksana

Panduan lengkap: docs/autopilot-runbook.md. Jadwal Codex lama disimpan PAUSED; belum ada scheduler Hermes.
Hermes kelak mencari tren → menulis cerita/caption/prompt sesuai profil → menyiapkan reservasi
biaya → mengoperasikan Flow → mengunduh/QA → membuat kartu Telegram dari caption rencana.
Ini arsitektur yang disiapkan; pencarian tren/generasi live belum dijalankan pada setup.
Pengguna memberi foto identitas sekali, login akun dan batas biaya, lalu review hasil.

Periksa kesiapan tanpa produksi:
python3 -m app.autopilot status

Panduan fitur review: docs/telegram-review.md. Tidak memerlukan paket tambahan.
Pengujian offline menggunakan fixture sementara dan API palsu:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

Pemeriksaan setup lokal (tidak mengakses jaringan atau memulai produksi):
python3 scripts/check_setup.py

Penyimpanan: 5 GiB media aktif dan minimum 10 GiB kosong masih kebijakan usulan.
Arsip/backup eksternal belum tersedia. Tidak ada bahan karakter atau media dihasilkan.

## Status Hermes tanpa menjalankan model

python3 -m app.hermes_bridge status

Provider root telah diperiksa: openai-codex / gpt-6.1-sol. Tes jawaban root dilaporkan
berhasil oleh pengguna. Konfigurasi ketiga profil sudah disiapkan; tes model per profil,
browser dan Telegram live belum dilakukan. Token Telegram tetap di adapter proyek.
