# Brief Perencanaan AI Influencer — Nara, Dinda, dan Rania

Versi: Draft v1, 4 November 2026 (Asia/Jakarta).
Tujuan dokumen: memberi konteks kepada Codex di Mac untuk menyusun rencana implementasi yang dapat ditinjau pengguna.
Status: PERENCANAAN. Dokumen ini belum merupakan persetujuan implementasi atau aktivasi produksi.

## 1. Tugas Codex pada sesi pertama

Baca brief ini, rangkum pemahamanmu, lakukan pemeriksaan lokal yang benar-benar read-only bila diperlukan, lalu susun rencana teknis. Bedakan keputusan pengguna, usulan teknologi, dan hal yang belum terbukti.

Pada tahap ini jangan menginstal atau menghapus paket, membuat struktur proyek, menulis kode implementasi, mengubah konfigurasi, memperbarui Hermes, mengaktifkan atau menghentikan layanan, membuat cron job, menjalankan generasi media, menggunakan kredit berbayar, atau menerbitkan konten. Sajikan rencana di chat dan tunggu persetujuan eksplisit sebelum implementasi. Jika suatu keputusan penting belum tersedia, ajukan paling banyak tiga pertanyaan yang paling menentukan.

Pemeriksaan read-only boleh mencakup versi macOS, arsitektur, RAM, ruang SSD kosong, keberadaan perangkat lunak, dan status layanan Hermes. Batasi pemeriksaan pada kebutuhan proyek dan instalasi Hermes. Jangan membaca berkas pribadi yang tidak terkait atau menampilkan password, OTP, token, API key, cookie, dan isi berkas kredensial. Laporkan keberadaan/metode koneksi tanpa nilai rahasianya. Jangan menganggap lingkungan cloud adalah Mac pengguna.

## 2. Tujuan dan keputusan pengguna

Pengguna ingin tiga AI influencer memproduksi konten sendiri: mencari ide berdasarkan tren terkini yang cocok, mengembangkan cerita, menyiapkan foto/video, dan menulis caption. Pengguna dapat memasukkan ide tambahan melalui Telegram.

Tujuan awal: membangun karakter dan followers, serta mendatangkan perhatian ke Intan Suar Kartika. Sebagian konten mengarah ke produk melalui kebutuhan cerita. Frekuensi promosi yang pasti belum ditetapkan; jangan membuat semua unggahan menjadi iklan.

Target per akun: satu unggahan sehari dengan komposisi 20 video dan 10 foto dalam periode 30 hari. Total ketiga akun: 60 video dan 30 foto. Durasi video reguler belum ditetapkan. Foto pemandangan, makanan, tempat, atau benda boleh menjadi konten jika sesuai kehidupan karakter.

Pengguna wajib memberi ACC sebelum publikasi. Persetujuan harus melekat pada karakter dan versi media/caption yang ditinjau. Perubahan versi memerlukan ACC ulang. Konten tanpa persetujuan tetap menunggu meskipun jadwalnya tiba. ACC publikasi berbeda dari izin menghabiskan anggaran produksi.

Karakter diharapkan memiliki rutinitas, hubungan sosial, dan cerita yang berlanjut, dengan identitas awal yang konsisten. Detail biografi baru yang penting perlu diputuskan pengguna. Draf yang ditolak tidak dianggap sebagai kejadian resmi dalam kehidupan karakter.

Pengguna secara tegas menginginkan perencanaan diselesaikan sebelum implementasi dan deployment. Codex di Mac akan menjadi pelaksana pembangunan setelah rencana disetujui. Hermes adalah kandidat pengelola operasional; koneksi model dalam Hermes merupakan konfigurasi yang berbeda dari sesi Codex yang sedang dipakai untuk membangun proyek.

## 3. Identitas karakter yang telah ditetapkan

