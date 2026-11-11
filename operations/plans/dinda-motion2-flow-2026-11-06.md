# Paket Eksekusi — Dinda x Motion Ref 2

**Dibuat:** 6 Nov 2026 · PM

## Input
- Identitas: `FOTO_KARAKTER/Dinda/_Kemala_Three-Expression_Reference_Sheet-1.png_ccfbeaff.jpg` (sha256 a1e87219...2ec8d6, master terpilih)
- Tubuh: `FOTO_KARAKTER/Dinda/dinda.jpg`
- Motion: `shared/motion_references/reference_motion_2.mp4` (10s, sha256 57e87492...47d48)
- Model: Omni Flash · 9:16 · 1 hasil/generasi
- Perkiraan biaya: ~10 kredit (flow_1 Dinda, saldo terverifikasi 458)

## Prompt (siap tempel di Flow)
> Use the master reference image for face and body identity.
> Vertical 9:16, single continuous take, static camera at eye level, medium close-up, plain olive wall background.
> Subject faces camera and counts items on her fingers: both hands open wide at the start, then extends one finger at a time near the chest,
> small head nods per item, playful expression, hands always within frame.
> Match the motion timing of the uploaded motion reference. No cuts, photoreal, soft indoor key light, 30 fps feel.

## Status Gate & Browser
1. **Gate ACC:** DIBUKA (Owner memberikan izin eksplisit via Telegram: "Generate vidio itu sebagai motion referensenya dinda").
2. **Browser:** TERHUBUNG ke Chrome Automation port `9333` (akun Mutia Kiting aktif dan login).

## Langkah Eksekusi (Aktif)
1. Buka project `3e9fe2ca-ee39-4235-81a1-9d8bfdee9603` di browser port 9333.
2. Anonymize video sumber `reference_motion_2.mp4` via `anonymize_motion_ref.py`.
3. Upload `reference_motion_2_anonymized.mp4` + Master Dinda ke Flow.
4. Trim durasi di timeline slider Flow (10.0 detik) atau pilih opsi 10s Omni Flash 9:16.
5. Tempel prompt dan klik Start generation.
6. Unduh MP4 dan kirim ke Telegram.
