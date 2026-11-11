# Kantor Intan — Studio Tim (Virtual Office 3D)

Kantor 3D interaktif untuk tim agen AI PT Intan Suar Kartika / Hermes.

## 🌐 Tautan Publik (Vercel)
- **Domain Resmi:** [https://kantor-ai-intan.vercel.app](https://kantor-ai-intan.vercel.app)
- **Akses Cepat (Auto-Login):** [https://kantor-ai-intan.vercel.app/?token=token_intan_ai_hq_88329104](https://kantor-ai-intan.vercel.app/?token=token_intan_ai_hq_88329104)
- **PIN Akses Masuk:** `7463982122` atau `intan`

## Alamat Lokal
- **Local Server:** `http://127.0.0.1:5173/`

- `index.html`: struktur halaman dan akses masuk.
- `studio.css`: tipografi, warna terang/gelap, denah, dan tata letak responsif.
- `studio.js`: pemilihan agen, tab tim/aktivitas, login/logout, serta sinkronisasi.
- `office-3d.js`: model WebGL, orbit kamera, zoom, raycast pemilihan ruang dan fokus agen.
- `assets/three.min.js` dan `assets/OrbitControls.js`: library lokal yang sudah ada.
- `office_status.py`: pembacaan registry agen dan heartbeat Hermes tanpa menjalankan agen.
- `server.py`: server dan API yang sudah ada, ditambah data kantor dan logout.

Jalankan dari folder ini menggunakan `python3 server.py` jika server belum
berjalan. Jangan menjalankan instance kedua pada port yang sama. Pengaturan
akses yang sudah ada tetap berlaku; jangan menaruh sandi atau token di frontend.

Data produksi dibaca dari SQLite dengan mode read-only. Jumlah tugas aktif
berasal dari heartbeat gateway yang masih segar; heartbeat lewat 120 detik tidak
ditampilkan sebagai pekerjaan aktif. Kesiapan hasil uji dipisahkan dari status
runtime. Saldo Flow ditampilkan per akun beserta tanggal verifikasinya.

Antarmuka hanya membaca status dan riwayat. Pemilihan ruang, tab dan refresh
bukan perintah menjalankan agen. Halaman tidak mengirim Telegram, menghasilkan
media, memposting konten, atau mengaktifkan layanan WhatsApp. Profil Sales tetap
ditunda. Tidak ada paket atau layanan cloud baru untuk desain ini.

Pemeriksaan dan bukti visual: `operations/reports/virtual-office-ui-2026-11-07.json`
di root proyek serta folder gambar dengan nama yang sama tanpa ekstensi.

Lantai 1 berisi PM Intan, Researcher, Sales, dan Hermes utama. Lantai 2
berisi studio Dinda, Nara, dan Rania. Pilih 3D atau Atas untuk mengubah
sudut pandang. Geser untuk memutar dalam mode 3D, gulir atau gunakan tombol
+/− untuk zoom, dan klik meja atau nama agen untuk membuka detail.
Seluruh lantai mengembalikan kamera. Tombol ↗ membuka layar penuh.
Warna status pada label nama mengikuti data dari API.
