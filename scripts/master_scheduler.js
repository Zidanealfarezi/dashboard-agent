throw new Error('Jalur lama Scheduler dinonaktifkan. Ikuti docs/production-controls.md.');

#!/usr/bin/env node
/**
 * Master Autonomous Influencer Scheduler
 * Operates on Asia/Jakarta (WIB) time:
 * - 05:00 WIB: Pinterest Wardrobe Generator (2 distinct outfits: Morning & Evening)
 * - 06:30 WIB: Morning Video Generation (Flow + Audio Mix) -> Send Preview to Telegram Owner
 * - 07:00 WIB: Publish Morning Video to TikTok Studio (or on Owner ACC)
 * - 18:30 WIB: Evening Video Generation (Flow + Audio Mix) -> Send Preview to Telegram Owner
 * - 19:00 WIB: Publish Evening Video to TikTok Studio (or on Owner ACC)
 */

const fs = require('fs');
const path = require('path');
const { exec, execSync } = require('child_process');

const BASE_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER';
const LOG_FILE = path.join(BASE_DIR, 'operations/master_scheduler.log');
const SQLITE_DB = path.join(BASE_DIR, 'operations/production.sqlite');
const PINTEREST_JOB = path.join(BASE_DIR, 'scripts/daily_pinterest_wardrobe_job.js');
const PUBLISHER_SCRIPT = path.join(BASE_DIR, 'scripts/tiktok_publisher.js');
const TELEGRAM_SCRIPT = path.join(BASE_DIR, 'scripts/send_to_telegram.py');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(msg);
  fs.appendFileSync(LOG_FILE, line);
}

// Catatan eksekusi per hari & slot
const executedSlots = new Set();

function getWibTime() {
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  const wib = new Date(utc + (3600000 * 7));
  return {
    hours: wib.getHours(),
    minutes: wib.getMinutes(),
    dateStr: wib.toISOString().slice(0, 10),
    timeStr: `${wib.getHours().toString().padStart(2, '0')}:${wib.getMinutes().toString().padStart(2, '0')}`
  };
}

async function runMasterCycle() {
  const { hours, minutes, dateStr, timeStr } = getWibTime();

  // 1. Pukul 05:00 - 05:05 WIB: Pinterest Wardrobe Job
  const slotPinterest = `pinterest_${dateStr}`;
  if (hours === 5 && minutes <= 5 && !executedSlots.has(slotPinterest)) {
    executedSlots.add(slotPinterest);
    log(`[SCHEDULER 05:00 WIB] Menjalankan generator OOTD Pinterest harian...`);
    try {
      execSync(`node "${PINTEREST_JOB}"`, { stdio: 'inherit' });
      log(`[SCHEDULER 05:00 WIB] Sukses menyiapkan 2 OOTD Pinterest untuk hari ini!`);
    } catch (err) {
      log(`[SCHEDULER ERROR 05:00]: ${err.message}`);
    }
  }

  // 2. Pukul 06:30 - 06:35 WIB: Pra-Produksi Slot Pagi
  const slotPrePagi = `prepagi_${dateStr}`;
  if (hours === 6 && minutes >= 30 && minutes <= 35 && !executedSlots.has(slotPrePagi)) {
    executedSlots.add(slotPrePagi);
    log(`[SCHEDULER 06:30 WIB] Memulai pra-produksi video slot Pagi...`);
    try {
      execSync(`node "${path.join(BASE_DIR, 'scripts/generate_pagi_palembang_vlog.js')}"`, { stdio: 'inherit' });
      log(`[SCHEDULER 06:30 WIB] Video slot pagi siap & dikirim ke Telegram Owner!`);
    } catch (err) {
      log(`[SCHEDULER ERROR 06:30]: ${err.message}`);
    }
  }

  // 3. Pukul 07:00 - 07:05 WIB: Auto-Publish Slot Pagi (Jika belum dipublish via ACC)
  const slotPubPagi = `pubpagi_${dateStr}`;
  if (hours === 7 && minutes <= 5 && !executedSlots.has(slotPubPagi)) {
    executedSlots.add(slotPubPagi);
    log(`[SCHEDULER 07:00 WIB] Memeriksa status publish video slot pagi...`);
    try {
      const videoPath = path.join(BASE_DIR, `characters/dinda/content/dinda-pagi-palembang-${dateStr}/final_vlog.mp4`);
      if (fs.existsSync(videoPath)) {
        // Cek apakah sudah terbit di SQLite
        const check = execSync(`sqlite3 "${SQLITE_DB}" "SELECT id FROM publications WHERE version_id LIKE '%senin_pagi_${dateStr.replace(/-/g, '')}%' OR platform_post_id='dinda_senin_pagi';"`, { encoding: 'utf8' }).trim();
        if (!check) {
          log(`[SCHEDULER 07:00 WIB] Menerbitkan video pagi ke TikTok Studio...`);
          execSync(`node "${PUBLISHER_SCRIPT}" "${videoPath}"`, { stdio: 'inherit' });
          log(`[SCHEDULER 07:00 WIB] Video pagi berhasil tayang live!`);
        } else {
          log(`[SCHEDULER 07:00 WIB] Video pagi sudah terbit sebelumnya.`);
        }
      }
    } catch (err) {
      log(`[SCHEDULER ERROR 07:00]: ${err.message}`);
    }
  }

  // 4. Pukul 18:30 - 18:35 WIB: Pra-Produksi Slot Malam
  const slotPreMalam = `premalam_${dateStr}`;
  if (hours === 18 && minutes >= 30 && minutes <= 35 && !executedSlots.has(slotPreMalam)) {
    executedSlots.add(slotPreMalam);
    log(`[SCHEDULER 18:30 WIB] Memulai pra-produksi video slot Malam...`);
    try {
      execSync(`node "${path.join(BASE_DIR, 'scripts/generate_malam_palembang_vlog.js')}"`, { stdio: 'inherit' });
      log(`[SCHEDULER 18:30 WIB] Video slot malam siap & dikirim ke Telegram Owner!`);
    } catch (err) {
      log(`[SCHEDULER ERROR 18:30]: ${err.message}`);
    }
  }

  // 5. Pukul 19:00 - 19:05 WIB: Auto-Publish Slot Malam (Jika belum dipublish via ACC)
  const slotPubMalam = `pubmalam_${dateStr}`;
  if (hours === 19 && minutes <= 5 && !executedSlots.has(slotPubMalam)) {
    executedSlots.add(slotPubMalam);
    log(`[SCHEDULER 19:00 WIB] Memeriksa status publish video slot malam...`);
    try {
      const videoPath = path.join(BASE_DIR, `characters/dinda/content/dinda-malam-palembang-${dateStr}/final_10s.mp4`);
      if (fs.existsSync(videoPath)) {
        log(`[SCHEDULER 19:00 WIB] Menerbitkan video malam ke TikTok Studio...`);
        execSync(`node "${PUBLISHER_SCRIPT}" "${videoPath}"`, { stdio: 'inherit' });
        log(`[SCHEDULER 19:00 WIB] Video malam berhasil tayang live!`);
      }
    } catch (err) {
      log(`[SCHEDULER ERROR 19:00]: ${err.message}`);
    }
  }
}

console.log('=== MASTER AUTONOMOUS SCHEDULER AKTIF (WIB TIMELINE) ===');
log('Master scheduler diaktifkan. Memantau slot: 05:00 (Pinterest), 06:30 & 07:00 (Pagi), 18:30 & 19:00 (Malam).');

// Jalankan pemeriksaan setiap 30 detik
setInterval(runMasterCycle, 30000);
runMasterCycle();
