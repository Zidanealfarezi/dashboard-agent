# Daftar Bukti yang Masih Kurang (Pembaruan Pasca-Penyerahan Bukti Visual)

Dokumen ini mencatat secara transparan status pemenuhan bukti dan item-item operasional yang **masih belum tersedia** untuk menuju operasional produksi otonom penuh per 5 November 2026.

---

### Status Pemenuhan Bukti Visual Terbaru:
* **Tangkapan Layar Prompt Google Flow:** **TERPENUHI (RESOLVED).**  
  Pengguna telah menyerahkan tangkapan layar otentik antarmuka Google Flow (`flow-prompt-ui.png`) yang memperlihatkan teks prompt lengkap, referensi master Dinda terpasang, serta setelan Video 720p 6s x1 sebelum tombol submit ditekan.
* **Tangkapan Layar Obrolan Telegram:** **TERPENUHI (RESOLVED).**  
  Pengguna telah menyerahkan dua tangkapan layar otentik aplikasi Telegram:
  1. `telegram-video-received.jpg`: Menampilkan pesan uji koneksi bot (11:56 AM) dan penerimaan file dokumen video `dinda-technical-pilot-2026-11-05 • v1` (12:04 PM).
  2. `telegram-card-acc.jpg`: Menampilkan kartu review balasan dengan verifikasi Media SHA256 (`bc2d75b0...`) dan Caption SHA256 (`e9ff7cb4...`) yang 100% cocok dengan basis data, serta status akhir *"Keputusan: ACC tersimpan. Belum diposting"* dengan tombol inline telah terhapus.

---

### Daftar Bukti & Prasyarat yang Masih Kurang (Pending Prerequisites):

#### 1. Pengujian Profil dan Akun Flow Karakter Nara & Rania
- **Eksekusi Model Profil Nara:** Profil `characters/nara` belum diuji menjalankan model Hermes untuk navigasi browser atau pembuatan formulir Google Flow.
- **Eksekusi Model Profil Rania:** Profil `characters/rania` belum diuji menjalankan model Hermes untuk navigasi browser atau pembuatan formulir Google Flow.
- **Akun Google Flow Akun 2 dan Akun 3:** Pengujian pilot teknis baru dilakukan pada akun `flow_1` (Chrome Mutia / proyek Dinda). Dua akun Flow lainnya belum diverifikasi dan belum dipetakan ke profil masing-masing.

#### 2. Bukti Tren Media Sosial yang Terverifikasi Kuat
- **Metrik Analitik Video TikTok:** Kandidat riset TikTok yang diperoleh (misal: Overtime Palembang) menampilkan angka metrik (21, 0, 5, 10) tanpa label yang dapat dipastikan, dan tanggal publikasi tidak terbaca pada DOM snapshot.
- **Pemutaran Visual Video Referensi:** Halaman video TikTok dapat diekstraksi sebagai teks, namun web player browser melaporkan gagal memutar video. Isi visual dan keterkaitannya dengan tren kuliner Palembang belum terbukti secara mandiri (kandidat belum boleh disebut viral atau top tren).

#### 3. Pustaka Audio & Penyesuaian Sound TikTok
- **Kecocokan Persis Sound Referensi:** Pengujian fitur pencarian Sounds pada TikTok Studio dengan kueri `"LEU"` dan `"original sound - LEU"` tidak menghasilkan kecocokan persis dengan ID sound referensi `7671150180729932552`.
- **Pengujian Attachment & Trimming Musik:** Penempelan lagu referensi ke video dan pemilihan segmen potongan durasi (audio offset trimming) pada platform belum pernah diuji.

#### 4. Jalur Publikasi Otonom & Adapter Publishing
- **Tombol Publikasi "Post":** Pengujian TikTok Studio oleh Codex baru sampai tahap menyimpan draf privat dengan visibilitas *"Only you"* dan label AI. Tombol *"Post"* belum pernah ditekan.
- **Adapter Publikasi Hermes:** Seluruh alur TikTok Studio pada pilot dikerjakan secara manual oleh Codex melalui browser Chrome native; belum ada adapter publikasi otomatis yang dioperasikan oleh Hermes.

#### 5. Background Daemon & Penjadwalan Berkelanjutan
- **Daemon Penerima Telegram Berkelanjutan:** Adapter review Telegram saat ini hanya berjalan dengan perintah sekali panggil (`receive-once`). Belum ada background service / daemon yang mendengarkan callback query secara terus-menerus.
- **Scheduler Otonom:** Autopilot dan scheduler berjadwal (termasuk jadwal Codex lama yang disimpan `PAUSED`) berada dalam status dinonaktifkan. Belum ada trigger berulang otomatis yang disahkan untuk produksi harian.
