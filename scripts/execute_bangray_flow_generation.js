/**
 * Eksekutor Flow untuk Bang Ray — satu slot, satu klik Generate, satu output.
 *
 * Berbeda dari eksekutor lama:
 * - TIDAK menghapus file MP4 di folder Downloads. Hanya mencatat isi folder sebelum
 *   klik, lalu menunggu file BARU muncul; file pengguna lain tidak disentuh.
 * - TIDAK menulis ke SQLite. Reservasi, submit, dan penutupan job dilakukan lewat
 *   `python3 -m app.autopilot reserve|begin-submit|finish` supaya gate anggaran tetap
 *   berjalan (reserve() adalah pintu tunggal biaya).
 *
 * Pakai: node scripts/execute_bangray_flow_generation.js
 */
const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/bang_ray/content/bang_ray-2026-11-12');
const FLOW_PROJECT_KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';
const CDP_PORT = 9333;
const RAW_NAME = 'raw_flow_bangray.mp4';

const sleep = ms => new Promise(r => setTimeout(r, ms));

function mp4sIn(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => f.toLowerCase().endsWith('.mp4'));
}

async function main() {
  if (!fs.existsSync(TARGET_DIR)) fs.mkdirSync(TARGET_DIR, { recursive: true });

  const before = new Set(mp4sIn(DOWNLOADS_DIR));
  console.log('MP4 sebelum klik:', before.size);

  const tabs = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes(FLOW_PROJECT_KEY));
  if (!tab) throw new Error('Tab Flow Bang Ray tidak ditemukan di port ' + CDP_PORT);

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let msgId = 1;
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = msgId++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + method)), 45000);
    const handler = event => {
      const msg = JSON.parse(event.data);
      if (msg.id !== id) return;
      clearTimeout(timer);
      ws.removeEventListener('message', handler);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });

  console.log('Terhubung ke tab Flow Bang Ray:', tab.id);
  await send('Page.enable');
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS_DIR });

  // Pastikan komposer sesuai rencana: Video, 360p, 15 dtk, 9:16, x1.
  const preset = await send('Runtime.evaluate', {
    expression: `(() => {
      const text = document.body.innerText.replace(/\\s+/g, ' ');
      return text.slice(0, 300);
    })()`,
    returnByValue: true
  });
  console.log('Cuplikan komposer:', (preset.result.value || '').slice(0, 160));

  const btn = await send('Runtime.evaluate', {
    expression: `(() => {
      const b = document.querySelector('.generate-icon-button, button[aria-label*="Mulai pembuatan"], button[aria-label*="Generate"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2,
               disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
               aria: b.getAttribute('aria-label') };
    })()`,
    returnByValue: true
  });
  const state = btn.result.value;
  console.log('Tombol Generate:', state);
  if (!state || state.disabled) throw new Error('Tombol Generate tidak tersedia atau nonaktif');

  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: state.x, y: state.y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: state.x, y: state.y, button: 'left', clickCount: 1 });
  console.log('Klik Generate terkirim.');

  await sleep(12000);
  let done = false;
  for (let attempt = 1; attempt <= 90 && !done; attempt++) {
    await sleep(4000);
    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { isDone: false, snippet: 'no container' };
        const text = top.innerText.replace(/\\s+/g, ' ');
        const isDone = (text.includes('download') || text.includes('Unduh') || text.includes('unduh'))
          && !text.includes('%') && !text.includes('Generating') && !text.includes('Membuat');
        return { isDone, snippet: text.slice(0, 100) };
      })()`,
      returnByValue: true
    });
    const v = status.result.value;
    console.log(`[cek ${attempt}] selesai=${v.isDone} | ${v.snippet}`);
    done = v.isDone;
  }
  if (!done) throw new Error('Timeout menunggu render Flow');

  await sleep(3000);
  const clickDl = await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      if (!top) return 'no container';
      const dl = top.querySelector('button[aria-label*="Download"], button[aria-label*="Unduh"], button[aria-label*="download"]');
      if (dl) { dl.click(); return 'clicked top-batch download'; }
      const cards = top.querySelectorAll('.video-card, .asset-card, [role="group"]');
      for (const card of cards) {
        const b = card.querySelector('button[aria-label*="Download"], button[aria-label*="Unduh"], button[aria-label*="download"]');
        if (b) { b.click(); return 'clicked card download'; }
      }
      return 'download button not found';
    })()`,
    returnByValue: true
  });
  console.log('Unduh:', clickDl.result.value);

  let newest = null;
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    const fresh = mp4sIn(DOWNLOADS_DIR).filter(f => !before.has(f));
    if (fresh.length) {
      const candidate = fresh
        .map(f => path.join(DOWNLOADS_DIR, f))
        .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
      if (fs.statSync(candidate).size > 100000) { newest = candidate; break; }
    }
  }
  if (!newest) throw new Error('File baru tidak muncul di Downloads');

  const baseName = path.basename(newest);
  const match = baseName.match(/_([a-f0-9]{8})\.mp4$/i);
  const batchId = match ? match[1] : 'flow_' + Date.now().toString(16);
  const target = path.join(TARGET_DIR, RAW_NAME);
  fs.copyFileSync(newest, target);
  ws.close();

  console.log(JSON.stringify({
    ok: true,
    downloaded: baseName,
    raw_path: path.relative(PROJECT_ROOT, target),
    size_bytes: fs.statSync(target).size,
    external_job_id: batchId
  }, null, 2));
}

main().catch(err => { console.error('GAGAL:', err.message); process.exit(1); });
