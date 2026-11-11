# Panduan Kreatif Multi-Produk PT Intan Suar Kartika (ISK)
Akun Resmi: @intansuarkartika | PT Intan Suar Kartika

Panduan ini mengatur standar produksi visual, acuan produk resmi, dan formula naskah untuk 4 lini produk utama PT Intan Suar Kartika berdasarkan temuan data analitik performa akun TikTok Studio.

---

## 1. Katalog Acuan Produk Resmi (Brand Reference Assets)

| Produk | Berkas Acuan Visual | Ciri Fisik Wajib (Visual Anchor) |
|---|---|---|
| **Kawat Duri Diamond** | `characters/isk/assets/brand/kawat_duri_diamond_reference.jpg` | Roll silinder kawat galvanis berkilau rapi; label oval kayu/karton bertuliskan **BARBED IRON WIRE**, cap merah logo roda gigi **INI** dan simbol **DIAMOND**, kolom `BWG#` dan `WEIGHT KGS.` |
| **Kereta Sorong Five Star** | `characters/isk/assets/brand/kereta_sorong_five_star_angle.jpg`<br>`characters/isk/assets/brand/kereta_sorong_five_star_top.jpg` | Bak plat baja press tebal merah cerah glossy; rangka pipa merah dengan bemper lengkung pelindung depan; stiker putih **FIVE STAR** di handle pipa kiri; grip karet hitam; roda ban angin tebal berulir. |
| **Paku Cap Keris** | `characters/isk/assets/brand/paku_cap_keris_box_reference.jpg` | Kardus kraft cokelat persegi panjang horizontal; tipografi hijau tua **PAKU EXPORT QUALITY**, ilustrasi keris, **CAP KERIS**, SNI No. 0194 - 78, PRODUKSI P.T. INTAN SUAR KARTIKA MEDAN-INDONESIA; paku curah lepas tanpa bungkus plastik. |
| **Kawat Licin Diamond** | `characters/isk/assets/brand/kawat_licin_diamond_reference.jpg` | Roll kawat baja galvanis halus mengkilap, lilitan rapi anti-karat, ulet dan lentur saat ditekuk tang catut. |

---

## 2. Struktur Formula Produksi (Input Flow 360p, Maksimal 20 Detik Total per Video, 1x Posting/Hari)

* **0–3 detik (Contextual 3-Layer Hook & Visual Anchor):**
  - *Visual (0.0s)*: Objek material fisik (kawat duri, kereta dorong, atau kardus paku) sudah terlihat disentuh/dipegang tangan sejak awal.
  - *Text-on-Screen*: Judul 3–5 kata tegas di tengah layar (mis. *"Uji Beban Paku Besi"* atau *"Pagar Kebun Anti Jebol"*).
  - *Spoken Hook*: Menyebut langsung masalah nyata lapangan (*"Banyak yang tergiur paku murah kiloan, pas dipukul tiga kali langsung meleyot. Kita tes langsung..."*). Bebas dari clickbait klise.
* **3–15 detik (Uji Ketahanan & Edukasi Solutif):** Menunjukkan keunggulan material produk resmi ISK secara visual, lalu diakhiri ajakan Save (*"Simpan video ini buat acuan belanja material proyek kamu"*).
* **Bumper Penutup Resmi Master (4.07 detik):** Concat 4.07 detik utuh `characters/isk/assets/brand/outro_keris_isk.mp4` sebagai penutup master baku untuk seluruh produk ISK (total video final bersama outro maksimal **20 detik**, misalnya klip utama `7–15` detik + outro `4.07` detik = `11.07–19.07` detik).
* **Aturan Kontinuitas Properti (Anti-Barang Muncul & Hilang):** Seluruh produk ISK & alat bantu dalam satu klip WAJIB sudah berada di frame sejak detik `0.0s` dan tidak boleh tiba-tiba muncul atau menghilang di tengah klip (`only named props visible from start to end; no sudden appearance or disappearance of objects`). Periksa frame awal-tengah-akhir sebelum registrasi versi.
* **Pasca-Produksi Wajib:** Frame mentah Flow `360p` bebas teks AI; otomatis di-upscale ke `1080x1920` memakai **Varian 3 Hybrid Foto-Realistik** (`55% upscayl-lite-4x + 45% tekstur asli CAS + grain`, `texture_preserve=0.45`), lalu ekstraksi audio Faster-Whisper alignment dan burning subtitle 2-tier terpadu **`editorial_tiktok`** tanpa tanda koma (`Ray_Top` `#FFFFFF` Helvetica Neue Bold 44 ALL CAPS + `Ray_Bot` `#E8FF3B` Times New Roman 126 `ScaleX=72` lowercase) via `app/subtitles.py` & `app/media.py --character isk` sebelum sambung outro dan kirim review Telegram.

