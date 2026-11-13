/**
 * Eksekutor Flow Bang Ray v2 — isi komposer sendiri: 3 referensi + prompt + 15s,
 * lalu satu klik Generate dan unduh hasilnya.
 *
 * Prinsip:
 * - Tidak menghapus MP4 di Downloads; hanya menunggu file BARU.
 * - Tidak menulis SQLite; reservasi/penutupan job lewat `python3 -m app.autopilot`.
 * - Gagal di titik mana pun sebelum klik = berhenti tanpa biaya.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/bang_ray/content/bang_ray-2026-11-12');
const FLOW_PROJECT_KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';
const CDP_PORT = 9333;
const DURATION_LABEL = '15s';
const SLOT_ID = 'bang_ray-2026-11-12';
const REFERENCES = [
  path.join(PROJECT_ROOT, 'FOTO_KARAKTER/BangRay/bangray_three_expression_sheet.jpg'),
  path.join(PROJECT_ROOT, 'FOTO_KARAKTER/BangRay/bangray_fullbody_turnaround.jpg'),
  path.join(PROJECT_ROOT, 'FOTO_KARAKTER/BangRay/bangray_profile_avatar.jpg'),
];

const sleep = ms => new Promise(r => setTimeout(r, ms));
const mp4sIn = dir => (fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.toLowerCase().endsWith('.mp4')) : []);

function readPrompt() {
  const db = path.join(PROJECT_ROOT, 'operations/production.sqlite');
  const raw = execFileSync('sqlite3', [db, `SELECT plan_json FROM daily_slots WHERE id='${SLOT_ID}';`], { encoding: 'utf8' }).trim();
  return JSON.parse(raw).shots[0].prompt;
}

async function main() {
  for (const ref of REFERENCES) if (!fs.existsSync(ref)) throw new Error('Referensi tidak ada: ' + ref);
  const PROMPT = readPrompt();
  if (!fs.existsSync(TARGET_DIR)) fs.mkdirSync(TARGET_DIR, { recursive: true });
  const before = new Set(mp4sIn(DOWNLOADS_DIR));

  const tabs = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes(FLOW_PROJECT_KEY));
  if (!tab) throw new Error('Tab Flow Bang Ray tidak ditemukan');

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 1;
  const pending = new Map();
  let chooserNode = null;
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.method === 'Page.fileChooserOpened') { chooserNode = m.params.backendNodeId; return; }
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
  await send('DOM.enable');
  await send('Page.setInterceptFileChooserDialog', { enabled: true });
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS_DIR });

  const addBtn = await evalJs(`(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => (x.getAttribute('aria-label')||'').includes('tambahkan media'));
    if (!b) return null; const r = b.getBoundingClientRect();
    return { x: r.x + r.width/2, y: r.y + r.height/2 };
  })()`);
  if (!addBtn) throw new Error('Tombol tambah media tidak ada');
  await clickAt(addBtn, 1200);

  const uploadItem = await (async () => {
    for (let attempt = 0; attempt < 3; attempt++) {
      const found = await evalJs(`(() => {
        const nodes = Array.from(document.querySelectorAll('[role=menuitem], .cdk-overlay-container button, .cdk-overlay-container [role=button], button'));
        const el = nodes.find(x => (x.innerText||'').trim().toLowerCase().startsWith('upload'));
        if (!el) return null; const r = el.getBoundingClientRect();
        if (!r.width || !r.height) return null;
        return { x: r.x + r.width/2, y: r.y + r.height/2 };
      })()`);
      if (found) return found;
      await clickAt(addBtn, 1500);
    }
    return null;
  })();
  if (!uploadItem) throw new Error('Item Upload tidak ditemukan');
  chooserNode = null;
  await clickAt(uploadItem, 0);

  for (let i = 0; i < 20 && !chooserNode; i++) await sleep(500);
  if (!chooserNode) throw new Error('File chooser tidak terbuka');
  await send('DOM.setFileInputFiles', { files: REFERENCES, backendNodeId: chooserNode });
  console.log('Tiga referensi dikirim:', REFERENCES.map(r => path.basename(r)).join(', '));
  await sleep(7000);

  const filled = await evalJs(`(() => {
    const pm = document.querySelector('.ProseMirror');
    if (!pm) return false;
    pm.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    return true;
  })()`);
  if (!filled) throw new Error('Komposer ProseMirror tidak ditemukan');
  await sleep(400);
  await send('Input.insertText', { text: PROMPT });
  await sleep(1500);

  const settings = await evalJs(`(() => {
    const t = document.querySelector('button[aria-label="Settings trigger"]');
    return t ? t.innerText.replace(/\\s+/g,' ') : null;
  })()`);
  console.log('Settings komposer:', settings);
  if (settings && !settings.includes(DURATION_LABEL)) {
    const trig = await evalJs(`(() => {
      const t = document.querySelector('button[aria-label="Settings trigger"]');
      if (!t) return null; const r = t.getBoundingClientRect();
      return { x: r.x + r.width/2, y: r.y + r.height/2 };
    })()`);
    await clickAt(trig, 1200);
    const opt = await evalJs(`(() => {
      const els = Array.from(document.querySelectorAll('.cdk-overlay-container button, .cdk-overlay-container [role=button], .cdk-overlay-container mat-button-toggle'));
      const t = els.find(e => (e.innerText||'').trim() === '${DURATION_LABEL}');
      if (!t) return null; const r = t.getBoundingClientRect();
      return { x: r.x + r.width/2, y: r.y + r.height/2 };
    })()`);
    if (!opt) throw new Error('Opsi durasi ' + DURATION_LABEL + ' tidak ditemukan');
    await clickAt(opt, 1000);
    await clickAt(trig, 1000);
  }

  const gen = await evalJs(`(() => {
    const b = document.querySelector('.generate-icon-button') ||
      Array.from(document.querySelectorAll('button')).find(x => (x.getAttribute('aria-label')||'') === 'Mulai pembuatan');
    if (!b) return null; const r = b.getBoundingClientRect();
    return { x: r.x + r.width/2, y: r.y + r.height/2, disabled: b.disabled || b.getAttribute('aria-disabled') === 'true' };
  })()`);
  console.log('Tombol Generate:', JSON.stringify(gen));
  if (!gen || gen.disabled) throw new Error('Tombol Generate nonaktif; berhenti sebelum biaya');

  await clickAt(gen, 0);
  console.log('Klik Generate terkirim; menunggu render...');

  await sleep(12000);
  let done = false;
  for (let i = 1; i <= 90 && !done; i++) {
    await sleep(4000);
    const st = await evalJs(`(() => {
      const top = document.querySelector('.batch-container');
      if (!top) return { isDone:false, snippet:'no container' };
      const text = top.innerText.replace(/\\s+/g,' ');
      const isDone = (text.includes('Unduh')||text.includes('download')||text.includes('unduh'))
        && !text.includes('%') && !text.includes('Membuat') && !text.includes('Generating');
      return { isDone, snippet: text.slice(0,90) };
    })()`);
    console.log(`[cek ${i}] selesai=${st.isDone} | ${st.snippet}`);
    done = st.isDone;
  }
  if (!done) throw new Error('Timeout render; biaya mungkin sudah terpakai, perlu pemeriksaan manual');

  await sleep(3000);
  const dl = await evalJs(`(() => {
    const top = document.querySelector('.batch-container');
    if (!top) return 'no container';
    const b = top.querySelector('button[aria-label*="Unduh"], button[aria-label*="Download"], button[aria-label*="unduh"]');
    if (b) { b.click(); return 'clicked'; }
    for (const card of top.querySelectorAll('.video-card, .asset-card, [role=group]')) {
      const c = card.querySelector('button[aria-label*="Unduh"], button[aria-label*="Download"]');
      if (c) { c.click(); return 'clicked card'; }
    }
    return 'not found';
  })()`);
  console.log('Unduh:', dl);

  let newest = null;
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    const fresh = mp4sIn(DOWNLOADS_DIR).filter(f => !before.has(f));
    if (fresh.length) {
      const cand = fresh.map(f => path.join(DOWNLOADS_DIR, f)).sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
      if (fs.statSync(cand).size > 100000) { newest = cand; break; }
    }
  }
  if (!newest) throw new Error('File hasil tidak muncul di Downloads');

  const base = path.basename(newest);
  const m = base.match(/_([a-f0-9]{8})\.mp4$/i);
  const target = path.join(TARGET_DIR, 'raw_flow_bangray.mp4');
  fs.copyFileSync(newest, target);
  ws.close();
  console.log(JSON.stringify({
    ok: true, downloaded: base, raw_path: path.relative(PROJECT_ROOT, target),
    size_bytes: fs.statSync(target).size, external_job_id: m ? m[1] : 'flow_' + Date.now().toString(16)
  }, null, 2));
}

main().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
