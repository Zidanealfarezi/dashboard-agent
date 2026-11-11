throw new Error('Jalur lama Scheduler dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const LOG_FILE = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/operations/autopost.log';
const SQLITE_DB = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/operations/production.sqlite';

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(msg);
  fs.appendFileSync(LOG_FILE, line);
}

function checkAndRun() {
  const now = new Date();
  // Format waktu WIB (Asia/Jakarta = UTC+7)
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  const wib = new Date(utc + (3600000 * 7));

  const hours = wib.getHours();
  const minutes = wib.getMinutes();
  const dateStr = wib.toISOString().slice(0, 10); // YYYY-MM-DD

  log(`Pemeriksaan Scheduler WIB: ${dateStr} ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`);

  // Slot Pagi: Jam 07:00 - 07:15 WIB
  const isMorningSlot = (hours === 7 && minutes <= 15);
  // Slot Malam: Jam 19:00 - 19:15 WIB
  const isEveningSlot = (hours === 19 && minutes <= 15);

  if (!isMorningSlot && !isEveningSlot) {
    log('Bukan jendela waktu tayang (Jadwal: 07:00 WIB & 19:00 WIB). Menunggu...');
    return;
  }

  const slotType = isMorningSlot ? 'pagi' : 'malam';
  const idempotencyKey = `dinda_${slotType}_${dateStr.replace(/-/g, '')}`;

  // Cek apakah slot hari ini sudah pernah diposting di SQLite
  try {
    const existing = execSync(`sqlite3 "${SQLITE_DB}" "SELECT id, state FROM publications WHERE idempotency_key LIKE '%${idempotencyKey}%' OR version_id LIKE '%${idempotencyKey}%';"`, { encoding: 'utf8' }).trim();
    if (existing) {
      log(`Slot ${slotType} tanggal ${dateStr} sudah terbit sebelumnya (${existing}). Melewati proses.`);
      return;
    }
  } catch (err) {
    log(`Warning query DB: ${err.message}`);
  }

  log(`Memulai proses otomatisasi publikasi slot ${slotType} untuk tanggal ${dateStr}...`);

  try {
    if (slotType === 'pagi') {
      execSync('node "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/generate_pagi_palembang_vlog.js"', { stdio: 'inherit' });
    } else {
      execSync('node "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/generate_malam_palembang_vlog.js"', { stdio: 'inherit' });
    }
    log(`Sukses mempublikasikan slot ${slotType} tanggal ${dateStr}!`);
  } catch (err) {
    log(`ERROR saat eksekusi slot ${slotType}: ${err.message}`);
  }
}

// Jalankan pemeriksaan
checkAndRun();
