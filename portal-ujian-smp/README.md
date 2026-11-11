# Ruang Ujian SMP — MVP demo

Portal ujian lokal berbahasa Indonesia untuk mencoba alur siswa dan guru. Seluruh akun, kelas, soal bawaan, dan hasil adalah data simulasi; jangan masukkan data pribadi siswa.

## Menjalankan

Perlu Node.js 25 atau lebih baru (mendukung `node:sqlite`). Tidak menggunakan dependency eksternal atau resource jaringan.

```sh
node server.mjs
```

Buka `http://127.0.0.1:3000`. Server hanya bind ke loopback. SQLite membuat `exam.db` pada direktori kerja saat pertama dijalankan; file ini menyimpan akun demo, sesi, dan progres secara persisten. Hapus database secara manual saat ingin mengulang demo.

## Akun demo

- Siswa: kode `SISWA01`, PIN `1234` (kelas simulasi 8A).
- Guru: kode `GURU01`, PIN `1234`.

Aplikasi menyiapkan satu ujian demo berisi 20 soal matematika SMP orisinal dan membuka jendela ujian selama 24 jam sejak database pertama dibuat. Siswa dapat mengulang latihan dengan umpan balik langsung. Ujian memiliki batas waktu server, penyimpanan jawaban, navigasi dan tanda soal, pengiriman ulang jawaban lokal saat koneksi kembali, pengumpulan idempoten, dan penutupan otomatis saat tenggat.

Guru dapat menambah soal pilihan ganda dengan empat opsi dan satu kunci, membuat jadwal dari ID soal bank, melihat progres akun demo, merilis hasil, dan mengunduh CSV dengan BOM agar terbaca baik di Excel. Jadwal menyimpan snapshot soal saat dibuat.

## Batas MVP

Import XLSX belum tersedia; saat ini guru menambahkan soal satu per satu melalui form. Manajemen sekolah/admin (pembuatan akun, kelas, dan izin) belum tersedia. Belum ada load trial atau jaminan kapasitas produksi. Belum ditujukan untuk penggunaan sekolah nyata, data sensitif, atau akses dari jaringan; gunakan akun demo saja.