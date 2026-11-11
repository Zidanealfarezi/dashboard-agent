const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/pak_vincent/content/pak_vincent-2026-11-11');
const FLOW_PROJECT_KEY = '9805121c-6c21-4562-aa46-390ad95e5a98';
const CHARACTER_ID = 'pak_vincent';
const FLOW_ACCOUNT_ID = 'flow_5';
const SLOT_ID = 'pak_vincent-2026-11-11';
const CREDITS = 16; // 8s 360p x2 Omni 1.2 Flash

async function main() {
  if (!fs.existsSync(TARGET_DIR)) {
    fs.mkdirSync(TARGET_DIR, { recursive: true });
  }

  // Bersihkan MP4 lama di Downloads
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const flowTab = tabs.find(t => t.url && t.url.includes(FLOW_PROJECT_KEY) && t.type === 'page');
  if (!flowTab) throw new Error('Pak Vincent Flow tab not found on port 9333');

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let msgId = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = msgId++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 45000);
    const h = e => {
      const g = JSON.parse(e.data);
      if (g.id === mid) {
        clearTimeout(timer);
        ws.removeEventListener('message', h);
        if (g.error) reject(new Error(JSON.stringify(g.error)));
        else resolve(g.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });

  console.log('Connected to Pak Vincent Flow tab:', flowTab.id);

  await send('Page.enable');
  await send('Browser.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: DOWNLOADS_DIR
  });

  // Verifikasi tombol Mulai pembuatan
  const genBtn = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.generate-icon-button, button[aria-label*="Mulai pembuatan"], button[aria-label*="Generate"]');
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      return {
        x: r.x + r.width / 2,
        y: r.y + r.height / 2,
        disabled: btn.disabled || btn.getAttribute('aria-disabled') === 'true',
        aria: btn.getAttribute('aria-label')
      };
    })()`,
    returnByValue: true
  });

  console.log('Generate button state:', genBtn.result.value);
  if (!genBtn.result.value || genBtn.result.value.disabled) {
    throw new Error('Generate button is disabled or not found');
  }

  const nowIso = new Date().toISOString();
  const jobId = 'pv_job_' + Date.now();
  const idempotencyKey = `flow_5_pv_${Date.now()}`;

  // Catat reservasi job di SQLite
  const sqliteDb = path.join(PROJECT_ROOT, 'operations/production.sqlite');
  execSync(`sqlite3 "${sqliteDb}" "INSERT INTO generation_jobs (id, character_id, flow_account_id, idempotency_key, state, model, duration_seconds, output_count, authorized_credits, actual_credits, created_at) VALUES ('${jobId}', '${CHARACTER_ID}', '${FLOW_ACCOUNT_ID}', '${idempotencyKey}', 'running', 'Omni 1.2 Flash', 8, 2, ${CREDITS}, ${CREDITS}, '${nowIso}');"`);
  execSync(`sqlite3 "${sqliteDb}" "UPDATE daily_slots SET job_id = '${jobId}', state = 'reserved' WHERE id = '${SLOT_ID}';"`);
  console.log('Job registered in SQLite as running:', jobId);

  // Klik tombol Mulai pembuatan
  console.log('Dispatching click to Generate button...');
  const { x, y } = genBtn.result.value;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  console.log('Generate button clicked successfully!');

  // Tunggu proses batch muncul dan selesai
  console.log('Waiting for generation batch to render...');
  await new Promise(r => setTimeout(r, 12000));

  let completed = false;
  let attempts = 0;
  while (!completed && attempts < 90) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));
    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { isDone: false, snippet: 'no container' };
        const text = top.innerText.replace(/\\s+/g, ' ');
        const isDone = (text.includes('download') || text.includes('Unduh') || text.includes('unduh')) && !text.includes('%') && !text.includes('Generating') && !text.includes('Membuat');
        return { isDone, snippet: text.slice(0, 100) };
      })()`,
      returnByValue: true
    });

    console.log(`[Pemeriksaan #${attempts}] Done: ${status.result.value.isDone} | ${status.result.value.snippet}`);
    if (status.result.value.isDone) {
      completed = true;
      break;
    }
  }

  if (!completed) {
    execSync(`sqlite3 "${sqliteDb}" "UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${jobId}';"`);
    throw new Error('Timeout waiting for Flow render');
  }

  console.log('Render 100% completed!');

  // Unduh video dari top batch
  await new Promise(r => setTimeout(r, 3000));
  console.log('Clicking Download on generated video...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      if (!top) return 'no container';
      const dlBtn = top.querySelector('button[aria-label*="Download"], button[aria-label*="Unduh"], button[aria-label*="download"], button[mattooltip*="Download"], button[mattooltip*="Unduh"]');
      if (dlBtn) {
        dlBtn.click();
        return 'clicked top batch download button';
      }
      // Opsi fallback jika tombol di dalam card video
      const cards = top.querySelectorAll('.video-card, .asset-card, [role="group"]');
      if (cards.length > 0) {
        const cardBtn = cards[0].querySelector('button[aria-label*="Download"], button[aria-label*="Unduh"], button[aria-label*="download"]');
        if (cardBtn) {
          cardBtn.click();
          return 'clicked card download button';
        }
      }
      return 'download button not found';
    })()`,
    returnByValue: true
  });

  // Tunggu file muncul di Downloads
  console.log('Waiting for file in Downloads...');
  let downloadedFile = null;
  for (let w = 0; w < 40; w++) {
    await new Promise(r => setTimeout(r, 1000));
    const mp4s = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
    if (mp4s.length > 0) {
      downloadedFile = path.join(DOWNLOADS_DIR, mp4s[0]);
      break;
    }
  }

  if (!downloadedFile || !fs.existsSync(downloadedFile)) {
    execSync(`sqlite3 "${sqliteDb}" "UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${jobId}';"`);
    throw new Error('Downloaded MP4 not found in Downloads folder');
  }

  console.log('Downloaded file found:', downloadedFile);
  const baseName = path.basename(downloadedFile);
  const match = baseName.match(/_([a-f0-9]{8})\.mp4$/i);
  const batchId = match ? match[1] : ('flow_' + Date.now().toString(16));
  console.log('Extracted batch ID:', batchId);

  const rawClip = path.join(TARGET_DIR, 'raw_flow_pakvincent.mp4');
  fs.copyFileSync(downloadedFile, rawClip);
  console.log('Raw Flow video clip saved to:', rawClip);

  // Update status job ke completed di SQLite
  execSync(`sqlite3 "${sqliteDb}" "UPDATE generation_jobs SET state = 'completed', actual_credits = ${CREDITS}, external_job_id = '${batchId}' WHERE id = '${jobId}';"`);
  console.log('SQLite job state set to completed.');

  ws.close();
  console.log('FLOW GENERATION STEP COMPLETED SUCCESSFULLY!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