| Karakter | Akun TikTok | Asal | Arah utama |
|---|---|---|---|
| Nara Adelia | @nara.adelia_ | Medan | Beauty, GRWM, office look, dan keseharian perempuan yang bekerja di Intan Suar Kartika. Divisi/jabatan belum ditentukan. |
| Dinda Kemala | @dinda.kemala_ | Palembang | Lifestyle, kuliner, jalan-jalan, dan daily vlog Palembang. Pekerjaan lain belum ditentukan. |
| Rania Meutia | @rania.meutia | Aceh | Cerita sejarah dan budaya Aceh; dapat membawa cerita keseharian yang tetap sesuai identitasnya. |

Bahasa utama Indonesia dengan sentuhan daerah yang ringan dan konsisten. Format produksi umumnya vertikal 9:16. Visual harus mempertahankan wajah, tubuh, tekstur kulit natural, dan suara antar-konten.

Referensi historis: Nara tampil berambut panjang cokelat pada rancangan terbaru; Dinda dan Rania menggunakan hijab dalam referensi yang tercatat. Foto master aktual tetap menjadi acuan dan perlu disediakan/diidentifikasi saat implementasi. Brief ini tidak membawa berkas master tersebut.

Usia pasti, tanggal lahir, tinggi/berat badan, keluarga, nama teman, tempat tinggal rinci, dan identitas suara final belum ditetapkan. Jangan mengarangnya sebagai keputusan pengguna. Jangan menggunakan foto tangkapan layar aplikasi sebagai foto karakter.

Produk yang pernah dipakai: Paku Cap Keris dari Intan Suar Kartika. Foto produk asli diperlukan agar kemasan tidak berubah. Dalam naskah gunakan nama lengkap Intan Suar Kartika. Kebutuhan produk lain dan pembagian promosi per karakter masih terbuka.

## 4. Perangkat dan kondisi instalasi

Perangkat yang dilaporkan pengguna: Mac mini M4, RAM 16 GB, SSD 256 GB. Mac tersedia untuk menyala 24 jam. Versi macOS dan ruang SSD yang benar-benar kosong belum diperiksa.

Akun macOS pada log: zidane; nama host JerryMac.

Log instalasi yang diberikan pengguna mengonfirmasi:
- Hermes Agent v0.22.7 terpasang melalui installer resmi.
- Data dan konfigurasi dasar berada di /Users/zidane/.hermes.
- Perintah hermes dipasang melalui /Users/zidane/.local/bin.
- Terminal backend dipilih local.
- Browser lokal Chromium dan browser-harness telah disiapkan installer.
- CuaDriver disiapkan, tetapi status izin macOS belum dikonfirmasi. Browser automation dan computer use desktop perlu dibedakan.
- Konfigurasi inference provider dibatalkan. Saat akhir setup, provider belum terhubung.
- Telegram belum dikonfigurasi.
- Installer memasang dan menjalankan gateway launchd. Status hidup terbaru perlu diperiksa read-only; jangan menganggap status historis adalah kondisi sekarang.
- Fitur gambar API, vision, dan beberapa alat lain belum dikonfigurasi.
- Label model Claude pada wizard tidak membuktikan provider Claude aktif.

Pengguna kini melaporkan Codex di Mac sudah siap digunakan. Tiga profil karakter, folder produksi khusus, database proyek, serta integrasi Flow belum dibuat dalam pekerjaan percakapan ini. Jangan mengulang instalasi Hermes tanpa kebutuhan yang dibuktikan.

## 5. Layanan yang sudah dimiliki

Pengguna berlangganan Google AI Pro dan menyebut memiliki 1.000 kredit Flow. Prioritaskan evaluasi layanan yang sudah dibayar sebelum mengusulkan langganan tambahan.

