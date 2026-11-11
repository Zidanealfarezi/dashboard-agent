# Alur Kerja Operasional Baku AI Influencer (Canonical Workflow)

Standar Operasional Terpadu per 9 November 2026.
Bebas Emoji (Strict 0% Emoji Policy).
Sistem: Dinda Kemala (@dinda.kemala_), Nara Adelia (@nara.adelia_), Rania Meutia (@rania.meutia).

---

## 1. Pembagian Peran dan Tanggung Jawab (Single Truth)

Setiap entitas dalam sistem memiliki batasan tugas yang tegas dan tidak saling tumpang tindih:

1. **Trend Researcher**
   * **Tugas:** Menyiapkan data bukti tren organik, kandidat topik, sound viral, dan referensi hook dari riset platform.
   * **Jadwal Aktual:** Berjalan otomatis melalui cron Hermes `64793d785fd7` setiap pukul 08:00 WIB (1x/hari, tidak terlalu pagi).
   * **Keluaran:** Catatan tren di tabel SQLite `trend_memory` dan `trend_selections`.

2. **PM Intan (@PM_INTAN_BOT)**
   * **Tugas:** Memilih topik terbaik dari hasil riset, mengunci brief kreatif, menyusun storyboard teks, menetapkan prompt Flow beresolusi **360p**, memilih referensi visual yang sesuai, menetapkan durasi sesuai batas per karakter (maksimal **20 detik** untuk Dinda & ISK, maksimal **30 detik** untuk Bang Ray; 1 kali posting per hari per karakter), merakit pasca-produksi terpadu pada kanvas `1080x1920` via `app/media.py --character <id>` (upscale otomatis **Varian 3 Hybrid Foto-Realistik** `55% upscayl-lite-4x + 45% Lanczos CAS + micro grain`, `texture_preserve=0.45` dari input `360p`, lalu hardsub 2-tier **`editorial_tiktok`** tanpa tanda koma: `Ray_Top` putih `#FFFFFF` Helvetica Neue Bold 44 ALL CAPS + `Ray_Bot` kuning limau `#E8FF3B` Times New Roman 126 `ScaleX=72` lowercase per frasa Faster-Whisper) pada seluruh video Dinda, ISK, dan Bang Ray, menulis caption, dan menetapkan akun tujuan. Untuk ISK, gunakan klip utama `360p` (hingga `15` detik) + outro resmi penuh `4.07` detik agar total maksimal `20` detik dan kardus paku curah lepas tanpa plastik. Untuk Bang Ray, gunakan durasi fleksibel `3–30` detik (1 atau gabungan multi-klip `360p`, maksimal `30` detik). Untuk Dinda, gabungkan audio vokal + lofi akustik 15% hingga maksimal `20` detik bersama upscale Varian 3 + subtitle `editorial_tiktok` tanpa koma tersebut.
   * **Batasan Mutlak:** PM dilarang memposting video langsung ke TikTok Studio tanpa keputusan ACC dari Owner.

3. **Flow Operator**
   * **Tugas:** Memeriksa akun, proyek, dan pengaturan Flow. Gunakan `app.autopilot reserve` dan `begin-submit` sebelum satu klik Generate, lalu catat ID pekerjaan Flow dan biaya yang terverifikasi melalui `finish`.
   * **Status:** Jalur browser lama dinonaktifkan. Lihat [kontrol produksi](production-controls.md).

4. **Owner (Kamu) & Pemantau Tombol ACC (`poll_telegram_acc.py`)**
   * **Tugas:** Meninjau video dan caption final, lalu menekan tombol ACC pada kartu review Telegram (`@ISKAGENT_BOT`) untuk versi tersebut. Watchdog Hermes tanpa-LLM (`~/.hermes/scripts/poll_telegram_acc.py` via `scripts/telegram_review_watcher.py` setiap 1 menit) serta pra-cek `python3 -m app.review receive-once` di setiap slot posting memproses klik ACC/Revisi/Tolak, menghapus tombol agar tidak ganda, dan mencatat persetujuan sah di `approvals`.
   * **Kedudukan:** Gerbang otorisasi tunggal sebelum publikasi dijalankan (Opsi B: Semi-Otonom Terkendali).

