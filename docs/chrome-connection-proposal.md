> Pembaruan 4 November 2026: usulan di bawah sudah disetujui pengguna, konektor
> 1.12.0 dipasang dan profil Dinda dikonfigurasi. Uji baca MCP lulus; model Hermes
> belum diuji memakai browser. Catatan di bawah merupakan kondisi sebelum pemasangan.
> Bukti: operations/reports/hermes-flow-connection-test.json.

# Sambungan Chrome Mutia → Hermes (belum aktif)

Masalah yang terlihat: chrome://inspect/#remote-debugging pada Chrome Mutia (FLOW)
menampilkan Allow remote debugging for this browser instance dalam keadaan mati.
Halaman pemeriksaan sudah dibuka di tab baru; tab proyek Dinda tetap ada.

Usulan: konektor resmi ChromeDevTools/chrome-devtools-mcp versi 1.12.0 dari npm,
terhubung lewat autoConnect ke Chrome yang berjalan. Tidak membuat snapshot atau
menyalin cookie/login dan tidak membutuhkan login Flow baru. Keberhasilan memilih
instance/profil yang benar tetap harus dibuktikan dengan pembacaan halaman Flow.

Rencana konfigurasi di config/hermes-chrome-connection.proposed.json belum dimasukkan
ke config Hermes. Tidak ada paket atau MCP server yang dipasang/dijalankan, checkbox
Chrome belum disentuh, toolset produksi tetap mati. Node saat ini memenuhi deklarasi
engine npm; kompatibilitas aktual konektor belum diuji.

Izin Chrome yang diminta memberi aplikasi yang disetujui kendali browser dan akses
data tersimpan/cookie/data situs; cakupannya lebih luas daripada satu tab Flow. Chrome
juga akan menampilkan dialog persetujuan ketika konektor meminta sambungan.

Uji pertama dibatasi pada daftar halaman, memilih tab Dinda yang sudah ada, lalu membaca
snapshot. Allowlist tools sisi Hermes hanya list_pages/select_page/take_snapshot;
ini membatasi alat model, bukan mempersempit kemampuan teknis konektor/izin Chrome.
Statistik penggunaan, pemeriksaan update dan layanan performa CrUX dinonaktifkan pada
rencana konfigurasi. Tidak ada analisis jaringan, penyalinan token atau pembacaan chat lain.

Pemasangan konektor dan aktivasi izin Chrome memerlukan persetujuan pengguna karena
belum tercakup izin memasang skill. Setelah disetujui, validasi opsi --help dan uji
sambungan sebelum menyatakan akun Flow terhubung ke Hermes. Generasi, bot, jadwal
dan publikasi tetap nonaktif; tidak ada izin memakai kredit dari persetujuan koneksi.