Kredit dan kuota harus diperiksa berdasarkan model, jumlah hasil, durasi klip, dan percobaan ulang. Jangan menghitung satu request sebagai satu video final atau menganggap 1.000 kredit berlaku untuk setiap karakter. Periksa ketentuan resmi terbaru mengenai kuota gambar, kredit harian/bulanan, masa berlaku, dan biaya model. Jangan menganggap kredit Flow sebagai saldo Gemini API.

Pengguna juga membeli akses yang disebut Codex non-Pro melalui bot Oksa, dengan promosi 100 juta token. Bentuk akses sebenarnya belum terverifikasi: akun login, berkas autentikasi, atau Base URL + key. Nama model, jumlah token, keabsahan hak akses, dan kompatibilitas belum dibuktikan. Jangan menganggap akses tersebut adalah API key OpenAI Platform, gratis tanpa batas, atau sudah tersambung ke Hermes. Pengguna memasukkan rahasia melalui alur lokal yang sesuai, bukan dalam jawaban/chat.

Anggaran bulanan tambahan di luar layanan yang sudah dimiliki belum ditetapkan.

## 6. Arsitektur kandidat yang perlu dinilai

Rancangan yang sedang dibahas: Hermes + browser lokal pada Mac + Google Flow + Telegram + penyimpanan lokal.

Hermes menjalankan pekerjaan kreatif menggunakan koneksi model yang nanti dipilih. Browser mengoperasikan antarmuka Flow yang menggunakan kuota langganan. Alur yang ingin diuji setelah rencana disetujui: membuka proyek karakter, memasukkan referensi dan prompt, memilih pengaturan, menjalankan generasi, mengenali hasil selesai, mengambil hasil, menyimpan metadata, lalu mengirim pratinjau ke Telegram.

Kemampuan browser umum Hermes telah ditinjau melalui dokumentasi, tetapi alur Flow end-to-end pada akun pengguna belum diuji. Jangan menyebut integrasi sudah berhasil atau menjanjikan operasi tanpa intervensi. Perencanaan perlu mencakup sesi login yang persisten, pengenal karakter/proyek yang benar, status pekerjaan, batas biaya, pencegahan generate ganda, dan jeda ketika autentikasi memerlukan pengguna. Gunakan jalur antarmuka/layanan yang didukung; jangan mengusulkan bypass verifikasi.

9Router bersifat opsional sebagai penghubung model; putuskan setelah format akses diketahui. Ia tidak otomatis menambahkan hak pembuatan gambar/video atau kuota Flow.

SQLite dan folder media merupakan kandidat penyimpanan. Bedakan state/profil internal Hermes, identitas karakter, riwayat cerita, katalog aset, antrean pekerjaan, dan persetujuan publikasi. Pertimbangkan tiga profil Hermes terpisah dengan koordinasi pekerjaan yang hemat sumber daya; jangan mengasumsikan semua agen dan browser harus berjalan bersamaan.

Lokasi proyek yang baru diusulkan: /Users/zidane/AI-Influencer/, dengan subfolder characters/nara, characters/dinda, characters/rania, dan shared. Ini rencana lokasi, bukan bukti bahwa folder tersebut ada. Shared dapat berisi aset produk dan referensi bersama; jangan mencampurkan memori kejadian karakter.

FFmpeg merupakan kandidat penyambungan klip/audio dan penyesuaian format. Remotion dapat dievaluasi jika overlay/subtitle membutuhkannya. Jangan menambah komponen yang belum diperlukan.

## 7. Kebutuhan motion transfer

Pengguna menginginkan foto karakter dapat mengikuti gerakan/joget dari video referensi. Ini kebutuhan khusus yang harus dibuktikan dengan hasil, terpisah dari video generatif biasa.

Wan-Animate/Wan-Animate-2 merupakan kandidat open-weight untuk diuji, bukan mesin produksi yang sudah dipilih final. Kecocokan model, lisensi kode dan weights, dependensi, kebutuhan memori, serta waktu proses harus diperiksa. Keberhasilan memasang ComfyUI tidak otomatis membuktikan model video tersebut layak pada M4 16 GB.