5. **Publisher (`app.publication`)**
   * **Tugas:** Menerima ID versi yang sudah berstatus ACC (`approved`), mencocokkan integritas berkas di disk (`media_sha256`) dan naskah (`caption_sha256`), memverifikasi kesesuaian akun yang sedang login di TikTok Studio, mengunggah video, membersihkan draft editor dari placeholder, dan mempublikasikan konten dengan visibilitas Everyone. Memblokir publikasi jika karakter sudah memiliki 1 postingan terkonfirmasi pada hari WIB yang sama atau durasi melebihi batas per karakter (`20` detik untuk Dinda & ISK, `30` detik untuk Bang Ray).
   * **Pencatatan:** Mencatat ID video numerik dan URL tayang publik ke tabel `publications`. Jika URL video spesifik belum terdeteksi, status wajib ditahan sebagai `unknown`. Dilarang menggunakan URL profil sebagai bukti tayang.

6. **Talent (Dinda, ISK, Bang Ray)**
   * **Tugas:** Menjalankan persona publik lokal dan interaksi komunitas (membalas komentar dan DM sesuai panduan kepribadian karakter).
   * **Batasan Mutlak:** Talent adalah persona media sosial, bukan eksekutor pengunggahan video.

7. **Evaluator**
   * **Tugas:** Menghitung metrik performa nyata dari postingan yang terverifikasi setiap akhir pekan (Minggu 20:00 WIB). Menandai data kosong sebagai *belum ada data* tanpa membuat estimasi tiruan.

---

## 2. Garis Waktu dan Status Cron Aktual

Jadwal operasional mengacu pada waktu sistem lokal (WIB / UTC+7) dan dikoordinasikan oleh cron Hermes (kebijakan global: maksimal 1 kali posting per hari, input Flow wajib 360p, batas durasi maks 20 detik untuk Dinda/ISK dan 30 detik untuk Bang Ray):

| ID Cron | Nama Tugas | Jadwal (WIB) | Status Nyata | Keterangan |
|---|---|---|---|---|
| `64793d785fd7` | Riset Tren & Bank Opsi Konten | 08:00 | **Active** | Menghasilkan kandidat topik dan 1 paket OOTD harian (1x/hari) |
| `6568e45ca870` | Dinda \| Produksi 09.00 WIB | 09:00 | **Active** | Sync saldo Flow + produksi Dinda 360p (maks 20s, Varian 3 + `editorial_tiktok` bebas koma + lo-fi) & kirim review |
| `66abf60b8dd6` | ISK \| Produksi 10.00 WIB | 10:00 | **Active** | Sync saldo Flow + produksi ISK 360p (klip maks 15s + outro 4.07s <= 20s, Varian 3 + `editorial_tiktok` bebas koma) & kirim review |
| `d1n4p05t1130` | Dinda \| Posting 11.30 WIB | 11:30 | **Active** | Sinkron ACC + posting paket final Dinda ke `@dinda.kemala_` (1x/hari) |
| `cc5f100e4571` | ISK \| Posting 13.00 WIB | 13:00 | **Active** | Sinkron ACC + posting paket final ISK yang telah di-ACC ke @intansuarkartika (1x/hari) |
| `b7a158cdf463` | Bang Ray \| Produksi 14.00 WIB | 14:00 | **Active** | Sync saldo Flow + produksi Bang Ray 360p (maks 30 detik, multi-klip opsional, Varian 3 + `editorial_tiktok` bebas koma) & kirim review |
| `ec66d01d23f5` | Bang Ray \| Posting 16.00 WIB | 16:00 | **Active** | Sinkron ACC + posting paket final Bang Ray yang telah di-ACC ke @teuku.rayyan00 (1x/hari) |
| `6de806aec4cd` | Evaluasi Mingguan Kinerja | Minggu 20:00 | **Active** | Laporan lokal dari posting terverifikasi dan data yang tersedia |

---

## 3. Matriks Alur Keputusan Produksi

```
[Trend Researcher]
       │
       ▼ (Kandidat Bukti Tren)
[PM Intan] ──> Mengunci Brief, Prompt, Caption & Target Akun
       │
       ▼ (Rencana Kreatif)
[Flow Operator] ──> Pintu Render Tunggal (reserve kredit) ──> Render ──> Mix Audio ──> Daftarkan Version
       │
       ▼ (Paket Version)
[Telegram Card] ──> Dikirim ke Chat Owner
       │
       ▼ (Owner menekan ACC pada kartu review)
[Publisher] ──> Verifikasi ACC ──> Cek Akun TikTok Browser ──> Post ──> Simpan Video ID ke SQLite
```
