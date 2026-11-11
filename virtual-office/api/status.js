// Vercel Serverless Function - AI Office Status API
const officeSnapshot = {
  "characters": [
    {
      "id": "nara",
      "name": "Nara Adelia",
      "account": "@nara.adelia_"
    },
    {
      "id": "dinda",
      "name": "Dinda Kemala",
      "account": "@dinda.kemala_"
    },
    {
      "id": "rania",
      "name": "Rania Meutia",
      "account": "@rania.meutia"
    },
    {
      "id": "aqara",
      "name": "Aqara Indonesia",
      "account": "@aqara.indonesia"
    },
    {
      "id": "isk",
      "name": "PT Intan Suar Kartika",
      "account": "@intansuarkartika"
    }
  ],
  "stats": {
    "total_jobs": 20,
    "completed_jobs": 18,
    "credits_used": 201,
    "total_approved": 6,
    "flow_credits_remaining": 458
  },
  "recent_jobs": [
    {
      "id": "job_isk_pk005_banting_tang",
      "character_id": "isk",
      "model": "Omni 1.2 Flash",
      "state": "completed",
      "actual_credits": 20,
      "created_at": "2026-11-09T08:42:00Z"
    },
    {
      "id": "job_isk_clip2_1794209517028",
      "character_id": "isk",
      "model": "Omni 1.2 Flash",
      "state": "running",
      "actual_credits": null,
      "created_at": "2026-11-09T07:31:57.028Z"
    },
    {
      "id": "job_recon_9nov_pagi",
      "character_id": "dinda",
      "model": "Omni 1.1 Flash",
      "state": "completed",
      "actual_credits": 10,
      "created_at": "2026-11-09T07:19:00+00:00"
    },
    {
      "id": "job_isk_clip1_1794208637596",
      "character_id": "isk",
      "model": "Omni 1.2 Flash",
      "state": "running",
      "actual_credits": null,
      "created_at": "2026-11-09T07:17:17.596Z"
    },
    {
      "id": "job_isk_clip1_1794204245900",
      "character_id": "isk",
      "model": "Omni 1.2 Flash",
      "state": "completed",
      "actual_credits": 24,
      "created_at": "2026-11-09T06:04:05.900Z"
    },
    {
      "id": "job_recon_8nov_malam",
      "character_id": "dinda",
      "model": "Omni 1.1 Flash",
      "state": "completed",
      "actual_credits": 12,
      "created_at": "2026-11-08T19:45:00+00:00"
    }
  ],
  "recent_approvals": [
    {
      "id": "app_nov9_pagi",
      "decision": "approved",
      "reviewer_id": "7463982122",
      "channel": "telegram",
      "created_at": "2026-11-09T02:35:00+00:00"
    },
    {
      "id": "app_nov8_malam",
      "decision": "approved",
      "reviewer_id": "7463982122",
      "channel": "telegram",
      "created_at": "2026-11-08T19:45:00+00:00"
    },
    {
      "id": "app_nov8_pagi",
      "decision": "approved",
      "reviewer_id": "7463982122",
      "channel": "telegram",
      "created_at": "2026-11-08T07:20:00+00:00"
    },
    {
      "id": "396c68db3fa945a9852e0126734985d1",
      "decision": "approved",
      "reviewer_id": "owner_autonomous_mode",
      "channel": "telegram",
      "created_at": "2026-11-07T12:21:34.681834+00:00"
    },
    {
      "id": "d5bd7967115247cd8cd1c3aa3dd5324b",
      "decision": "approved",
      "reviewer_id": "7463982122",
      "channel": "telegram",
      "created_at": "2026-11-07T06:29:49.995704+00:00"
    }
  ],
  "active_renders": [
    {
      "id": "job_isk_clip1_1794208637596",
      "character_id": "isk",
      "flow_account_id": "flow_2",
      "idempotency_key": "isk_pk004_clip1_job_isk_clip1_1794208637596",
      "state": "running",
      "model": "Omni 1.2 Flash",
      "duration_seconds": 10,
      "output_count": 1,
      "authorized_credits": 24,
      "actual_credits": null,
      "external_job_id": null,
      "created_at": "2026-11-09T07:17:17.596Z"
    },
    {
      "id": "job_isk_clip2_1794209517028",
      "character_id": "isk",
      "flow_account_id": "flow_2",
      "idempotency_key": "isk_pk004_clip2_job_isk_clip2_1794209517028",
      "state": "running",
      "model": "Omni 1.2 Flash",
      "duration_seconds": 10,
      "output_count": 1,
      "authorized_credits": 24,
      "actual_credits": null,
      "external_job_id": null,
      "created_at": "2026-11-09T07:31:57.028Z"
    }
  ],
  "pending_accs": [
    {
      "id": "7e0fdc35704e461194d07c77de5cb59d",
      "version_id": "ver_isk_isk_pk_001_1794198120",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T04:36:18.675267+00:00",
      "caption": "Pekerjaan konstruksi butuh material yang presisi dan tidak gampang bengkok. Paku Cap Keris hadir dengan jaminan timbangan pas 25 kg dan standar mutu ekspor. Komentar KATALOG untuk mendapatkan tautan WhatsApp pemesanan langsung lewat DM.",
      "media_path": "characters/isk/content/ISK_PK_001/ISK_PK_001_final_18s.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "2c8cb71c7adf44b2914c24fc0aa1c5a8",
      "version_id": "ver_isk_isk_pk_001_rev3_1794199758",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T04:49:24.623262+00:00",
      "caption": "Pekerjaan konstruksi butuh material yang presisi dan tidak gampang bengkok. Paku Cap Keris hadir dengan jaminan timbangan pas 25 kg dan standar mutu ekspor. Komentar KATALOG untuk mendapatkan tautan WhatsApp pemesanan langsung lewat DM.",
      "media_path": "characters/isk/content/ISK_PK_001/ISK_PK_001_final_18s.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "d1550ef2cdc44512b0223e3d82708496",
      "version_id": "ver_rania_rania_soft_001_rev1_1794202020",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T05:27:00.233154+00:00",
      "caption": "Rania Meutia - Rak dari Zaman SD. Pekerjaan rapi dan konstruksi kokoh selalu berawal dari paku bermutu ekspor. Paku Cap Keris dari PT Intan Suar Kartika, timbangan pas 25 kg dan batang kokoh anti bengkok. Hubungi WhatsApp wa.me/62819889350 untuk pasokan proyek atau toko bangunan Anda.",
      "media_path": "characters/rania/content/RANIA_SOFT_001/RANIA_SOFT_001_final_24s.mp4",
      "destination_account": "@rania.meutia"
    },
    {
      "id": "16ea39f4cd7f40b095707ac063f9aa76",
      "version_id": "ver_isk_isk_pk_002_rev1_1794202954",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T05:43:15.009795+00:00",
      "caption": "Pekerjaan proyek atau konstruksi sering tertunda gara-gara paku gampang bengkok? Jangan buang waktu dan biaya. Pakai Paku Cap Keris dari PT Intan Suar Kartika! Batang kokoh presisi standar mutu ekspor dan jaminan timbangan pas 25 kg murni. Hubungi WhatsApp wa.me/62819889350 untuk pasokan langsung toko bangunan dan proyek Anda. #intansuarkartika #pakucapkeris #tokobangunan #kontraktor #tukangkayu #bahanbangunan",
      "media_path": "characters/isk/content/ISK_PK_002/ISK_PK_002_final_20s.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "fbacf7aa900844a592385a4579cf28c0",
      "version_id": "ver_isk_isk_pk_002_rev2_1794204562",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T06:09:22.942479+00:00",
      "caption": "Paku murahan baru dihantam langsung bengkok? Waktunya ganti ke standar mutu ekspor! Paku Cap Keris dari PT Intan Suar Kartika, batang baja kokoh anti bengkok dan jaminan timbangan pas 25 kg murni. Pasokan aman untuk toko bangunan, kontraktor, dan tukang kayu. Pemesanan via WhatsApp wa.me/62819889350! #intansuarkartika #pakucapkeris #tokobangunan #kontraktor #tukangkayu #bahanbangunan",
      "media_path": "characters/isk/content/ISK_PK_002/ISK_PK_002_flow_native_final.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "32ae4f6606d54f8880ac77b24a9c2ed5",
      "version_id": "126d56cb4f39498a9383c54fbe3ce0f0",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T06:34:34.623402+00:00",
      "caption": "Kenali kemasan Paku Cap Keris dari tulisan PAKU hijau tua, simbol keris, dan nama PT Intan Suar Kartika di bagian depan.",
      "media_path": "characters/isk/content/ISK_PK_003/ISK_PK_003_kenali_kardus_paku_cap_keris.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "c560b868ebd14b2dbaa6c290ff34e154",
      "version_id": "ver_isk_isk_pk_004_rev4_1794214186",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T08:49:46Z",
      "caption": "Rahasia mandor proyek selalu balik belanja: Paku Cap Keris jaminan timbangan pas 25 kg dan baja kokoh anti bengkok. Pemesanan via WA 08198889350 (wa.me/628198889350). #pakucapkeris #intansuarkartika #bahanbangunan",
      "media_path": "characters/isk/content/ISK_PK_004/ISK_PK_004_toko_material_final.mp4",
      "destination_account": "@intansuarkartika"
    },
    {
      "id": "0d62fd12cefc40cca82e256eb859991e",
      "version_id": "ver_isk_isk_pk_005_rev2_1794214177",
      "chat_id": 7463982122,
      "state": "sent",
      "created_at": "2026-11-09T08:49:37Z",
      "caption": "Paku baru dihantam sekali langsung bengkok? Pakai Paku Cap Keris dari PT Intan Suar Kartika, batang baja kokoh anti bengkok dan timbangan pas 25 kg. Pemesanan via WA 08198889350 (wa.me/628198889350). #pakucapkeris #intansuarkartika #tokobangunan",
      "media_path": "characters/isk/content/ISK_PK_005/ISK_PK_005_banting_tang_final.mp4",
      "destination_account": "@intansuarkartika"
    }
  ],
  "active_publications": [
    {
      "id": "897b7e9d7a1c43b09d11e1ab413f3fd0",
      "version_id": "ver_isk_isk_pk_004_rev4_1794214186",
      "content_id": "isk_isk_pk_004",
      "account": "@intansuarkartika",
      "post_url": "https://www.tiktok.com/@intansuarkartika/video/7706094288249097524",
      "state": "confirmed",
      "confirmed_at": "2026-11-09T09:07:08Z"
    },
    {
      "id": "870e20692a5f4cec9c7b2ea5a492bc05",
      "version_id": "ver_isk_isk_pk_005_rev2_1794214177",
      "content_id": "isk_isk_pk_005",
      "account": "@intansuarkartika",
      "post_url": "https://www.tiktok.com/@intansuarkartika/video/7706091935244635398",
      "state": "confirmed",
      "confirmed_at": "2026-11-09T09:01:01Z"
    }
  ],
  "department_states": {
    "pm": {
      "state": "active",
      "task": "Jadwal Aktif: Produksi 06:00 WIB • Spare ACC 2 Jam • Posting 08:00 WIB",
      "badge": "⏰ 06:00 - 08:00 WIB"
    },
    "flow": {
      "state": "standby",
      "task": "Render Selesai: ISK_PK_005 (Hook Banting Tang)",
      "badge": "\u2713 SELESAI"
    },
    "dinda": {
      "state": "standby",
      "task": "Memantau Komentar & DM TikTok",
      "badge": "\u25cf AKTIF MEDSOS"
    },
    "nara": {
      "state": "standby",
      "task": "Standby \u2022 Target Riset Konten Pagi",
      "badge": "\u25cf AKTIF MEDSOS"
    },
    "rania": {
      "state": "standby",
      "task": "Standby \u2022 Menjawab DM Budaya Aceh",
      "badge": "\u25cf AKTIF MEDSOS"
    },
    "trend": {
      "state": "completed_recent",
      "task": "Riset Terkirim: POV: 5 Menit Morning Glow & Office Ready Medan",
      "badge": "\u2713 RISET SELESAI"
    }
  },
  "office": {
    "checked_at": "2026-11-09T08:06:56.695729+00:00",
    "agents": [
      {
        "name": "PM Intan",
        "short_name": "PM Intan",
        "role": "Koordinasi & arahan",
        "group": "Dapur produksi",
        "initials": "PI",
        "room": "01",
        "description": "Menyusun brief, membagi tugas, dan memeriksa hasil sebelum dibawa ke pemilik.",
        "responsibilities": [
          "Perencanaan dan brief konten",
          "Koordinasi researcher dan talent",
          "Pemeriksaan paket untuk persetujuan"
        ],
        "id": "pm",
        "profile": "ai-influencer-pm",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Siap internal",
        "stage": "Koordinasi lulus uji",
        "checks": [
          {
            "label": "Pembagian tugas",
            "value": "Lulus uji"
          },
          {
            "label": "Pembacaan hasil",
            "value": "Lulus uji"
          },
          {
            "label": "Produksi rutin",
            "value": "Belum aktif"
          }
        ],
        "limitation": "Persetujuan konten tidak otomatis mengaktifkan publikasi, pembelian, atau generasi baru."
      },
      {
        "name": "Researcher",
        "short_name": "Researcher",
        "role": "Riset & penulisan",
        "group": "Dapur produksi",
        "initials": "RS",
        "room": "02",
        "description": "Memeriksa sumber publik dan menyiapkan temuan, hook, serta draf caption untuk PM.",
        "responsibilities": [
          "Riset dan pemeriksaan sumber",
          "Brief tren dan kandidat sound",
          "Draf hook dan caption"
        ],
        "id": "researcher",
        "profile": "ai-influencer-researcher",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Siap internal",
        "stage": "Brief publik lulus uji",
        "checks": [
          {
            "label": "Sumber publik",
            "value": "Lulus uji"
          },
          {
            "label": "Serah terima ke PM",
            "value": "Lulus uji"
          },
          {
            "label": "Tren & sound TikTok",
            "value": "Perlu validasi lanjutan"
          }
        ],
        "limitation": "Brief riset historis bukan bukti bahwa agen sedang melakukan riset saat ini."
      },
      {
        "name": "Dinda Kemala",
        "short_name": "Dinda",
        "role": "Talent \u00b7 Palembang",
        "group": "Studio talent",
        "initials": "DK",
        "room": "03",
        "description": "Talent daily vlog, lifestyle, dan kuliner Palembang. Pilot konten sudah melewati review dan ACC.",
        "responsibilities": [
          "Konten sesuai identitas Dinda",
          "Balasan DM dan komentar dalam sesi manual",
          "Pemeriksaan paket sebelum publikasi"
        ],
        "id": "dinda",
        "profile": "ai-influencer-dinda",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Siap internal",
        "stage": "Pilot konten berhasil",
        "checks": [
          {
            "label": "Generate & download",
            "value": "Lulus uji"
          },
          {
            "label": "DM & komentar manual",
            "value": "Lulus uji"
          },
          {
            "label": "Adapter kirim baru",
            "value": "Belum diuji langsung"
          }
        ],
        "limitation": "Publikasi tetap memerlukan paket final, ACC yang sesuai, dan izin publikasi terpisah."
      },
      {
        "name": "Nara Adelia",
        "short_name": "Nara",
        "role": "Talent \u00b7 Medan",
        "group": "Studio talent",
        "initials": "NA",
        "room": "04",
        "description": "Talent beauty, GRWM, dan keseharian bekerja di Medan. Pengujian produksi masih menunggu.",
        "responsibilities": [
          "Konten beauty dan GRWM",
          "Gaya kantor dan keseharian Medan",
          "Menjaga konsistensi identitas Nara"
        ],
        "id": "nara",
        "profile": "ai-influencer-nara",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Siap internal",
        "stage": "Uji produksi menunggu",
        "checks": [
          {
            "label": "Model",
            "value": "Lulus uji"
          },
          {
            "label": "Tugas lokal",
            "value": "Lulus uji"
          },
          {
            "label": "Browser & produksi",
            "value": "Belum diuji"
          }
        ],
        "limitation": "Akses browser dan akun Flow belum lulus uji produksi. Jadwal rutin belum aktif."
      },
      {
        "name": "Rania Meutia",
        "short_name": "Rania",
        "role": "Talent \u00b7 Aceh",
        "group": "Studio talent",
        "initials": "RM",
        "room": "05",
        "description": "Talent wisata alam, hidden gems, dan kuliner wisata Aceh dengan modest travel look.",
        "responsibilities": [
          "Wisata alam dan destinasi Aceh",
          "Kuliner di sekitar tempat wisata",
          "Menjaga konsistensi identitas Rania"
        ],
        "id": "rania",
        "profile": "ai-influencer-rania",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Siap internal",
        "stage": "Uji produksi menunggu",
        "checks": [
          {
            "label": "Model",
            "value": "Lulus uji"
          },
          {
            "label": "Tugas lokal",
            "value": "Lulus uji"
          },
          {
            "label": "Browser & produksi",
            "value": "Belum diuji"
          }
        ],
        "limitation": "Akses browser dan akun Flow belum lulus uji produksi. Jadwal rutin belum aktif."
      },
      {
        "name": "Agent Sales",
        "short_name": "Sales",
        "role": "Penjualan toko",
        "group": "Operasional",
        "initials": "SL",
        "room": "06",
        "description": "Menyiapkan konsultasi produk, draf penawaran dan pesanan, serta ringkasan prospek.",
        "responsibilities": [
          "Konsultasi dan rekomendasi produk",
          "Draf penawaran dan pesanan",
          "Penyerahan ke sales manusia"
        ],
        "id": "sales",
        "profile": "sales-toko",
        "model": "deepseek-chat",
        "runtime": "offline",
        "runtime_label": "Gateway tidak melayani",
        "stage": "WhatsApp ditunda",
        "checks": [
          {
            "label": "Setup agen",
            "value": "Selesai"
          },
          {
            "label": "Uji model",
            "value": "Belum dijalankan"
          },
          {
            "label": "Katalog toko",
            "value": "Belum diisi"
          }
        ],
        "limitation": "Koneksi dan balasan WhatsApp tetap ditunda. Harga serta stok harus berasal dari data toko yang disahkan."
      },
      {
        "name": "Hermes utama",
        "short_name": "Hermes utama",
        "role": "Gateway tim",
        "group": "Operasional",
        "initials": "HM",
        "room": "07",
        "description": "Penghubung profil tim Hermes. Status diambil dari heartbeat lokal, terpisah dari hasil uji tiap agen.",
        "responsibilities": [
          "Melayani profil tim",
          "Menampilkan status proses",
          "Menjaga jalur koordinasi"
        ],
        "id": "default",
        "profile": "default",
        "model": "deepseek-flash",
        "runtime": "available",
        "runtime_label": "Gateway aktif",
        "stage": "Status gateway",
        "checks": [
          {
            "label": "Heartbeat",
            "value": "Terbarui"
          },
          {
            "label": "Proses",
            "value": "Berjalan"
          }
        ],
        "limitation": "Gateway berjalan sebagai proses terpisah; pemulihan otomatis macOS belum terverifikasi."
      }
    ],
    "runtime": {
      "state": "running",
      "updated_at": "2026-11-09T08:06:54.128400+00:00",
      "active_agents": 0,
      "served_profiles": [
        "ai-influencer-dinda",
        "ai-influencer-nara",
        "ai-influencer-pm",
        "ai-influencer-rania",
        "ai-influencer-researcher",
        "default"
      ]
    },
    "permissions": {
      "generation_enabled": true,
      "publication_enabled": false,
      "scheduler_enabled": true,
      "telegram_enabled": true
    },
    "flow": {
      "balance": 283,
      "verified_at": "2026-11-09T03:00:00+00:00",
      "account": "Mutia (FLOW)",
      "verified_accounts": 3,
      "unverified_accounts": 1
    },
    "pilot": {
      "spent": null,
      "cap": 300
    }
  },
  "latest_research": {
    "report_id": "research-nara-1793874313",
    "timestamp": "2026-11-05T10:25:13.890695+00:00",
    "department": "Digital Marketing & Trend Research",
    "target_character": {
      "id": "nara",
      "name": "Nara Adelia",
      "account": "@nara.adelia_",
      "persona": "Medan Beauty, GRWM & Office Chic",
      "tone": "Ramah, cerdas, gaul khas Medan"
    },
    "trend_data": {
      "title": "POV: 5 Menit Morning Glow & Office Ready Medan",
      "trend_hook": "Transisi natural meja rias ke busana kerja rapi dengan senyum manis percaya diri.",
      "sound": {
        "title": "Morning Acoustic Chill - Lofi Soft Beats",
        "sound_url": "https://www.tiktok.com/music/morning-acoustic-chill-768829104",
        "status": "trending_active",
        "usage_growth": "+34% minggu ini di kategori Lifestyle/Beauty"
      },
      "video_brief": {
        "format": "9:16 Vertical Video",
        "duration": 6,
        "model": "Omni 1.1 Flash",
        "shots": [
          {
            "seconds": "0-3s",
            "visual": "Nara duduk di meja rias dengan pencahayaan ring light natural, merapikan pashmina krem dengan sentuhan lembut, tersenyum ramah ke arah cermin/kamera."
          },
          {
            "seconds": "3-6s",
            "visual": "Nara mengambil tote bag kantor berbahan kanvas premium, melangkah anggun dengan blazer earth-tone kasual siap berangkat kerja."
          }
        ],
        "cost_credits": 10
      },
      "proposed_caption": "Senin pagi jangan mager ya kelen. Minimal sunscreen sama senyum manis sudah siap tempur di kantor Medan hari ini. OOTD hijab hari ini tema earth tone, suka gak? Kasih tahu di kolom komentar ya. #GRWMMedan #AnakKantor #HijabStyle #NaraAdelia",
      "content_pillar": "Relatable Daily Morning & Office Style"
    }
  }
};

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Cache-Control', 'no-store, max-age=0');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Check Bearer token or cookie or ?token= query parameter
  const authHeader = req.headers['authorization'] || '';
  const queryToken = req.query?.token;
  const cookieHeader = req.headers['cookie'] || '';
  const validToken = 'token_intan_ai_hq_88329104';

  const isAuth = authHeader.includes(validToken) ||
                 queryToken === validToken ||
                 cookieHeader.includes(validToken);

  if (!isAuth) {
    return res.status(401).json({
      authenticated: false,
      error: 'Akses Ditolak. Harap verifikasi PIN keamanan Kantor AI Intan.'
    });
  }

  // Clone snapshot and update dynamic timestamps
  const now = new Date();
  const payload = JSON.parse(JSON.stringify(officeSnapshot));
  if (payload.office) {
    payload.office.checked_at = now.toISOString();
    payload.office.runtime.state = 'running';
  }

  return res.status(200).json(payload);
}