---

## 3. Matriks Skenario Siap Render per Produk

### Skenario 1: Kawat Duri Diamond — Pagar Kebun Sawit & Batas Lahan (Top Views)
* **Target Masalah:** Kebun sawit sering diserobot atau dimasuki ternak liar/pencuri buah.
* **Hook Dialog (0–3s):** *"Batas kebun jelas bukan buat musuhan, tapi buat lindungi hasil panen!"* (9 kata)
* **Caption Resmi (0% Emoji):** *Amankan investasi kebun sawit dan batas lahan Anda dengan Kawat Duri Diamond dari PT Intan Suar Kartika. Baja galvanis anti-karat dengan lilitan duri ekstra tajam dan kencang. Pemesanan distributor langsung via WhatsApp wa.me/62819889350. #kawatduridiamond #pagarkebun #kebunsawit #intansuarkartika*

### Skenario 2: Kereta Sorong Five Star — Uji Beban Proyek 200 KG
* **Target Masalah:** Gerobak dorong murah yang as rodanya bengkok atau bak platnya meleyot saat muat batu kali dan adukan semen basah.
* **Hook Dialog (0–3s):** *"Kereta dorong kaleng-kaleng baru muat batu sedikit rodanya sudah goyang!"* (10 kata)
* **Caption Resmi (0% Emoji):** *Kerja berat di proyek dan perkebunan butuh armada tangguh. Kereta Sorong Five Star dari PT Intan Suar Kartika, bak baja tebal anti-penyok dengan ban angin kokoh di segala medan. Pemesanan distributor langsung via WhatsApp wa.me/62819889350. #keretasorongfivestar #alatproyek #tokobangunan #intansuarkartika*

### Skenario 3: Paku Cap Keris — Penetrasi Balok Kayu Keras (Bukan Timbangan)
* **Target Masalah:** Paku biasa sering bengkok atau melintir patah saat dipukul ke dalam balok kayu ulin/kamper tebal untuk kuda-kuda atap.
* **Hook Dialog (0–3s):** *"Kerja kayu keras jangan pakai paku biasa kalau nggak mau patah di tengah!"* (11 kata)
* **Caption Resmi (0% Emoji):** *Konstruksi atap dan kayu keras butuh paku tangguh anti-bengkok. Paku Cap Keris mutu baja ekspor dari PT Intan Suar Kartika, tembus serat kayu padat dengan lurus dan kokoh. Pemesanan distributor langsung via WhatsApp wa.me/62819889350. #pakucapkeris #tukangkayu #proyekkonstruksi #intansuarkartika*

### Skenario 4: Kawat Licin Diamond — Tulangan Besi Cor Proyek
* **Target Masalah:** Kawat bendrat/ikat murah yang getas dan putus saat diputar tang catut, memperlambat pengecoran kolom tiang.
* **Hook Dialog (0–3s):** *"Kawat ikat gampang putus bikin kerjaan cor tiang jadi lambat!"* (9 kata)
* **Caption Resmi (0% Emoji):** *Rangka tulangan tiang cor beton lebih kokoh dan cepat selesai dengan Kawat Licin Diamond dari PT Intan Suar Kartika. Ulet, lentur, dan tidak mudah putus saat ditarik kencang. Pemesanan distributor langsung via WhatsApp wa.me/62819889350. #kawatlicindiamond #kawatikat #besicor #intansuarkartika*
