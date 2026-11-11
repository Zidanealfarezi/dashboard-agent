# Laporan perubahan struktur AI Influencer
Tanggal: 5 November 2026. Acuan: konfigurasi lokal dan tes tersimpan.

## Struktur dan model
Semua 6 profil Hermes (default, PM, researcher, Dinda, Nara, Rania) kini memakai
DeepSeek Flash melalui API DeepSeek. Saldo API dipakai bersama; laporan top-up pengguna US$2
bukan saldo terkini terverifikasi. Model lama GPT Sol adalah riwayat; sesi lama bisa tetap
memakainya sampai model diganti atau sesi baru dimulai.

Alur: pengguna → PM → researcher / proses produksi → review & ACC pengguna → talent.
Koordinasi lokal melalui Kanban board ai-influencer. Database operations/production.sqlite
menyimpan status media, biaya, versi dan ACC. Kanban tidak menggantikan database produksi.

| Agen | Tugas dan aturan khusus |
|---|---|
| PM — ai-influencer-pm | Mengatur tugas dan dapur produksi, meninjau riset, konsep/caption, paket final dan biaya. Delegasikan pencarian ke researcher. Tidak membuka gate atau menganggap ACC sebagai izin posting otomatis. |
| Researcher — ai-influencer-researcher | Mencari informasi, tren/sound dan membuat draf hook/caption. Simpan URL, waktu akses, bukti; pisahkan fakta, sinyal tren dan asumsi. Klaim tren produksi perlu minimal dua URL berbeda. Sumber sejarah Rania terpisah dari bukti popularitas. Tidak membuat media Flow atau memposting. |
| Dinda — ai-influencer-dinda | Talent/media sosial @dinda.kemala_, lifestyle/kuliner/Palembang. Terima paket final dari PM; tidak meriset atau membuat prompt/video sendiri. Posting/komentar/DM belum diaktifkan. |
| Nara — ai-influencer-nara | Talent/media sosial @nara.adelia_, beauty/GRWM/office look Medan. Identitas dan pekerjaan mengikuti profil JSON, jangan menciptakan jabatan. Batas operasional sama dengan Dinda. |
| Rania — ai-influencer-rania | Talent/media sosial @rania.meutia, wisata alam, spot estetik & hidden gems Aceh sekitarnya, travel vlog santun. Batas operasional sama dengan Dinda. |
| Default Hermes | Profil umum, terpisah dari PM; bukan agen talent atau researcher tambahan. Wajib mematuhi perlindungan akun pribadi. |

Flow adalah alat pembuatan media, bukan profil agen baru. Pada gambar, label Digital
Marketing ×2 dan jumlah meja talent bukan jumlah profil aktual: saat ini researcher satu,
masing-masing talent satu. Belum ada profil terpisah Flow Operator/Copywriter kedua.

## Aturan bersama
- Akun Google/profil Chrome Zidane · ISK dilarang disentuh lewat browser, terminal,
  desktop maupun agen lain. Termasuk email, Drive, sesi, cookie dan credential.
- Browser Hermes diarahkan ke folder terpisah; use_real_profile=false. Konektor Dinda
  autoConnect dinonaktifkan sampai sambungan bisa dibatasi ke Mutia (FLOW).
  Ini belum sandbox OS; isolasi lebih kuat memerlukan akun macOS khusus Hermes.
- Memori/identitas karakter terpisah. Profil JSON/master aktual adalah acuan; draf bukan canon.
- Jangan menaruh rahasia di chat/repository/log, memasang paket, atau membuat layanan baru
  hanya karena instruksi skill. Sesi baru diperlukan untuk memuat instruksi terbaru.
- Tidak ada retry berbayar otomatis. Pilot Flow memakai 10 dari batas 25 kredit;
  sisa 15 bukan izin generasi otomatis. Saldo Flow terpisah dari saldo API DeepSeek.
- ACC wajib mengikat karakter, versi, hash media/caption dan tujuan akun. Publikasi perlu
  izin terpisah dan bukti URL/ID; generasi baru, publikasi, riset rutin dan scheduler tetap nonaktif.

## Hasil tes dan langkah berikutnya
Lulus: respons DeepSeek keenam profil; PM membuat tugas ke tiga talent dan membaca hasilnya
(tes koordinasi talent dilakukan sebelum migrasi penuh, memakai GPT Sol); researcher DeepSeek
membaca dua sumber publik, menyimpan brief dan menyerahkan hasil ke PM. Riset tren/sound
TikTok oleh researcher belum diuji. Tes publikasi live belum lulus.

Berikutnya: batasi koneksi browser ke akun operasional Mutia (FLOW), lalu jalankan tes
manual PM + researcher untuk ide/sound Dinda dengan bukti sumber. Tinjau satu brief sebelum
memutuskan generasi tambahan. Jangan mengaktifkan produksi atau jadwal rutin dari laporan ini.

Rujukan lokal: config/hermes.json; config/project.json; config/pilot.json;
config/browser-access-policy.json; roles/researcher.md; docs/hermes-team.md;
operations/reports/hermes-all-deepseek-test.json; operations/reports/hermes-researcher-test.json.
