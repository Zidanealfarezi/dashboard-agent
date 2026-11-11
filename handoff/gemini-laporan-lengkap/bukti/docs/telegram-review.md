# Review Telegram — pilot live lulus, tanpa daemon

Pembaruan 5 November 2026: pengguna mengizinkan pilot dan adapter diaktifkan untuk
tes sekali panggil. getMe/getWebhookInfo lulus; pesan, file final dan kartu review
berhasil terkirim. Tidak ada webhook aktif atau daemon polling. Callback ACC pengguna
kemudian diterima, disimpan satu kali meskipun ada klik berulang, dan paket diperiksa
ulang dengan approved_package. Kartu diubah menjadi ACC tersimpan dan tombol dihapus.
Uji kirim media → kartu → callback → keputusan persisten lulus. Tidak ada publikasi otomatis.
Catatan nonaktif di bawah adalah riwayat setup sebelum izin pilot.

sync_card_decision memperbarui kartu dari keputusan yang SUDAH tersimpan; fungsi ini
tidak menciptakan ACC. receive-once mencoba memperbarui kartu setelah callback.
Kegagalan edit kartu tidak membatalkan keputusan/cursor. Penerima belum berjalan
terus-menerus: respons seketika untuk operasi rutin memerlukan consumer aktif yang
dirancang dan diaktifkan terpisah dari scheduler produksi.

Implementasi hanya Python standard library. Tidak ada paket, layanan, cron atau bot
yang dijalankan. Tidak ada pesan terkirim pada pengembangan ini. Pengujian memakai
media dummy di folder sementara dan API palsu, bukan akun atau konten produksi.
Transport mengikuti https://core.telegram.org/bots/api (sendDocument, sendMessage,
getUpdates, answerCallbackQuery). Token hanya dibaca ketika panggilan live diizinkan;
URL/error API yang mungkin memuat token tidak dicetak.

## Perintah lokal

Jalankan dari direktori proyek. Gunakan media yang sudah ada di folder content karakter.
Contoh ini memakai placeholder path, bukan media yang telah tersedia:

```bash
python3 -m app.review register --character nara --content nara-001 --kind video --media characters/nara/content/nara-001/v1.mp4 --caption-file characters/nara/content/nara-001/caption.txt
python3 -m app.review prepare --version ID_VERSI_DARI_REGISTER
```

Register menyimpan hash media dan caption, karakter serta tujuan akun pada versi
immutable. Menggunakan ID konten yang sama membuat versi berikutnya dan membatalkan
kelayakan ACC lama. Buat file terpisah untuk tiap revisi agar versi lama tetap utuh.
Prepare membuat satu delivery per versi/penerima tanpa jaringan. Riwayat konten/versi
dan ACC di SQLite, sedangkan media tetap berkas lokal. Target akun berasal dari karakter;
MVP tidak menyediakan pilihan tujuan akun bebas.

## Setelah aktivasi terpisah oleh pengguna

Flag `telegram_enabled` di config/project.json DAN `enabled` di config/telegram.json
harus true. Saat ini keduanya false. Generasi, publikasi, dan scheduler tetap terpisah.
Jangan aktifkan hanya untuk menjalankan tes lokal.

```bash
python3 -m app.review send --review ID_REVIEW_DARI_PREPARE
python3 -m app.review receive-once
```

Send mengunggah file asli sebagai dokumen untuk menghindari kompresi, lalu kartu reply
dengan caption lengkap, nama/akun, versi, hash dan tombol ACC/Revisi/Tolak. File dapat
dibuka/diunduh di Telegram; thumbnail inline bergantung klien dan jenis file.
Caption MVP maksimal 3.000 unit UTF-16, kartu maksimal 4.096; media maksimal 49 MB.
Tidak ada parse HTML/Markdown yang dapat mengubah caption atau tautan dari teks pengguna.

Receive-once membaca maksimal 100 update sekali, tanpa loop, kemudian berhenti. Karena
tidak ada polling latar belakang, tombol diproses hanya ketika perintah ini dijalankan.
Jangan gunakan bot ini untuk gateway Hermes atau consumer lain pada saat bersamaan.
Webhook aktif harus dievaluasi dahulu; adapter tidak menghapus webhook otomatis.
Telegram menyimpan update terbatas (umumnya hingga 24 jam); jangan menjanjikan keputusan
yang diklik saat bot offline akan bertahan selamanya. Review lokal kedaluwarsa 7 hari.

Callback harus berasal dari pengguna terdaftar, chat private terdaftar, pesan bot yang
benar, dan ID kartu yang tercatat. Sebelum mencatat keputusan, adapter memeriksa versi
terbaru, hash media/caption, akun tujuan, state dan masa berlaku review. Klik berulang
tidak menggandakan ACC. Keputusan pertama pada kartu bersifat final; keputusan berikutnya
memerlukan versi baru. Revisi menyimpan permintaan revisi, tidak mengubah caption otomatis.
Pesan teks bebas tidak dianggap ACC dan tidak dijalankan sebagai instruksi.

ACC hanya dicatat; tidak membuat pekerjaan publikasi dan tidak memberi izin biaya.
Fungsi approved_package memeriksa ACC terbaru dan byte media lagi sebelum dipakai
adapter publikasi kelak. Adapter publikasi dan Flow belum dibuat.

## Pengiriman gagal dan pemulihan

Delivery berubah prepared → sending → sent → decided. Timeout/error pengiriman menjadi
unknown. Proses yang mati mendadak dapat meninggalkan sending. Keduanya memblokir
pengiriman ulang otomatis. Periksa chat dan ID pesan secara manual; jangan mengubah state
menjadi prepared tanpa rekonsiliasi. Belum ada perintah rekonsiliasi otomatis.
Jika kartu sudah terkirim tetapi respons hilang, callback ditolak sampai direkonsiliasi.

Cursor getUpdates disimpan setelah pemrosesan. Jika proses mati setelah ACC tersimpan,
update dapat dibaca ulang tanpa menduplikasi keputusan. ACK gagal tidak menghapus ACC.
Tidak ada retry otomatis untuk upload atau pengiriman kartu.

Migrasi v2 dibuat dengan backup SQLite konsisten di operations/backups/ sebelum perubahan.
Pemulihan: hentikan pemakaian lokal, arsipkan database saat ini, lalu pulihkan backup yang
dipilih. Backup sebelum v2 tidak berisi tabel review; jalankan migrasi lagi sebelum memakai
adapter. Jangan menjalankan restore saat ada penulisan database atau membuang ACC baru.

## Status validasi

Tes offline: pengikatan paket/target, idempotensi ACC, keputusan revisi/tolak, penolakan
akun/pesan salah, versi lama, media berubah, kedaluwarsa, replay update, timeout,
pengiriman ganda, pemisahan karakter, serta blokir jaringan saat Telegram nonaktif.
Uji live upload, tampilan Telegram dan klik pengguna belum dilakukan.
