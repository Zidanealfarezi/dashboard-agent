Pembaruan tim 7 November 2026: Agent Sales resmi ditambahkan dengan memakai
kembali profil `sales-toko` yang sudah disiapkan. Model DeepSeek Flash; peran
`roles/sales.md`, pengaturan `config/sales.json`. Sales menyiapkan konsultasi
produk, draf penawaran/pesanan, ringkasan prospek dan eskalasi manusia dari data
toko yang disahkan. CLI internal: file/memory/kanban. Katalog dan aturan toko
belum diisi; uji model Sales belum dilakukan. Profil tetap standalone/parked,
WhatsApp dan pairing tetap ditunda. Tidak ada tugas runnable, pengiriman,
scheduler atau daemon yang diaktifkan oleh penambahan ini. PM memuat peran baru
pada sesi baru. Bukti setup: operations/reports/sales-agent-setup-2026-11-07.json.
Profil Sales punya skill lokal `sales-konsultatif` dan sembilan skenario latihan
fiktif di `roles/sales-training/`. Materi siap; jawaban model belum diuji.

Pembaruan adapter 6 November 2026: operasi engagement Dinda sekarang memakai
mcp-dinda_tiktok_adapter sebagai toolset CLI default. AI cukup scan dan menyusun
balasan kelompok; navigasi, pemeriksaan, submit tunggal dan rekonsiliasi dijalankan
kode. Tool raw disimpan untuk perbaikan eksplisit, bukan jalur operasi normal.
Baca docs/tiktok-adapter.md. Tes read/input live lulus; delivery adapter baru belum
lulus live dan tidak boleh diklaim dari pengiriman metode lama. Tidak ada scheduler.

Pembaruan hasil training 6 November 2026: Dinda lulus uji DM dan reply komentar bertingkat setelah perbaikan input. Akses fitur TikTok dan balasan masuk tersedia pada sesi manual terbatas; guard teks/akun/target wajib. Lihat `config/engagement.json` dan `docs/dinda-engagement.md`. Tidak ada daemon, scheduler atau publikasi konten diaktifkan. Catatan belum teruji/nonaktif di bawah adalah riwayat sebelum validasi ini.

Pembaruan engagement 6 November 2026: pengguna kini mengizinkan penyiapan dan pelatihan balasan DM/komentar Dinda serta pemeriksaan isi TikTok. Tools navigasi dan input diaktifkan hanya pada konektor browser khusus Dinda. Lihat `config/engagement.json` dan `docs/dinda-engagement.md`. Tidak ada scheduler, daemon atau publikasi diaktifkan. Status tes live terpisah dari izin. Pernyataan read-only/DM nonaktif di bawah adalah riwayat sebelum otorisasi ini.

Pembaruan 6 November 2026: atas permintaan pengguna, konektor `flow_chrome` Dinda
aktif dengan endpoint eksplisit `http://127.0.0.1:9333`. Proses browser diverifikasi
memakai folder `private/browser/dinda-automation`, bukan profil Chrome pribadi.
Model Hermes berhasil memanggil `mcp__flow_chrome__list_pages` pada tes satu kali.
Tools tetap hanya list_pages/select_page/take_snapshot; balasan DM/komentar,
publikasi dan scheduler belum diaktifkan. Unscoped autoConnect tetap dilarang.
Bukti: `operations/reports/dinda-dedicated-browser-connection.json`.
Catatan konektor Dinda nonaktif di bawah adalah riwayat sebelum perubahan ini.

Pembaruan 5 November 2026: pengguna meminta seluruh Hermes dipindahkan ke DeepSeek.
Default, PM, Dinda, Nara dan Rania kini memakai deepseek / deepseek-flash.
API key berada hanya di .env privat tiap home. Sesi yang sudah terbuka dapat tetap
memakai model lama; gunakan sesi baru atau ganti model eksplisit pada sesi tersebut.
Laporan tes migrasi: operations/reports/hermes-all-deepseek-test.json.
Catatan model gpt-6.1-sol di bawah adalah hasil tes sebelum migrasi, bukan model saat ini.

# Koordinasi lokal PM dan talent

Diizinkan pengguna 5 November 2026. PM memakai DeepSeek Flash; ketiga talent tetap
openai-codex / gpt-6.1-sol. Board: ai-influencer; bukan sumber kebenaran ACC produksi.
Peran dapur produksi/talent mengikuti docs/workflow.md. Status biaya/media/ACC ada di
operations/production.sqlite; baca config/project.json dan config/pilot.json.

Koordinasi lokal/file/memori/kanban diaktifkan. Generasi baru, publikasi, balasan DM/komentar,
scheduler dan daemon belum diaktifkan. ACC tidak otomatis memicu publikasi.

PM memakai kanban_create dengan assignee ai-influencer-dinda / ai-influencer-nara /
ai-influencer-rania dan workspace dir:/Users/zidane/Documents/ChatGPT/AI INFLUENCER.
Uji: baca berkas lokal, max_runtime_seconds=180. Worker memakai
kanban_show lalu kanban_complete dengan bukti, atau kanban_block bila belum berhasil.
Batasi satu tugas berjalan. Jangan mengklaim tes model sukses hanya dari pembuatan kartu.

Eksekusi manual satu kali:
hermes -p ai-influencer-pm kanban --board ai-influencer dispatch --max 1

Mulai chat PM:
HERMES_KANBAN_BOARD=ai-influencer hermes -p ai-influencer-pm --in "/Users/zidane/Documents/ChatGPT/AI INFLUENCER"

Tidak ada layanan baru diaktifkan. Gateway default yang sudah ada dikelola terpisah;
flag dispatcher per profil tidak menghentikan gateway lain. Jangan membuat kartu runnable
untuk tindakan belum diizinkan. Izin biaya Flow dan publikasi tetap mengikuti gate proyek.

Uji live 5 November 2026 LULUS: PM DeepSeek membuat 3 kartu, ketiga talent menyelesaikan tugas dengan gpt-6.1-sol, dan PM membaca kembali seluruh hasil. Gateway yang sudah aktif ikut auto-specify dan dispatch; triage tidak menjamin kartu tetap diam. Mode aktual existing_gateway_or_manual_once. Jangan membuat kartu untuk tindakan belum diizinkan. Laporan: operations/reports/hermes-team-coordination-test.json. Tidak ada daemon baru dimulai.

Agen baru: ai-influencer-researcher — Trend Researcher & Copywriter, DeepSeek Flash. Riset sumber publik/sound dan draf hook/caption didelegasikan PM lewat board ai-influencer. Lihat roles/researcher.md. Enam skill lokal: grounded-citations, competitor-news-monitor, humanizer, blocked-page-recovery, creative-ideation, social-media-content-calendar. Tidak ada layanan/paket baru atau API pencarian premium.

Tes researcher lulus: PM membuat t_e2a152db, researcher membaca dua dokumentasi publik dan menyimpan brief, PM membaca hasilnya. Laporan operations/reports/hermes-researcher-test.json. Riset tren/sound TikTok belum diuji; jangan disimpulkan dari tes dokumen publik ini.

Akun pribadi Zidane · ISK dilarang diakses seluruh Hermes. Lihat AGENTS.md dan config/browser-access-policy.json. Browser memakai direktori terpisah dan use_real_profile=false; konektor Chrome autoConnect Dinda dinonaktifkan sampai dapat dibatasi ke Mutia (FLOW). Ini bukan sandbox macOS; terminal/desktop masih memiliki kewenangan OS yang sama. Mulai sesi baru untuk memuat instruksi terbaru.
