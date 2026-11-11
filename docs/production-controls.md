# Kontrol produksi dan status operasi

Cron Hermes adalah sumber jam dan status runtime. Riset
05.00 dan 17.00 WIB aktif. Izin Generate dan Post di konfigurasi ditutup
selama rekonsiliasi, termasuk untuk job Dinda lama pukul 07.00 dan 19.00 WIB.
Skrip browser lama yang
langsung menekan Generate atau Post gagal sebelum membuka browser, termasuk
`scripts/flow_render_gate.js` dan `scripts/tiktok_publisher.js`.

## Jadwal harian ISK

Jadwal resmi operasional konten ISK berbasis data riset analitik akun:

| Jam WIB | Job | Tugas |
|---|---|---|
| 08.00 | `64793d785fd7` | Riset tren & bank OOTD Pinterest harian. |
| 09.00 | `6568e45ca870` | Sinkron saldo Flow (`scripts/sync_flow_status.js`) + produksi Dinda `360p` (maks 20s, Varian 3 + subtitle `editorial_tiktok` bebas koma + lo-fi) dan kirim review ke Telegram. |
| 10.00 | `66abf60b8dd6` | Sinkron saldo Flow + produksi paket video harian ISK berbasis pilar riset (`360p` maks 15s + outro 4.07s <= 20s, upscale Varian 3, subtitle `editorial_tiktok` bebas koma, caption & WA 08198889350) dan kirim review ke Telegram Owner. |
| 11.30 | `d1n4p05t1130` | Sinkron callback ACC (`receive-once`) + posting paket Dinda yang telah di-ACC ke TikTok `@dinda.kemala_` (maksimal 1 post/hari, maksimal 20 detik). |
| 13.00 | `cc5f100e4571` | Sinkron callback ACC + posting paket video ISK yang telah di-ACC ke TikTok `@intansuarkartika` (maksimal 1 post/hari, maksimal 20 detik). |
| 14.00 | `b7a158cdf463` | Sinkron saldo Flow + produksi Bang Ray `360p` (maks 30s, 1 atau multi-klip, Varian 3 + subtitle `editorial_tiktok` bebas koma) dan kirim review ke Telegram. |
| 16.00 | `ec66d01d23f5` | Sinkron callback ACC + posting paket Bang Ray yang telah di-ACC ke TikTok `@teuku.rayyan00` (maksimal 1 post/hari, maksimal 30 detik). |

Jika belum ada ACC saat jam posting tiba, posting ditunda sampai ACC diberikan oleh Owner. Pemantau tombol ACC (`~/.hermes/scripts/poll_telegram_acc.py` yang menjalankan `scripts/telegram_review_watcher.py` setiap 1 menit plus pra-cek `python3 -m app.review receive-once` di setiap cron posting) otomatis mencatat klik ACC/Revisi/Tolak pada `@ISKAGENT_BOT` ke SQLite dan memperbarui kartu Telegram. Paket yang mendapat ACC setelah jam slot dapat langsung diposting segera atau masuk slot berikutnya.

## Satu percobaan per paket

- **Flow.** Simpan rencana melalui `app.autopilot save-plan`, lalu catat
  `reserve`. Operator yang sudah memeriksa akun/proyek operasional dan opsi UI
  menjalankan `python3 -m app.autopilot begin-submit` dengan slot, akun, URL
  proyek, nama model, durasi native, jumlah output, dan total kredit yang
  benar-benar terlihat. Hanya reservasi yang belum dipakai dan cocok yang bisa
  berubah menjadi `submitted`. Setelah itu operator menekan Generate satu kali.
  Gunakan `finish` dengan ID pekerjaan Flow, file final dan biaya aktual yang
  terverifikasi. Untuk hasil meragukan, gunakan `mark-unknown` dan rekonsiliasi.
- **TikTok.** Kirim review lewat adapter resmi dan terima callback ACC yang
  terikat ke paket. Operator memeriksa akun operasional yang terbuka, lalu
  menjalankan `python3 -m app.publication begin --version ID --account @AKUN`.
  Gunakan file dan caption dari paket yang divalidasi, cek akun dan paket tepat
  sebelum pengiriman, lalu klik Post sekali. Gunakan `confirm --publication ID
  --video-url URL` setelah mencocokkan video yang muncul di TikTok dengan paket.
  URL harus menunjuk video pada akun tujuan. Gunakan `mark-unknown --publication
  ID` bila belum pasti. Pengajuan kedua untuk konten yang sama diblokir selama
  percobaan lama belum jelas atau sudah terkonfirmasi.

Kedua perintah mencatat pengajuan sebelum tindakan manual di browser. Kode
lokal tidak membuktikan sendiri bahwa video Flow atau TikTok muncul. Akses
browser umum bukan pembatas OS. Operator wajib memakai akun operasional yang
diizinkan dan mencocokkan bukti UI. Jangan gunakan perintah CDP umum untuk
memintas alur ini.

## Rekonsiliasi dan evaluasi

Rekonsiliasi sisa selisih Flow berdasarkan bukti tiap pekerjaan. Saldo awal dan
akhir saja tidak menentukan biaya per file. `python3 -m app.autopilot status`
menghitung kredit tercatat, reservasi yang belum selesai, dan sisa batas dari
ledger yang sama dengan pemeriksaan reservasi. Sisa batas hitung bukan saldo
Flow dan bukan izin membelanjakan. Laporan lama mencatat 175 kredit, sedangkan
17 baris yang ada di SQLite berjumlah 177. Penahanan produksi tetap aktif
sampai selisih dan ID eksternal bisa dibuktikan. Catatan publikasi lama tanpa versi
sah ditahan di `unknown`; data asli dicatat di
`operations/reports/publication-quarantine-2026-11-09.json`. Periksa akun
operasional untuk menemukan ID video yang tepat sebelum mengesahkan catatan.

Evaluator sekarang menyusun laporan lokal dengan
`python3 scripts/generate_weekly_evaluation.py`. Opsi `--metrics-file` menerima
snapshot terverifikasi berupa daftar objek dengan `video_url`, `observed_at`
berzona waktu, dan hitungan `views`, `likes`, `comments`. Data hanya dipasangkan
ke URL video pada paket yang tercatat. Metrik kosong dilaporkan sebagai belum ada
data. Cron evaluator terjadwal Minggu 20.00 WIB untuk laporan lokal. Token Telegram yang pernah tertulis
di skrip lama perlu dirotasi sebelum mengaktifkan kembali pengiriman laporan.

## Uji WhatsApp Sales

Profil Sales memakai daftar nomor penguji dan mode teks di bridge. Mode ini
menolak pengiriman lampiran, lokasi, dan polling, serta mengganti balasan yang
memuat pola sintaks alat atau path internal dengan teks aman. Setelah pembaruan
Hermes, pastikan endpoint lokal `/health` melaporkan `textOnly: true` sebelum
menggunakan jalur balasan uji.
