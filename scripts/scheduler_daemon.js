throw new Error('Jalur lama Scheduler dinonaktifkan. Ikuti docs/production-controls.md.');

const { exec } = require('child_process');

console.log('=== AUTONOMOUS POSTING DAEMON STARTED (07:00 & 19:00 WIB) ===');

let lastTriggeredDateAndSlot = '';

setInterval(() => {
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  const wib = new Date(utc + (3600000 * 7));

  const hours = wib.getHours();
  const minutes = wib.getMinutes();
  const dateStr = wib.toISOString().slice(0, 10);

  // Trigger di menit 0-2 pada jam 7 dan 19
  if ((hours === 7 || hours === 19) && minutes <= 2) {
    const slotKey = `${dateStr}_${hours}`;
    if (lastTriggeredDateAndSlot !== slotKey) {
      lastTriggeredDateAndSlot = slotKey;
      console.log(`[DAEMON] Triggering autopost for slot ${slotKey}...`);
      exec('/opt/homebrew/bin/node "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/run_scheduled_autopost.js"', (err, stdout, stderr) => {
        if (err) console.error('[DAEMON ERROR]:', err);
        else console.log('[DAEMON RESULT]:', stdout);
      });
    }
  }
}, 30000);
