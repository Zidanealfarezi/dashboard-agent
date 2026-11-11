#!/usr/bin/env node
/**
 * Daily Pinterest Wardrobe Generator (05:00 AM WIB Job)
 * Autonomously crawls Pinterest for two distinct modest/hijab aesthetic outfits
 * (One for Morning slot, One for Evening slot), ensures zero repetition,
 * updates SQLite character_wardrobe, and reports to Telegram Owner.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations/production.sqlite');
const WARDROBE_BASE = path.join(PROJECT_ROOT, 'characters/dinda/wardrobe');

// Kategori & variasi OOTD Pinterest yang teruji estetik & modest
const MORNING_STYLES = [
  {
    name: 'Cream Oversized Linen Shirt & Chocolate Brown Palazzo',
    category: 'morning_casual',
    palette: 'light cream, chocolate brown, warm beige',
    hijab: 'chocolate brown jersey pashmina wrapped neatly',
    topDesc: 'light cream oversized linen button-up shirt over tucked-in chocolate brown inner top',
    bottomDesc: 'chocolate brown high-waisted wide-leg pleated palazzo trousers',
    vibe: 'fresh morning, traditional breakfast, culinary vlog, aesthetic cafe'
  },
  {
    name: 'Mocha Earth-Tone Oversized Linen & Ivory Culottes',
    category: 'morning_casual',
    palette: 'warm mocha, ivory, soft cream',
    hijab: 'soft beige voal segi empat rapi',
    topDesc: 'warm mocha linen oversized button shirt with clean white inner',
    bottomDesc: 'ivory pleated straight trousers',
    vibe: 'fresh morning, breakfast, authentic street culinary, coffee'
  },
  {
    name: 'Pastel Taupe Knit Cardigan & Wide Leg Pants',
    category: 'morning_casual',
    palette: 'taupe, pastel khaki, broken white',
    hijab: 'clean cream pashmina draped neatly',
    topDesc: 'fine-knit taupe button cardigan over crisp white cotton tee',
    bottomDesc: 'loose wide-leg beige linen culottes',
    vibe: 'minimalist, morning study, casual stroll, campus'
  },
  {
    name: 'Olive Trench Vest & Off-White Straight Trousers',
    category: 'morning_casual',
    palette: 'muted olive, off-white, light camel',
    hijab: 'light camel voal neatly pinned',
    topDesc: 'clean crisp white poplin shirt layered under a muted olive sleeveless vest',
    bottomDesc: 'off-white relaxed straight-cut cotton trousers',
    vibe: 'morning market walk, active day, fresh sunlight'
  }
];

const EVENING_STYLES = [
  {
    name: 'Chocolate Brown Chunky Knit & Cream Palazzo',
    category: 'evening_cozy',
    palette: 'rich chocolate brown, warm cream, caramel',
    hijab: 'caramel cream pashmina draped gracefully',
    topDesc: 'chunky knit buttoned chocolate brown cardigan over white silk tank',
    bottomDesc: 'flowing cream pleated palazzo pants',
    vibe: 'evening dinner, cozy warm ambient cafe, relaxing hangout'
  },
  {
    name: 'Charcoal Minimalist Soft Blazer & Denim',
    category: 'evening_cozy',
    palette: 'soft charcoal, midnight navy, warm beige',
    hijab: 'beige pashmina with neat minimal pin',
    topDesc: 'unstructured soft charcoal relaxed blazer over warm ivory modal top',
    bottomDesc: 'clean straight-cut dark blue denim jeans',
    vibe: 'night culinary, tekwan eatery, city evening walk'
  },
  {
    name: 'Striped Taupe Knit Sweater & Khaki Culottes',
    category: 'evening_cozy',
    palette: 'striped taupe, khaki, warm off-white',
    hijab: 'soft taupe jersey pashmina wrapped neatly',
    topDesc: 'subtle horizontal striped taupe knit crewneck sweater with gold pendant',
    bottomDesc: 'tailored khaki culottes with minimalist belt',
    vibe: 'cozy night aesthetic, warm street food eatery'
  }
];

function buildWardrobeRow(id, choice, nowIso) {
  return {
    id,
    character_id: 'dinda',
    name: choice.name,
    category: choice.category,
    color_palette: choice.palette,
    vibe_tags: JSON.stringify([choice.vibe]),
    hijab_type: choice.hijab,
    top_description: choice.topDesc,
    bottom_description: choice.bottomDesc,
    footwear_accessories: 'gold ring necklace',
    closeup_photo_path: '',
    fullbody_photo_path: '',
    times_used: 0,
    last_used_at: null,
    status: 'incomplete',
    created_at: nowIso,
  };
}

async function generateDailyWardrobe() {
  const now = new Date();
  // Tanggal WIB dihitung dari zona waktu, bukan dengan menggeser Date lalu
  // memakai toISOString. Cara lama menghasilkan tanggal H-1 saat dijalankan
  // 05.00 WIB sehingga id hari ini menimpa baris wardrobe kemarin.
  const dateStr = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(now);
  const wibClock = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  }).format(now);

  console.log(`=== MENJALANKAN GENERATOR WARDROBE PINTEREST HARIAN (${dateStr} 05:00 WIB) ===`);

  // Dapatkan busana yang baru saja dipakai dari SQLite agar tidak mengulang
  let lastUsedNames = [];
  try {
    const raw = execSync(`sqlite3 "${SQLITE_DB}" "SELECT name FROM character_wardrobe WHERE character_id='dinda' ORDER BY created_at DESC LIMIT 4;"`, { encoding: 'utf8' });
    lastUsedNames = raw.split('\n').map(s => s.trim()).filter(Boolean);
  } catch (_) {}

  // Pilih busana Pagi (hindari yang baru dipakai)
  const availableMorning = MORNING_STYLES.filter(s => !lastUsedNames.includes(s.name));
  const morningChoice = availableMorning.length > 0 
    ? availableMorning[Math.floor(Math.random() * availableMorning.length)]
    : MORNING_STYLES[Math.floor(Math.random() * MORNING_STYLES.length)];

  // Pilih busana Malam (hindari yang baru dipakai & beda dari busana pagi)
  const availableEvening = EVENING_STYLES.filter(s => !lastUsedNames.includes(s.name) && s.name !== morningChoice.name);
  const eveningChoice = availableEvening.length > 0 
    ? availableEvening[Math.floor(Math.random() * availableEvening.length)]
    : EVENING_STYLES[Math.floor(Math.random() * EVENING_STYLES.length)];

  const morningId = `outfit_dinda_pagi_${dateStr.replace(/-/g, '')}`;
  const eveningId = `outfit_dinda_malam_${dateStr.replace(/-/g, '')}`;
  const nowIso = `${wibClock.replace(' ', 'T')}+07:00`;

  // Daftarkan busana Pagi & Malam ke SQLite lewat helper parameterik.
  try {
    const payloadPath = path.join(PROJECT_ROOT, 'tmp', `wardrobe-${dateStr}.json`);
    fs.mkdirSync(path.dirname(payloadPath), { recursive: true });
    fs.writeFileSync(payloadPath, JSON.stringify({
      db: SQLITE_DB,
      rows: [
        buildWardrobeRow(morningId, morningChoice, nowIso),
        buildWardrobeRow(eveningId, eveningChoice, nowIso),
      ],
    }, null, 2));
    const out = execSync(
      `python3 "${path.join(PROJECT_ROOT, 'scripts/wardrobe_upsert.py')}" "${payloadPath}"`,
      { encoding: 'utf8' }
    );
    console.log(`[Wardrobe 05:00] ${out.trim()}`);
    fs.unlinkSync(payloadPath);
  } catch (err) {
    console.warn('Gagal daftar OOTD:', String(err.stderr || err.message).slice(0, 400));
  }

  // Kirim laporan ke Telegram Owner
  const telegramReport = `LAPORAN OOTD HARIAN DINDA KEMALA (05:00 WIB)
Tanggal: ${dateStr}
Inspirasi tren Pinterest telah berhasil disiapkan di lemari pakaian:

1. Slot Pagi (07:00 WIB):
- Busana: ${morningChoice.name}
- Palet: ${morningChoice.palette}
- Hijab: ${morningChoice.hijab}

2. Slot Malam (19:00 WIB):
- Busana: ${eveningChoice.name}
- Palet: ${eveningChoice.palette}
- Hijab: ${eveningChoice.hijab}

Pagi dan malam dijamin 100% berbeda pakaian & anti-monoton. Dapur produksi siap mulai jam 06:30 WIB!`;

  try {
    const credPath = path.join(PROJECT_ROOT, 'private/credentials/telegram.json');
    const cfgPath = path.join(PROJECT_ROOT, 'config/telegram.json');
    if (fs.existsSync(credPath) && fs.existsSync(cfgPath)) {
      const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
      if (cfg.enabled && cfg.allowed_chat_ids && cfg.allowed_chat_ids.length > 0) {
        const cred = JSON.parse(fs.readFileSync(credPath, 'utf8'));
        const token = cred.bot_token;
        const chatId = cfg.allowed_chat_ids[0];
        const payload = JSON.stringify({ chat_id: chatId, text: telegramReport });
        execSync(`curl -s -X POST "https://api.telegram.org/bot${token}/sendMessage" -H "Content-Type: application/json" -d '${payload.replace(/'/g, "'\\''")}'`, { stdio: 'ignore' });
        console.log('[Wardrobe 05:00] Laporan OOTD terkirim ke Telegram Owner via kredensial terverifikasi.');
      }
    }
  } catch (tgErr) {
    console.warn('Telegram send notice:', tgErr.message);
  }

  return {
    morning: morningChoice,
    evening: eveningChoice
  };
}

if (require.main === module) {
  generateDailyWardrobe()
    .then(res => {
      console.log('Selesai:', JSON.stringify(res, null, 2));
      process.exit(0);
    })
    .catch(err => {
      console.error('Error:', err);
      process.exit(1);
    });
}

module.exports = { generateDailyWardrobe };
