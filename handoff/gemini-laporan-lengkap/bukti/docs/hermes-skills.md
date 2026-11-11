# Skill Hermes — pemasangan 4 November 2026

Sembilan skill unik ditambahkan ke setiap profil ai-influencer-nara/dinda/rania lewat
installer resmi Hermes. hyperframes yang sebelumnya disebut dua kali dihitung sekali.
Dengan hermes-agent yang sudah ada, tiap profil memiliki 10 skill terdaftar.

| Skill | Sumber |
| --- | --- |
| humanizer | bundled Hermes |
| computer-use | bundled Hermes |
| creative-ideation | official/creative/creative-ideation |
| social-media-content-calendar | official/creative/social-media-content-calendar |
| grill-me | official/software-development/grill-me, adaptasi Hermes |
| hyperframes | official/creative/hyperframes, adaptasi Hermes |
| find-skills | skills-sh/vercel-labs/skills/find-skills |
| hyperframes-cli | skills-sh/heygen-com/hyperframes/hyperframes-cli |
| agent-browser | skills-sh/vercel-labs/agent-browser/agent-browser |

Tidak ada runtime, model, checkpoint, paket npm/Python, FFmpeg atau browser yang
diinstal/dijalankan. Node v25.9.0 tersedia; ffmpeg/ffprobe/agent-browser tidak ditemukan
di PATH. Hyperframes dan computer-use belum diuji operasional. Skill adalah panduan
dan berkas pendukung; keberadaannya tidak membuktikan runtime sudah siap.

find-skills dan agent-browser mendapat SAFE dari pemindai. hyperframes-cli mendapat
CAUTION karena dokumentasi AWS opsional, lookup path shell, proxy localhost dan tautan
relatif. Bagian yang ditandai ditinjau pada commit
7e717189c5f89e1bf36a267ecd734eaa608f012c. Pemasangan dilanjutkan dengan --force setelah
review manual, bukan bypass verdict DANGEROUS. Hash empat referensi yang ditinjau cocok
di semua profil. Tidak ada contoh perintah yang dieksekusi.
Audit: operations/reports/hermes-skills/hyperframes-cli-manual-review.json.
Manifest: operations/reports/hermes-skills/installation-verified.json.

Gunakan skill sesuai tugas. Ideation/calendar/humanizer untuk konten; grill-me hanya
untuk permintaan review rencana mendalam, bukan tanya-jawab harian wajib. Izin pemasangan
skill tidak memberi izin menginstal dependensi, menjalankan cloud/AWS/billing, mengirim
feedback/telemetri, mengubah izin browser, atau menjalankan generasi.

Skill terdaftar enabled di library. Toolset CLI/Telegram, launcher, generasi, bot,
publikasi dan jadwal tetap nonaktif. Browser Hermes belum tersambung ke Chrome Mutia.

Melihat daftar dari Terminal tidak memakai model atau memulai produksi:

```bash
hermes -p ai-influencer-nara skills list
hermes -p ai-influencer-dinda skills list
hermes -p ai-influencer-rania skills list
```

Untuk menambahkan skill kelak: periksa dengan `skills inspect IDENTIFIER`, lalu gunakan
`hermes -p NAMA_PROFIL skills install IDENTIFIER`. Jangan memakai --force secara rutin.
