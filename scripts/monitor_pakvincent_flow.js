const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/pak_vincent/content/pak_vincent-2026-11-11');
const FLOW_PROJECT_KEY = '9805121c-6c21-4562-aa46-390ad95e5a98';
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations/production.sqlite');

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
  if (!flowTab) throw new Error('Flow tab not found');

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

  console.log('Connected to Flow tab.');
  await send('Page.enable');
  await send('Browser.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: DOWNLOADS_DIR
  });

  console.log('Waiting for generation to finish...');
  let completed = false;
  let attempts = 0;

  while (!completed && attempts < 90) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));
    const check = await send('Runtime.evaluate', {
      expression: `(() => {
        const text = document.body.innerText;
        const matches = text.match(/\\b\\d+%/g);
        const hasGenerating = text.includes('Membuat') || text.includes('Generating');
        const dlBtns = Array.from(document.querySelectorAll('button')).filter(b => {
          const aria = b.getAttribute('aria-label') || '';
          const t = b.innerText || '';
          return aria.toLowerCase().includes('unduh') || aria.toLowerCase().includes('download') || t.includes('download');
        });
        const videos = document.querySelectorAll('video');
        return JSON.stringify({
          percentages: matches,
          hasGenerating,
          dlCount: dlBtns.length,
          videoCount: videos.length
        });
      })()`,
      returnByValue: true
    });

    const parsed = JSON.parse(check.result.value);
    console.log(`[Pemeriksaan #${attempts}] %: ${JSON.stringify(parsed.percentages)} | DlBtns: ${parsed.dlCount} | Videos: ${parsed.videoCount}`);

    // Jika persentase hilang dan ada video atau tombol unduh
    if (!parsed.percentages && (parsed.dlCount > 0 || parsed.videoCount > 0)) {
      completed = true;
      break;
    }
  }

  if (!completed) throw new Error('Generation did not complete within expected time.');

  console.log('Generation completed! Triggering download...');
  await new Promise(r => setTimeout(r, 2000));

  // Klik tombol download pertama yang tersedia
  const dlResult = await send('Runtime.evaluate', {
    expression: `(() => {
      // 1. Coba tombol unduh langsung
      const dlBtns = Array.from(document.querySelectorAll('button')).filter(b => {
        const aria = b.getAttribute('aria-label') || '';
        const t = b.innerText || '';
        return aria.toLowerCase().includes('unduh') || aria.toLowerCase().includes('download') || t.includes('download');
      });
      if (dlBtns.length > 0) {
        dlBtns[0].click();
        return 'clicked dlBtn: ' + (dlBtns[0].getAttribute('aria-label') || dlBtns[0].innerText);
      }

      // 2. Coba card video jika ada tombol hover
      const videoCards = document.querySelectorAll('.tile-row, .video-card, .asset-card');
      for (const card of videoCards) {
        const b = card.querySelector('button[aria-label*="Unduh"], button[aria-label*="Download"]');
        if (b) {
          b.click();
          return 'clicked card dl';
        }
      }

      // 3. Coba klik video untuk membuka preview dialog
      const v = document.querySelector('video');
      if (v) {
        v.click();
        return 'clicked video to open modal';
      }

      return 'no trigger found';
    })()`,
    returnByValue: true
  });
  console.log('Download trigger result:', dlResult.result.value);

  // Jika klik video membuka modal, klik tombol unduh di modal
  await new Promise(r => setTimeout(r, 2000));
  await send('Runtime.evaluate', {
    expression: `(() => {
      const modalBtn = document.querySelector('.cdk-overlay-container button[aria-label*="Unduh"], .cdk-overlay-container button[aria-label*="Download"]');
      if (modalBtn) modalBtn.click();
    })()`
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

  if (!downloadedFile) {
    throw new Error('Downloaded file not found in Downloads directory');
  }

  console.log('Downloaded file found:', downloadedFile);
  const rawClip = path.join(TARGET_DIR, 'raw_flow_pakvincent.mp4');
  fs.copyFileSync(downloadedFile, rawClip);
  console.log('Saved to:', rawClip);

  const baseName = path.basename(downloadedFile);
  const match = baseName.match(/_([a-f0-9]{8})\.mp4$/i);
  const batchId = match ? match[1] : ('flow_' + Date.now().toString(16));

  execSync(`sqlite3 "${SQLITE_DB}" "UPDATE generation_jobs SET state = 'completed', actual_credits = 16, external_job_id = '${batchId}' WHERE character_id = 'pak_vincent' AND state IN ('running', 'planned', 'submitted');"`);
  console.log('Updated SQLite generation_jobs to completed.');

  ws.close();
  console.log('DONE!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
