# Panduan Standar Produksi Video AI ISK — Paku Cap Keris
Akun Resmi: @intansuarkartika | PT Intan Suar Kartika

Dokumen ini adalah SOP tunggal yang sah untuk seluruh produksi video iklan komersial dan soft-selling PT Intan Suar Kartika.
Dilarang menggunakan skrip slide statis FFmpeg, dubbing eksternal TTS terpisah, atau pemotongan outro di luar panduan ini.

---

## 1. Prinsip Utama Pembuatan Video

1. **AI Video Generatif Live-Action Murni (Google Flow):**
   * Seluruh adegan video dihasilkan secara murni melalui Google Flow (Gemini Omni Flash) dalam rasio vertikal 9:16 (720x1280 atau 1080x1920).
   * Dilarang membuat video slide gambar diam dengan teks overlay FFmpeg drawtext.
2. **Audio & Dialog Native di Flow:**
   * Dialog dan efek suara dihasilkan secara langsung di dalam Google Flow melalui instruksi prompt (dialog dalam tanda kutip).
   * Dialog menggunakan bahasa Indonesia natural dengan artikulasi jelas dan sinkronisasi bibir (*lip-sync*) yang presisi.
   * Tidak menggunakan dubbing narator eksternal (Edge-TTS / ElevenLabs) untuk konten video AI utama.
3. **Visual Bersih Tanpa Subtitle Bakar:**
   * Layar visual video harus 100% bersih dari subtitle bakar (*burned-in subtitles*), judul teks buatan, watermark, atau label storyboard.
   * Seluruh pesan verbal disampaikan lewat audio dialog karakter.
4. **Acuan Kemasan Kardus Paku Cap Keris:**
   * Menggunakan acuan visual foto asli tunggal: `characters/isk/assets/brand/paku_cap_keris_box_reference.jpg`.
   * Ciri fisik wajib: Kardus kraft cokelat persegi panjang horizontal, cetakan hijau tua bertuliskan PAKU EXPORT QUALITY, lambang keris, simbol tiga paku, SNI No. 0194 - 78, PRODUKSI P.T. INTAN SUAR KARTIKA MEDAN-INDONESIA.
   * **Kondisi Paku:** Paku baja curah lepas langsung di dalam kardus, TANPA BUNGKUS PLASTIK.
   * Saat kardus bergerak dalam video, kamera menyorot bagian dalam atau sisi polos kardus untuk mencegah distorsi teks merek.

---

## 2. Struktur Durasi dan Storyboard

### Pola 1 Klip (10 Detik Flow + 4.07 Detik Outro = Total 14.07 Detik)
* **0–3 detik (Hook):** Masalah kuat atau pertanyaan yang menarik perhatian dalam 3 detik pertama (misal: paku murahan langsung bengkok saat dipukul palu).
* **3–5 detik (Reaksi):** Ekspresi kekecewaan atau perbandingan langsung terhadap mutu bahan.
* **5–9 detik (Aksi Utama):** Membuka kardus Paku Cap Keris asli, memperlihatkan paku baja kokoh tanpa bungkus plastik, atau memukul paku hingga menancap lurus sempurna. Dialog keunggulan produk disampaikan di sini.
* **9–10 detik (Frame Akhir):** Pose akhir tertahan dengan produk atau hasil kerja terlihat jelas.

### Pola 2 Klip (20 Detik Flow + 4.07 Detik Outro = Total 24.07 Detik)
* **Klip 1 (10 detik):** Hook awal, perkenalan masalah, membuka kardus Paku Cap Keris, dan mengambil paku. Klip berakhir pada frame tertahan (hold).
* **Klip 2 (10 detik):** Dimulai dari frame terakhir bersih dari Klip 1 sebagai gambar awal (*start frame*) untuk menjaga kontinuitas visual 100%. Melanjutkan aksi menancapkan paku, menguji kekokohan kayu, dan memberikan senyuman kepuasan.

---

## 3. Outro Bumper Resmi PT Intan Suar Kartika

* **Berkas Master Outro:** `characters/isk/assets/brand/outro_keris_isk.mp4`
* **Durasi Wajib:** **4.0667 detik (122 frame pada 30 fps)**.
* **Resolusi:** 1080x1920 (Full HD Vertikal).
* **Aturan Keras:**
  * DILARANG MEMOTONG OUTRO MENJADI 3 DETIK.
  * Durasi penuh 4.07 detik wajib dipertahankan agar animasi logo 3D, kontak WhatsApp resmi (`wa.me/62819889350`), dan sound tag penutup terdengar utuh sempurna.

---

## 4. Template Prompt Google Flow Resmi

```text
Generate a photorealistic live-action video, vertical 9:16, exactly 10 seconds. Use the uploaded clean scene image as the first frame. Use a fixed medium shot in natural daylight workshop.

An Indonesian male carpenter in a navy work shirt is working at a wooden workbench. On the table sits a loose wooden plank, a hammer, and an open carton of Paku Cap Keris matching the reference photo. Inside the brown kraft carton, bulk steel nails lie loose directly without plastic packaging.

0–3 seconds. The carpenter strikes a cheap bent nail, stops in frustration, inspects the bent nail, and says, "Paku murahan baru dihantam langsung bengkok? Waktunya ganti standar mutu ekspor!"
3–5 seconds. He tosses the bent nail aside, reaches out toward the open Paku Cap Keris box on the table.
5–9 seconds. He picks up a straight, sturdy Paku Cap Keris nail, displays it proudly, pointing at the clean steel shank.
9–10 seconds. He positions the nail tip onto the hardwood plank, hammer raised ready to strike. Hold this final position cleanly.

Natural Indonesian dialogue with realistic lip sync and clear audio. Keep the dialogue audio-only and the full-screen image completely clean of subtitles, text, and storyboard labels.
```

---

## 5. Ringkasan Validasi Video Siap Tayang

1. Klip Flow terverifikasi memiliki audio dialog dan lip-sync natural.
2. Kardus cokelat kraft Paku Cap Keris akurat, paku lepas tanpa plastik.
3. Sambungan outro master berdurasi 4.07 detik menempel mulus di akhir adegan.
4. Total durasi adalah ~14.07 detik (1 klip) atau ~24.07 detik (2 klip).
5. Tidak ada teks bakar / subtitle yang merusak frame video.
