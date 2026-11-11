# Spesifikasi Teknis: Arsitektur Multi-Agent Hermes untuk @intansuarkartika

Dokumen ini mendefinisikan cetak biru arsitektur (Technical Architecture Blueprint) integrasi akun PT Intan Suar Kartika (@intansuarkartika) ke dalam framework agen otonom Hermes.

---

## 1. Topologi Arsitektur Sistem (Separation of Concerns)

Sistem beroperasi menggunakan model desentralisasi 4 sub-agent otonom yang dikoordinasikan oleh SQLite State Machine dan Cron Scheduler:

1. **Core Account & Identity Orchestrator (ai-influencer-isk)**: Mengelola state akun, brand voice, dan integritas naskah.
2. **Continuous Growth & SEO Analyzer (isk-growth-engine)**: Menambang data TikTok Studio, menganalisis kueri pencarian, dan mengoptimalkan retensi views.
3. **Media Post-Production & Editorial Subtitle Engine (isk-media-engine)**: Pipeline upscale hybrid Varian 3 (`upscayl-lite-4x`, `texture_preserve = 0.45`, `--upscale auto`), ekstraksi audio, penjadwalan stempel waktu Whisper, dan hardsub 2-tier `editorial_tiktok` ASS standar terpadu Dinda/ISK/Bang Ray (`Ray_Top` `#FFFFFF` Helvetica Neue Bold 44 ALL CAPS + `Ray_Bot` `#E8FF3B` Times New Roman 126 `ScaleX=72` lowercase pada `1080x1920`).
4. **Autonomous Publisher & Gatekeeper (isk-publisher-agent)**: Gerbang review Telegram, time-lock 2 jam ACC, dan otomatisasi upload CDP ke TikTok Studio.

---

## 2. Spesifikasi Teknis 4 Sub-Agent Inti

### Modul 1: ISK Core Profile Agent (ai-influencer-isk)
- **Tanggung Jawab**: Menyimpan profil resmi (@intansuarkartika), nomor WA resmi (08198889350), dan penegakan Strict 0% Emoji Policy.
- **Konfigurasi Database**: Terikat pada tabel content (character_id: isk) dan versions (append-only ledger).
- **Aturan Naskah**: Format dialog lugas manusia lapangan, pemotongan caption ringkas, dan pembatasan tepat 3 hashtag terfokus (#pakucapkeris #intansuarkartika #tokobangunan).

### Modul 2: Growth & SEO Analyzer Agent (isk-growth-engine)
- **Protokol Ekstraksi**: Chrome DevTools Protocol (CDP) membaca https://www.tiktok.com/tiktokstudio/analytics.
- **Eksploitasi 89.5% Search Intent**: Mengambil kueri pencarian organik teratas dan menginjeksikannya ke dalam brief kreatif harian.
- **Pilar Prioritas Berdasarkan Data**:
  1. Kawat Duri Diamond: Niche sawit, pagar kebun cabai, dan keamanan batas lahan (rata-rata 265 views, top video 784 views).
  2. Paku Cap Keris: Hook visual 0-3s (banting tang/paku bengkok) dan timbangan pas 25 kg (rata-rata 268 views).
  3. Kereta Sorong Five Star: Uji beban ekstrem 200+ kg di jalan proyek bergelombang (rata-rata 173 views).

### Modul 3: Media Post-Production & Subtitling Agent (isk-media-engine)
- **Input**: Video generatif Google Flow **360p** (Omni 1.2 Flash) bebas watermark/teks bawaan AI (durasi klip utama hingga `15` detik agar total bersama outro maksimal `20` detik), lalu ditingkatkan ke `1080x1920` via `app/upscaler.py` (`Varian 3 Hybrid Foto-Realistik`: `55% upscayl-lite-4x + 45% Lanczos CAS + micro grain`, `texture_preserve=0.45`).
- **Audio & Subtitle Pipeline**:
  - Ekstraksi audio WAV 16kHz via FFmpeg.
  - Faster-Whisper alignment untuk mendapatkan word-level timing presisi.
  - Kompilasi berkas SSA/ASS preset terpadu `editorial_tiktok` **tanpa tanda koma**: baris atas `Ray_Top` putih `#FFFFFF` Helvetica Neue Bold 44 ALL CAPS (`y=1502`) dan baris bawah `Ray_Bot` kuning limau `#E8FF3B` Times New Roman 126 `ScaleX=72` lowercase (`y=1595`) pada kanvas `1080x1920` (diterapkan seragam pada ISK, Dinda, dan Bang Ray; preset lama `isk_yellow` tetap tersedia opsional).
- **Assembly Bumper**: Concat tanpa penurunan kualitas dengan outro bumper resmi PT Intan Suar Kartika (4.0667 detik utuh).

### Modul 4: Autonomous Publisher & Gatekeeper (isk-publisher-agent)
- **Time Gates Harian**:
  - 06:00 WIB: Produksi video selesai, kirim video dan kartu review ke Telegram Owner (chat_id: 7463982122).
  - 06:00 - 08:00 WIB: Window waktu tunggu konfirmasi ACC (spare 2 jam).
  - 08:00 WIB: Jika status approved di SQLite approvals, agen menjalankan pengunggahan otomatis ke TikTok Studio. Jika belum di-ACC, posting ditahan di antrean demi keamanan brand.
- **Otomasi CDP Browser**:
  - Akses tab https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video.
  - Set berkas via DOM.setFileInputFiles.
  - Bypass otomatis modal dialog Joyride (Mengerti) dan hak cipta (Posting sekarang).
  - Injeksi caption ringkas via document.execCommand(insertText).
  - Verifikasi tayang publik di tab profil https://www.tiktok.com/@intansuarkartika dan catat platform_post_id serta post_url ke tabel publications.
