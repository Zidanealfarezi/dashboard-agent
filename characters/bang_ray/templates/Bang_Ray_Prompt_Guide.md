# Panduan Standar Produksi Video AI — Bang Ray
Akun Resmi: @teuku.rayyan00 | Karakter: Bang Ray (Asal Banda Aceh — Berbagi Tips & Trik Bangunan)

Dokumen ini adalah SOP tunggal untuk produksi video edukasi dan tips praktis bangunan karakter **Bang Ray** (`Teuku Rayyan`).

---

## 1. Identitas Visual & Postur Baku

1. **Wajah & Ekspresi Asli:**
   * Berkas master wajah: `FOTO_KARAKTER/BangRay/bangray_three_expression_sheet.jpg` (`NETRAL`, `SENYUM`, `SERIUS`).
   * Kulit sawo matang alami khas pria Aceh dengan tekstur pori-pori nyata (matte natural, nol efek plastik/waxy/CGI).
2. **Postur Badan & Pakaian Kerja Tetap:**
   * Berkas master postur 3 sudut: `FOTO_KARAKTER/BangRay/bangray_fullbody_turnaround.jpg` (`DEPAN`, `SAMPING`, `BELAKANG`).
   * Postur tegap atletis proporsional pekerja lapangan (~173 cm, ~68 kg).
   * Pakaian ciri khas: Kemeja kerja lengan pendek biru dongker (navy) berkancing dua saku dada di atas kaus dalam putih bersih, celana kerja chino/canvas warna khaki, jam tangan lapangan hitam di pergelangan tangan kiri, serta sepatu bot kerja kulit cokelat tua.
3. **Potret Profil Resmi:**
   * Berkas avatar resmi: `FOTO_KARAKTER/BangRay/bangray_profile_avatar.jpg`.

---

## 2. Format Konten Tips & Trik Bangunan

1. **Sumber & Pola Pembelajaran Konten:**
   * Materi tips digali dari riset akun kreator tukang/kuli bangunan populer (pola hook, trik lapangan yang teruji, alat sederhana yang berdampak besar), lalu diadaptasi menjadi demonstrasi orisinal Bang Ray dari Banda Aceh.
2. **Struktur Video Fleksibel (Input Flow Wajib 360p, Golden Duration 10–18 Detik, Maksimal 30 Detik, 1x Posting/Hari):**
   * **Input Google Flow (`360p` Omni 1.2 Flash):** 1 klip native (10–15s) atau 2 klip tersambung lokal (total 20–25s). Durasi ideal 10–18 detik untuk menjamin *completion rate* > 75%.
   * **0–3 detik (Contextual 3-Layer Hook):**
     - *Visual*: Tangan Bang Ray sudah memegang/mengetuk alat atau bidang kerja sejak frame 0.0s.
     - *Text-on-Screen*: Teks judul 3–5 kata tegas di tengah layar (mis. *"Penyebab Keramik Meledak"* atau *"Stop Acian Retak Rambut"*).
     - *Vokal*: Kalimat pertama langsung menyebut gejala masalah spesifik di lapangan (*"Pernah dengar suara retak dari bawah lantai terus keramiknya meledak terangkat? Jangan salahin merek keramiknya dulu..."*). Bebas dari clickbait klise.
   * **Inti Penjelasan & Demonstrasi (3–12s):** Bang Ray mempraktikkan langsung teknik/triknya step-by-step dengan gerakan tangan terukur dan sudut kamera jelas.
   * **Penutup & CTA (12–15s):** 
     - *Save-Bait*: *"Simpan video ini biar waktu renovasi rumah gak boncos jutaan rupiah."*
     - *Debat Komentar / Seamless Loop*: Ajakan diskusi biner (*"Kalian tim aduk semen manual atau pakai mixer instan?"*), dengan kalimat terakhir menyambung ke kalimat awal bila memungkinkan.
3. **Aturan Ketat Kontinuitas Properti (Anti-Barang Muncul & Hilang):**
   * DILARANG keras merancang lebih dari 2 properti utama atau mengganti alat di tengah adegan (*off-screen tool swap*), karena model generatif sering memunculkan palu/alat baru atau menghilangkan alat lama di tengah take.
   * Setiap barang yang disentuh/dipegang Bang Ray WAJIB dijelaskan sudah berada di tangan atau diam di permukaan meja/lantai sejak detik `0.0s` dan tetap terlihat utuh sampai detik terakhir (`only the exact named props exist in frame from 0.0s to the end; no tool or object appears out of nowhere or vanishes mid-shot`).
   * Jika butuh demonstrasi lebih panjang (>15 detik) lewat 2 klip, pisahkan pergantian alat hanya di batas antar-klip atau pertahankan properti yang sama di kedua klip.
   * WAJIB inspeksi frame visual awal, tengah, dan akhir (`0s`, `3s`, `6s`, `9s`, `12s`, `15s`) sebelum registrasi versi; tolak/ulang jika ada benda yang mendadak muncul atau menghilang.
4. **Template Terpadu Varian 3 + Subtitle editorial_tiktok Tanpa Koma & Kebijakan Bahasa:**
   * Bahasa Indonesia lugas dan akrab dengan sapaan hangat Banda Aceh secukupnya.
   * Frame mentah Google Flow (`360p`) harus bersih tanpa teks bawaan AI; di tahap pasca-produksi (`app/media.py --character bang_ray`), video `360p` otomatis di-upscale ke `1080x1920` dengan **Varian 3 Hybrid Foto-Realistik** (`55% upscayl-lite-4x + 45% Lanczos CAS + micro grain`, `texture_preserve=0.45`), lalu dibakar hardsub 2-tier **`editorial_tiktok`** bebas tanda koma (`Ray_Top` putih `#FFFFFF` Helvetica Neue Bold 44 ALL CAPS `y=1502` + `Ray_Bot` kuning limau `#E8FF3B` Times New Roman 126 `ScaleX=72` lowercase `y=1595`).
   * Strict 0% Emoji pada seluruh caption, tagar, dan metadata.
