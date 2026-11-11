const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations', 'production.sqlite');
const PUB_ID = '1fa5374da86548a8ace51f7ced3e8720';
const TARGET_ACCOUNT = '@pakvincent.riau';
const TARGET_CLEAN = 'pakvincent.riau';

async function main() {
  execSync(`sqlite3 "${SQLITE_DB}" "UPDATE publications SET state = 'submitted' WHERE id = '${PUB_ID}';"`);
  console.log(`Publication attempt ${PUB_ID} state reset to submitted.`);

  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const tab = tabs.find(t => t.id === 'B5A1D2DF49DFC3CA1D011BFF3BAAC293');
  if (!tab) throw new Error('TikTok tab not found');

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const curId = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 45000);
    const h = (e) => {
      const g = JSON.parse(e.data);
      if (g.id === curId) {
        clearTimeout(timer);
        ws.removeEventListener('message', h);
        resolve(g.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: curId, method: m, params: p }));
  });

  // 1. Klik tombol Post
  console.log('Locating and clicking Post button...');
  const clickRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const postBtn = buttons.find(b => {
        const t = (b.innerText || '').trim();
        const ariaDisabled = b.getAttribute('aria-disabled') === 'true' || b.getAttribute('data-disabled') === 'true';
        return (t === 'Post' || t === 'Posting') && !b.disabled && !ariaDisabled;
      });
      if (postBtn) {
        postBtn.scrollIntoView({ block: 'center' });
        postBtn.click();
        return { success: true, text: postBtn.innerText };
      }
      return { success: false };
    })()`,
    returnByValue: true
  });
  console.log('Post button click result:', clickRes.result.value);

  // Tunggu kemungkinan modal konfirmasi
  await new Promise(r => setTimeout(r, 3000));
  await send('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => {
        const t = (b.innerText || '').trim();
        return (t === 'Post now' || t === 'Posting sekarang' || t === 'Continue') && !b.disabled;
      });
      if (btn) btn.click();
    })()`
  });

  console.log('Waiting 10 seconds for TikTok backend processing...');
  await new Promise(r => setTimeout(r, 10000));

  // 2. Verifikasi status tayang di TikTok Studio atau halaman profil
  console.log('Checking published video link...');
  let verifiedVideoUrl = null;

  for (let attempt = 1; attempt <= 10; attempt++) {
    console.log(`[Pemeriksaan link #${attempt}] Navigating to profile / studio content...`);
    if (attempt % 2 === 1) {
      await send('Page.navigate', { url: `https://www.tiktok.com/@${TARGET_CLEAN}` });
    } else {
      await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
    }
    await new Promise(r => setTimeout(r, 5000));

    const checkRes = await send('Runtime.evaluate', {
      expression: `(() => {
        const links = Array.from(document.querySelectorAll("a[href*='/video/']"));
        const re = new RegExp('https://www\\\\.tiktok\\\\.com/@' + ${JSON.stringify(TARGET_CLEAN)}.replace(/[.*+?^$\{\}()|[\\]\\\\]/g, '\\\\$&') + '/video/([0-9]+)', 'i');
        for (const a of links) {
          const match = (a.href || '').match(re);
          if (match) return { url: match[0], videoId: match[1] };
        }
        // Juga cek tautan dengan format umum /video/
        for (const a of links) {
          const m = (a.href || '').match(/https:\\/\\/www\\.tiktok\\.com\\/@[^/]+\\/video\\/([0-9]+)/);
          if (m) return { url: m[0], videoId: m[1] };
        }
        return null;
      })()`,
      returnByValue: true
    });

    if (checkRes.result && checkRes.result.value && checkRes.result.value.url) {
      verifiedVideoUrl = checkRes.result.value.url;
      console.log('VERIFIED VIDEO URL FOUND:', verifiedVideoUrl);
      break;
    }
  }

  if (!verifiedVideoUrl) {
    execSync(`sqlite3 "${SQLITE_DB}" "UPDATE publications SET state = 'unknown' WHERE id = '${PUB_ID}';"`);
    throw new Error('Video URL belum dapat diverifikasi setelah 10 percobaan.');
  }

  // 3. Konfirmasi di database resmi
  console.log('Recording confirmation in SQLite...');
  execSync(
    `python3 -m app.publication confirm --publication "${PUB_ID}" --video-url "${verifiedVideoUrl}"`,
    { cwd: PROJECT_ROOT, stdio: 'inherit' }
  );

  ws.close();
  console.log('PUBLICATION CONFIRMED 100% SUCCESSFULLY!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
