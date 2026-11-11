# Panduan storyboard dan prompt video Hermes

PM Intan menyiapkan storyboard dan prompt untuk Flow Operator. Gunakan profil dan foto master karakter yang disahkan. Untuk klip pendek, rancang satu momen yang bisa dipahami dalam sekali lihat. Satu video memakai satu prompt, satu klip, dan satu hasil Flow. Pilih durasi native di model yang tersedia sesuai izin dan slot.

## Tulis storyboard teks dulu (Standar 3-Layer Contextual Hook)

Setiap naskah dan storyboard wajib menggunakan formula **Contextual 3-Layer Hook** (bukan clickbait generik):

1. **Pembuka (0–3 detik):** 
   - *Visual Hook (Detik 0.0s)*: Aksi fisik atau gestur nyata sudah terlihat sejak frame pertama (memegang alat, mengetuk keramik, mengangkat paku, atau mengaduk kuah). Dilarang membuka dengan pose diam melamun.
   - *Text-on-Screen (0–2 detik)*: Judul teks 3–5 kata yang lugas di tengah layar untuk penonton mode hening (mis. *"Penyebab Keramik Meledak"*, *"Uji Kuat Paku Besi"*, *"Rahasia Burgo Juara"*).
   - *Spoken Hook (0–3 detik)*: Kalimat vokal pertama langsung menyebut topik konkret tanpa basa-basi *"halo guys"* atau clickbait generik.
2. **Aksi inti (3–12 detik):** Pilih satu gerakan utama yang mendemonstrasikan solusi masalah. Sebut objek yang disentuh, posisi kamera dan detail ruang yang membantu adegan terasa nyata.
3. **Penutup & CTA (12–15 detik):** Kalimat penutup yang memicu *Save* (*"Simpan video ini..."*), pertanyaan debat komentar, serta struktur *Seamless Loop* yang menyambung kembali ke kalimat awal bila memungkinkan.

Ketiga beat berada dalam satu klip. Ringkas urutannya menjadi satu `shots` entry dengan `seconds` sama dengan durasi slot dan `prompt` berisi arahan utuh. Pembagian detik adalah panduan ritme, bukan permintaan tiga cut atau tiga generasi. Untuk video biasa, storyboard teks sudah cukup. Gunakan frame acuan tambahan jika pembuka, pose akhir, komposisi produk, atau kontinuitas benar-benar bergantung padanya. Utamakan aset yang sudah disahkan. Pembuatan gambar acuan baru mengikuti izin dan anggaran terpisah.

## Ubah storyboard jadi prompt yang bisa direkam

- **Referensi dan framing.** Tentukan referensi identitas yang benar, jarak kamera, tinggi kamera, dan apakah kamera diam atau bergerak. Untuk foto awal yang sudah menentukan visual, fokuskan prompt pada perubahan yang perlu terlihat.
- **Gerak dan reaksi.** Jelaskan urutan yang terlihat. Misalnya tangan meletakkan gelas, es berhenti bergeser, kemudian tatapan kembali ke kamera. Kurangi interaksi tangan, perpindahan benda, atau gerak kamera yang bersaing dalam satu klip.
- **Cahaya, tekstur dan suara.** Gunakan arah cahaya yang masuk akal, warna netral dan tekstur kulit alami sesuai `video_policy.anti_ai_slop_policy` di `config/autopilot.json`. Tulis detail yang bisa diperiksa di hasil, seperti bayangan yang konsisten, pegangan gelas yang stabil dan warna pakaian yang sama. Tentukan ambience atau mode tanpa dialog bila suara karakter belum disahkan. Tambahkan teks layar di editing jika dibutuhkan.
- **Motion Reference.** Jika gerak mengikuti video lain, gunakan Motion Reference Omni Flash di Google Flow. Catat segmen gerak dan master yang akan dipasang. Gunakan `video_policy.motion_reference_policy.video_prompt_template` secara utuh dan tautkan kedua aset pada kontrol Flow. Storyboard teks dipakai untuk menjelaskan bagian referensi dan menilai hasil. Pilih referensi yang cocok dengan gaya visual sebelum menyiapkan prompt agar arahan baru tidak bertentangan dengan gerak, framing, atau pencahayaan referensi. Jika acuan atau mode tidak tersedia, laporkan penghalangnya sebelum generasi.

