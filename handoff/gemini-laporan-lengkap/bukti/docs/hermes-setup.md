# Hermes — setup profil, belum produksi

Pembaruan 5 November 2026: pilot terkontrol Dinda telah membuktikan model Hermes
membaca browser, menyiapkan referensi/prompt, generate Omni Flash x1 dan mengunduh
hasil. Biaya 10 dari batas 25 kredit. Laporan: pilot-2026-11-05.md. Worker khusus
Dinda sudah dihentikan dan toolset CLI dikosongkan kembali. Gateway default tidak
direstart. Telegram diuji melalui adapter proyek, bukan native gateway. Publikasi,
scheduler dan model profil Nara/Rania belum lulus uji. Catatan setup di bawah historis.

Pengguna telah mengonfigurasi root Hermes memakai openai-codex / gpt-6.1-sol,
reasoning medium, dan melaporkan tes jawaban teks berhasil. Provider dan nama model
dikonfirmasi dari konfigurasi lokal. Tes model tidak diulang oleh Codex pada tahap ini.

Tiga profil blank dibuat lewat CLI resmi dengan --no-alias dan --no-skills:
- ai-influencer-nara
- ai-influencer-dinda
- ai-influencer-rania

Masing-masing memiliki SOUL.md, config, memori dan state sendiri di ~/.hermes/profiles/.
Lokasi kerja diarahkan ke proyek AI INFLUENCER. Tidak ada penyalinan token, .env,
memori, sesi atau bot dari default. Login OpenAI mengikuti fallback OAuth root Hermes
yang didokumentasikan Hermes; status inference ketiga profil belum diuji satu per satu.
Default config/model dan gateway utama tidak diubah, dihentikan, atau dimulai ulang.

Config awal tiap profil membatasi platform_toolsets.cli dan .telegram menjadi [] dan
gateway.standalone=true. Tidak ada gateway/cron profil yang dipasang/dijalankan.
Browser disiapkan dengan folder sesi terpisah di private/browser/ai-influencer-<id>,
tetapi folder login/session belum diisi dan akses browser belum diuji.
Pembatasan toolset ini adalah konfigurasi Hermes; CLI launcher juga memiliki gate lokal.
Pemisahan profil bukan sandbox OS yang melarang akses folder karakter lain.

## Pelaksana dan sumber kebenaran

Hermes adalah calon pelaksana operasional; Codex membangun dan memeriksa setup.
Instruksi yang dulu memilih Codex saja digantikan keputusan sesi berikutnya yang
memilih dan menguji model Hermes. Tidak ada aktivasi produksi yang tersirat.

Profil karakter dan foto referensi: characters/<id>/profile.json, identity/reference_catalog.json,
story/canon.md, FOTO_KARAKTER/<Nama>. Database proyek: operations/production.sqlite.
Hermes mengurus riset/ide/naskah/caption/prompt sesuai peran, dan kelak operasi browser.
Tidak ada permintaan input konten harian kepada pengguna. Artefak internal disiapkan agen.

Antrean/budget/ACC menggunakan modul app.autopilot dan app.review yang sudah ada,
bukan memori bebas Hermes sebagai status produksi. Ikuti docs/autopilot-runbook.md,
dengan pelaksana sesuai config/project.json.operator. Foto/hasil yang ditolak bukan canon.

## Telegram hanya satu consumer

Token tetap di private/credentials/telegram.json dan penerima tetap di config/telegram.json.
Jangan menyalinnya ke .env atau native gateway Hermes. Telegram memakai adapter proyek
untuk menjaga pengikatan ACC/media/caption/akun/versi. Pengiriman dan receive-once tetap
dibatasi dua flag yang nonaktif. Native chat Telegram Hermes belum disiapkan dan pesan
teks ide belum otomatis diolah menjadi pekerjaan kreatif. Tidak ada pesan dikirim di setup ini.

## Launcher dan aktivasi berikutnya

`python3 -m app.hermes_bridge status` hanya membaca status berkas dan tidak memakai model.
Launcher run menerima character dan task-file yang disiapkan sistem. Ia memeriksa operator,
mode setup, execution_enabled dan autopilot.enabled, serta satu lock global agar tidak ada
dua worker berjalan bersamaan. Tidak ada pemanggilan launcher terjadwal yang aktif.

Sebelum run dapat digunakan: pengguna mengizinkan aktivasi/pilot; periksa budget dan
gate terkait; pilih toolset yang benar-benar diperlukan; uji profil, browser dan Telegram.
Jangan mengaktifkan flag atau toolset sendiri untuk melewati batas setup. Setiap media
tetap memerlukan QA dan ACC. Modul ini tidak menyediakan implementasi auto-post.

Jadwal Codex lama tetap PAUSED dan sekarang bukan pengelola Hermes. Belum ada cron,
launchd baru atau scheduler Hermes untuk pekerjaan ini. Otomatisasi Hermes baru boleh
disiapkan/diaktifkan sesuai arahan pengguna dan setelah alur manual terbukti.

## Yang masih diperlukan

1. Uji tool/browser Hermes tanpa generasi, login akun Flow oleh pengguna, dan pemetaan
   akun/proyek yang tepat per karakter. Chrome Mutia (FLOW) sudah diamati lewat Codex: PRO, 468 kredit, proyek dinda;
   flow_1 dipetakan ke Dinda. Ketiga akun belum tersambung ke sesi browser Hermes.
2. Tetapkan batas kredit uji; lakukan pilot 6/12 detik hanya setelah izin biaya.
3. Uji preview Telegram dan callback ACC secara live jika diizinkan.
4. Baru evaluasi penjadwalan operasional dan publikasi terpisah.

Backup config/SOUL awal tiap profil ada di backups/before-project-setup dalam home profil.
Rollback konfigurasi memakai backup tersebut tanpa menyentuh login root atau sesi lain.
Tidak ada credential yang dimasukkan ke backup proyek. Jangan menghapus profil yang
sudah mempunyai riwayat tanpa meninjau datanya dan meminta izin penghapusan.

## Preferensi video terbaru (menggantikan durasi uji 6/12 detik)

Prioritaskan Omni Flash; x1, satu permintaan generasi per konten, tanpa retry berbayar
otomatis. Durasi mengikuti opsi native model yang sudah diperiksa pada UI. Saat ini
Omni 1.1 Flash memperlihatkan 4/6/8/10 detik dan durasi terpilih 8 detik. Tidak perlu
memaksa 12 detik lewat beberapa generasi. Model pengganti memerlukan keputusan pengguna.
Preferensi ini belum memberi izin membelanjakan kredit atau menekan Generate.

## Hasil uji konektor Chrome — 4 November 2026

Konektor resmi chrome-devtools-mcp 1.12.0 sudah dipasang lokal dan dikonfigurasi
pada profil ai-influencer-dinda, dibatasi pada list_pages/select_page/take_snapshot.
Uji MCP oleh Codex berhasil menemukan URL proyek Dinda yang tepat dan membaca
halamannya dalam satu sesi. Model Hermes tidak dipanggil. Snapshot lengkap dan
isi tab lain tidak disimpan; proses konektor ditutup setelah tes.

Ini menggantikan catatan konektor belum teruji di atas. connected dan
hermes_attachment_verified tetap false sampai sesi operasional Hermes diuji.
Popup Allow Chrome berlaku untuk sambungan debugging baru; bukan setiap aksi.
Hindari pengulangan proses tes; restart konektor dapat meminta izin kembali.
Semua gate produksi tetap false, budget nol, tidak ada generasi atau pesan Telegram.
Bukti: operations/reports/hermes-flow-connection-test.json.