Bandingkan jalur Flow, eksperimen lokal yang sesuai, dan GPU terpisah bila diperlukan. Nyatakan biaya komputasi secara terpisah dari biaya lisensi software. Jangan membeli/menyewa GPU, membuka billing, atau mengunduh checkpoint besar pada tahap perencanaan. Jangan menganggap efek pan/zoom pada foto telah memenuhi kebutuhan meniru joget.

## 8. Publikasi dan kendali

Jalur posting akhir belum dipilih. Periksa dukungan platform dan ketentuan integrasi resmi sebelum menjanjikan auto-post; terutama jangan mengasumsikan aplikasi internal dapat langsung menerbitkan publik melalui TikTok Direct Post API.

Rancangan harus menjaga persetujuan per versi, mencatat hasil publikasi yang benar-benar terkonfirmasi, dan mencegah unggahan ganda. Jadwal tidak boleh dianggap sebagai bukti konten sudah terbit. Riset tren dan evaluasi performa harus menyimpan sumber/tanggal serta membedakan observasi dari dugaan.

## 9. Hasil perencanaan yang diminta

Berikan rencana yang bisa ditinjau pengguna, mencakup:
1. Ringkasan kondisi lokal yang berhasil diverifikasi, beserta batas pemeriksaan.
2. Tabel teknologi yang direkomendasikan, alasan pemilihan, alternatif seperlunya, biaya, dan status kepastian.
3. Arsitektur/alur kerja dari ide dan riset sampai review, revisi, serta publikasi setelah ACC.
4. Struktur folder/profil dan rancangan data, termasuk pemisahan karakter, versi media, serta sumber kebenaran status pekerjaan.
5. Perkiraan kebutuhan produksi 60 video + 30 foto per 30 hari, dengan asumsi durasi, jumlah klip, jumlah percobaan, pemakaian Flow, dan biaya tambahan yang dinyatakan jelas. Jangan menjanjikan kapasitas tanpa pengujian.
6. Rencana implementasi bertahap, validasi yang bermakna, pencadangan, dan cara pemulihan perubahan setelah implementasi nanti.
7. Pertanyaan penting yang belum terjawab, paling banyak tiga pada satu giliran.

MVP yang diusulkan setelah persetujuan: satu karakter, dengan Nara sebagai kandidat awal; satu klip sekitar lima detik mengikuti video referensi, hasil disimpan dan dikirim ke Telegram untuk revisi/ACC. Bahan master dan video penggerak harus tersedia sebelum generasi. Uji kualitas identitas/gerak, waktu, biaya, penanganan kegagalan, dan persetujuan per versi. Publikasi tidak menjadi syarat uji generasi pertama.

Tutup dengan ringkasan keputusan yang memerlukan persetujuan. Jangan mulai implementasi pada sesi perencanaan ini.

## 10. Rujukan untuk diverifikasi

Ini petunjuk riset, bukan jaminan kesesuaian versi yang terpasang:
- Hermes providers: https://hermes-agent.nousresearch.com/docs/integrations/providers
- Hermes profiles: https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- Hermes browser: https://hermes-agent.nousresearch.com/docs/user-guide/features/browser
- Hermes platform support: https://hermes-agent.nousresearch.com/docs/getting-started/platform-support
- Flow credits: https://support.google.com/flow/answer/16526234
- Flow images: https://support.google.com/flow/answer/16729550
- Flow Agent: https://support.google.com/flow/answer/17093911
- Gemini API billing: https://ai.google.dev/gemini-api/docs/billing
- Wan-Animate-2: https://github.com/Wan-Video/Wan-Animate-2
- ComfyUI macOS: https://docs.comfy.org/installation/desktop/macos
- SQLite: https://www.sqlite.org/whentouse.html
- TikTok content sharing: https://developers.tiktok.com/docs/en/content-sharing-guidelines

