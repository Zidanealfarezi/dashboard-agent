#!/usr/bin/env node
throw new Error('Jalur ad-hoc dinonaktifkan. Gunakan scripts/tiktok_publisher.js atau app.publication sesuai docs/production-controls.md');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations', 'production.sqlite');
const VERSION_ID = 'ver_isk_pk006_rev1_1794273764';
const CAPTION = 'Pekerjaan konstruksi butuh material yang presisi dan tidak gampang bengkok. Paku Cap Keris hadir dengan jaminan timbangan pas 25 kg dan standar mutu ekspor. Komentar KATALOG untuk mendapatkan tautan WhatsApp pemesanan langsung lewat DM.';

async function main() {
  const ws = new WebSocket('ws://127.0.0.1:9333/devtools/page/86AB88171ECAE9F5F3C30735B507BAE4');
  await new Promise(r => ws.addEventListener('open', r));
  let msgId = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const curId = msgId++;
    const timer = setTimeout(() => reject(new Error('CDP Timeout: ' + m)), 45000);
    const h = (e) => {
      const g = JSON.parse(e.data);
      if (g.id === curId) {
        clearTimeout(timer);
        ws.removeEventListener('message', h);
        if (g.error) reject(new Error(JSON.stringify(g.error)));
        else resolve(g.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: curId, method: m, params: p }));
  });

  console.log('Connected to TikTok Studio tab.');

  // 1. Focus dan isi caption
  console.log('Focusing caption editor...');
  const focusEditor = await send('Runtime.evaluate', {
    expression: `(() => {
      window.scrollTo(0, 0);
      const el = document.querySelector('[contenteditable="true"]');
      if (!el) return null;
      el.focus();
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2) };
    })()`,
    returnByValue: true
  });

  if (!focusEditor.result.value) throw new Error('Editor not found');
  const { x, y } = focusEditor.result.value;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  await new Promise(r => setTimeout(r, 300));

  await send('Runtime.evaluate', {
    expression: `(() => {
      const el = document.querySelector('[contenteditable="true"]');
      if (el) {
        el.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
      }
    })()`
  });
  await new Promise(r => setTimeout(r, 300));

  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
  await new Promise(r => setTimeout(r, 300));

  console.log('Typing caption via Input.insertText...');
  await send('Input.insertText', { text: CAPTION });
  await new Promise(r => setTimeout(r, 1200));

  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await new Promise(r => setTimeout(r, 600));

  // 2. Verifikasi caption
  const verifyCaption = await send('Runtime.evaluate', {
    expression: `(() => {
      const el = document.querySelector('[contenteditable="true"]');
      return el ? el.innerText.trim() : '';
    })()`,
    returnByValue: true
  });
  console.log('Caption in editor:', verifyCaption.result.value.slice(0, 60) + '...');
  if (!verifyCaption.result.value.includes('Pekerjaan konstruksi')) {
    throw new Error('Caption verification failed in editor: ' + verifyCaption.result.value);
  }

  // 3. Cari dan klik tombol Posting
  console.log('Locating Posting button...');
  const postBtn = await send('Runtime.evaluate', {
    expression: `(() => {
      window.scrollTo(0, document.body.scrollHeight);
      const btns = Array.from(document.querySelectorAll('button')).filter(b => {
        const t = b.innerText.trim();
        return t === 'Posting' || t === 'Post';
      });
      if (btns.length === 0) return null;
      const b = btns[0];
      const r = b.getBoundingClientRect();
      return { x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true' };
    })()`,
    returnByValue: true
  });

  console.log('Posting button info:', postBtn.result.value);
  if (!postBtn.result.value || postBtn.result.value.disabled) {
    throw new Error('Posting button not ready or disabled');
  }

  console.log('Clicking Posting button...');
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: postBtn.result.value.x, y: postBtn.result.value.y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: postBtn.result.value.x, y: postBtn.result.value.y, button: 'left', clickCount: 1 });

  // 4. Pantau posting selesai
  console.log('Waiting for post submission confirmation...');
  let postSuccess = false;
  for (let s = 0; s < 25; s++) {
    await new Promise(r => setTimeout(r, 2000));
    const pageStatus = await send('Runtime.evaluate', {
      expression: `(() => {
        const text = document.body.innerText;
        const manageBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Kelola postingan') || b.innerText.includes('Manage'));
        if (manageBtn) {
          manageBtn.click();
          return { done: true, clickedManage: true };
        }
        if (text.includes('telah diposting') || text.includes('uploaded') || text.includes('Manage your posts') || window.location.href.includes('tiktokstudio/content')) {
          return { done: true, clickedManage: false };
        }
        return { done: false };
      })()`,
      returnByValue: true
    });

    if (pageStatus.result.value && pageStatus.result.value.done) {
      console.log('Post submission detected! Details:', pageStatus.result.value);
      postSuccess = true;
      break;
    }
  }

  if (!postSuccess) {
    throw new Error('Posting timed out or confirmation modal not found');
  }

  // 5. Buka tiktokstudio/content dan ambil numeric post ID
  console.log('Navigating to content manager to verify numeric post ID...');
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 6000));

  let verifiedVideoId = null;
  let verifiedUrl = null;

  for (let c = 0; c < 15; c++) {
    const postData = await send('Runtime.evaluate', {
      expression: `(() => {
        const links = Array.from(document.querySelectorAll('a[href*="/video/"]')).map(a => a.href);
        const uniqueLinks = Array.from(new Set(links));
        return uniqueLinks;
      })()`,
      returnByValue: true
    });

    console.log(`[Pemeriksaan #${c+1}] Found video links:`, postData.result.value);
    if (postData.result.value && postData.result.value.length > 0) {
      verifiedUrl = postData.result.value[0];
      const match = verifiedUrl.match(/video\/(\d+)/);
      if (match) {
        verifiedVideoId = match[1];
        break;
      }
    }
    await new Promise(r => setTimeout(r, 3000));
  }

  if (!verifiedVideoId) {
    throw new Error('Failed to verify numeric video ID on TikTok Studio');
  }

  console.log('VERIFIED PUBLISHED VIDEO ID:', verifiedVideoId);
  console.log('VERIFIED LIVE URL:', verifiedUrl);

  // 6. Catat publikasi confirmed di SQLite
  const pubId = 'pub_' + Date.now();
  const idempotencyKey = 'pub_idempotency_' + VERSION_ID;
  const nowIso = new Date().toISOString();

  execSync(`sqlite3 "${SQLITE_DB}" "INSERT OR REPLACE INTO publications (id, version_id, idempotency_key, state, platform_post_id, post_url, published_at) VALUES ('${pubId}', '${VERSION_ID}', '${idempotencyKey}', 'confirmed', '${verifiedVideoId}', '${verifiedUrl}', '${nowIso}');"`);
  console.log('Publication confirmed in SQLite publications table.');

  ws.close();
  console.log('SUCCESS! ISK Video published and verified live.');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