## Contoh draf Dinda, satu klip 8 detik

| Beat | Yang terlihat |
| --- | --- |
| 0–2 detik | Dari kamera setinggi mata, Dinda sudah terlihat di meja kedai dan meletakkan gelas es kopi di depannya. |
| 2–6 detik | Gelas tetap di meja. Dinda melepaskan pegangan dan melihat sebentar ke gelas. |
| 6–8 detik | Dinda kembali menatap kamera dan tersenyum tipis. |

Contoh prompt untuk aksi orisinal. Pasang foto master Dinda yang sudah disahkan pada Flow sebelum menggunakan prompt.

> Use the attached Dinda master image for identity. Vertical 9:16, one continuous smartphone vlog shot, steady at eye level in a medium shot. Dinda sits at a small coffee stall table near a window. She sets a clear glass of iced coffee on the table, releases her grip, looks down at the glass briefly, then looks back at the camera with a small smile. The glass stays in place. A soft tap of the glass and faint room ambience, with no dialogue. Natural clean daylight from the window, neutral white balance, true-to-life colors, realistic matte human skin with visible fine pores. No plastic shine, waxy skin, glass skin, yellow or orange tint, or artificial golden glow. Zero CGI look. Authentic documentary smartphone footage. Keep her face, clothing and background consistent throughout.

## Periksa sebelum dan sesudah Flow

Sebelum pengajuan generasi, periksa bahwa aksi utamanya terbaca tanpa caption, semua beat muat dalam durasi native, master terpasang sesuai mode dan arah kamera tidak saling bertentangan. Simpan `hook`, `story` dan satu `shots` entry sesuai skema rencana. Pemeriksaan izin, model, biaya dan jumlah hasil mengikuti runbook.

Setelah unduh, tonton klip penuh dan jeda pada awal, kontak tangan dengan objek, dan penutup. Cocokkan identitas dengan master. Cek tangan, benda yang bergeser atau berubah bentuk, wajah/pakaian yang berubah, cahaya berkedip, framing, serta suara. Jika ada cacat yang mengganggu, catat detik dan masalahnya sebagai bahan revisi. Perbaikan prompt berikutnya harus menyasar cacat yang diamati. Jangan mengulang generasi otomatis.

## Template akhir untuk video brand

Siapkan SRT dari audio final. Untuk video tanpa ucapan, beri teks layar singkat
yang mengikuti aksi. Pakai maksimal dua baris per kemunculan. Editor menempatkan
teks putih dengan latar gelap transparan di atas area tombol dan caption platform.
Sesuaikan timing dengan ucapan atau aksi dan cek di ukuran layar ponsel.

Gabungkan isi yang sudah diedit dengan aset penutup yang disahkan untuk brand itu.
Isi video brand maksimal 16 detik. Pilih durasi isi sesuai kebutuhan adegan.
Tiga detik terakhir menampilkan nama atau logo brand dan maksimal satu ajakan
singkat bila sudah disahkan. Gunakan aset penutup yang memang dibuat agar bisa
dipotong ke tiga detik atau ditahan pada frame terakhir.

```bash
python3 -m app.media --input isi.mp4 --subtitles subtitle.srt \
  --outro penutup-brand.mp4 --output final-v1.mp4
```

Berikan satu file isi yang sudah berisi campuran audio final. Jika perlu,
`--duration` memotong isi dari awal sebelum tiga detik penutup ditambahkan.
Durasi final maksimal 19 detik. Setiap cue SRT harus muat utuh di bagian isi.
Editor memakai FFmpeg lokal yang mendukung
subtitle dan mempertahankan audio isi serta penutup bila tersedia. Tonton hasil
akhir, cek nama brand, keterbacaan subtitle, dan penutup pada tiga detik terakhir.
Daftarkan hasil ekspor ini sebagai versi yang akan direview untuk ACC.

Panduan resmi Google tentang [praktik video pendek dan animasi foto](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice), [elemen prompt video](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide), dan [cara membuat video dari referensi di Flow](https://support.google.com/flow/answer/16353334).
