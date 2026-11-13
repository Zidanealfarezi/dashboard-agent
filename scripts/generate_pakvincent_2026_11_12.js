/**
 * Generate Flow Video for Pak Vincent (2026-11-12)
 * Connects to existing CDP tab on port 9333, verifies settings, triggers generation,
 * monitors batch render, downloads MP4, and saves to characters/pak_vincent/content/pak_vincent-2026-11-12/raw_flow_pakvincent.mp4.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/pak_vincent/content/pak_vincent-2026-11-12');
const FLOW_PROJECT_KEY = '9805121c-6c21-4562-aa46-390ad95e5a98';
const CDP_PORT = 9333;
const SLOT_ID = 'pak_vincent-2026-11-12';
const JOB_ID = '7902b09cfb6444dcbcfff4e5d5737760';

const sleep = ms => new Promise(r => setTimeout(r, ms));
const mp4sIn = dir => (fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.toLowerCase().endsWith('.mp4')) : []);

async function main() {
  if (!fs.existsSync(TARGET_DIR)) fs.mkdirSync(TARGET_DIR, { recursive: true });
  const before = new Set(mp4sIn(DOWNLOADS_DIR));
  console.log(`Initial MP4s in Downloads: ${before.size}`);

  const tabs = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes(FLOW_PROJECT_KEY));
  if (!tab) throw new Error('Tab Flow Pak Vincent tidak ditemukan pada CDP port ' + CDP_PORT);

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 1;
  const pending = new Map();
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { resolve, reject, timer } = pending.get(m.id);
      clearTimeout(timer); pending.delete(m.id);
      m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
    }
  });

  const send = (method, params = {}, timeout = 45000) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => { pending.delete(mid); reject(new Error('Timeout ' + method)); }, timeout);
    pending.set(mid, { resolve, reject, timer });
    ws.send(JSON.stringify({ id: mid, method, params }));
  });

  const evalJs = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true })).result.value;
  const clickAt = async (p, settle = 800) => {
    for (const type of ['mousePressed', 'mouseReleased'])
      await send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', clickCount: 1 });
    await sleep(settle);
  };

  await send('Page.enable');
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS_DIR });

  // Cek tombol Mulai pembuatan
  const genBtn = await evalJs(`(() => {
    const b = document.querySelector('.generate-icon-button') ||
      Array.from(document.querySelectorAll('button')).find(x => (x.getAttribute('aria-label')||'').includes('Mulai pembuatan') || (x.getAttribute('aria-label')||'').includes('Generate'));
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return {
      x: r.x + r.width / 2,
      y: r.y + r.height / 2,
      disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
      aria: b.getAttribute('aria-label')
    };
  })()`);

  console.log('Status tombol pembuatan:', JSON.stringify(genBtn));
  if (!genBtn || genBtn.disabled) throw new Error('Tombol Generate nonaktif atau tidak ditemukan');

  // Update status job SQLite ke running
  const dbPath = path.join(PROJECT_ROOT, 'operations/production.sqlite');
  execFileSync('sqlite3', [dbPath, `UPDATE generation_jobs SET state = 'running' WHERE id = '${JOB_ID}';`]);
  console.log(`Job ${JOB_ID} diset ke 'running' di SQLite.`);

  // Klik tombol Mulai pembuatan
  console.log('Mengklik tombol Mulai pembuatan...');
  await clickAt(genBtn, 0);
  console.log('Generate diklik! Menunggu proses render...');

  // Tunggu batch muncul
  await sleep(10000);

  let done = false;
  for (let i = 1; i <= 90 && !done; i++) {
    await sleep(4000);
    const st = await evalJs(`(() => {
      const top = document.querySelector('.batch-container');
      if (!top) return { isDone: false, snippet: 'no container' };
      const text = top.innerText.replace(/\\s+/g, ' ');
      const isDone = (text.includes('Unduh') || text.includes('download') || text.includes('unduh'))
        && !text.includes('%') && !text.includes('Membuat') && !text.includes('Generating');
      return { isDone, snippet: text.slice(0, 90) };
    })()`);
    console.log(`[Pemeriksaan render #${i}] selesai=${st.isDone} | ${st.snippet}`);
    done = st.isDone;
  }

  if (!done) {
    execFileSync('sqlite3', [dbPath, `UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${JOB_ID}';`]);
    throw new Error('Timeout menunggu render Google Flow');
  }

  console.log('Render selesai 100%! Mengklik tombol Unduh...');
  await sleep(3000);

  const dlResult = await evalJs(`(() => {
    const top = document.querySelector('.batch-container');
    if (!top) return 'no container';
    const b = top.querySelector('button[aria-label*="Unduh"], button[aria-label*="Download"], button[aria-label*="unduh"]');
    if (b) { b.click(); return 'clicked batch download'; }
    for (const card of top.querySelectorAll('.video-card, .asset-card, [role=group]')) {
      const c = card.querySelector('button[aria-label*="Unduh"], button[aria-label*="Download"]');
      if (c) { c.click(); return 'clicked card download'; }
    }
    return 'download button not found';
  })()`);
  console.log('Hasil klik unduh:', dlResult);

  // Tunggu file baru muncul di folder Downloads
  console.log('Menunggu file video diunduh...');
  let newest = null;
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    const fresh = mp4sIn(DOWNLOADS_DIR).filter(f => !before.has(f));
    if (fresh.length) {
      const cand = fresh.map(f => path.join(DOWNLOADS_DIR, f)).sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
      if (fs.statSync(cand).size > 100000) {
        // Cek stabilitas ukuran file (memastikan download selesai)
        const size1 = fs.statSync(cand).size;
        await sleep(1000);
        const size2 = fs.statSync(cand).size;
        if (size1 === size2) {
          newest = cand;
          break;
        }
      }
    }
  }

  if (!newest) {
    execFileSync('sqlite3', [dbPath, `UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${JOB_ID}';`]);
    throw new Error('File MP4 hasil generasi tidak ditemukan di Downloads');
  }

  const base = path.basename(newest);
  const m = base.match(/_([a-f0-9]{8})\.mp4$/i);
  const externalJobId = m ? m[1] : ('pv_' + Date.now().toString(16).slice(-8));
  const rawTarget = path.join(TARGET_DIR, 'raw_flow_pakvincent.mp4');
  fs.copyFileSync(newest, rawTarget);
  ws.close();

  console.log('File berhasil diunduh dan disalin:');
  console.log(`- Asli: ${newest}`);
  console.log(`- Target: ${rawTarget}`);
  console.log(`- Ukuran: ${fs.statSync(rawTarget).size} bytes`);
  console.log(`- External Job ID: ${externalJobId}`);

  // Tulis metadata hasil untuk diproses pipeline
  const resultJson = path.join(TARGET_DIR, 'generation_result.json');
  fs.writeFileSync(resultJson, JSON.stringify({
    ok: true,
    job_id: JOB_ID,
    slot_id: SLOT_ID,
    external_job_id: externalJobId,
    raw_path: rawTarget,
    downloaded_file: newest,
    size_bytes: fs.statSync(rawTarget).size,
    created_at: new Date().toISOString()
  }, null, 2));

  console.log('Metadata tersimpan di:', resultJson);
}

main().catch(err => {
  console.error('GAGAL:', err.message);
  process.exit(1);
});
