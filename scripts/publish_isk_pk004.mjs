throw new Error('Jalur ad-hoc dinonaktifkan. Gunakan scripts/tiktok_publisher.js atau app.publication sesuai docs/production-controls.md');

import fs from 'fs';

const ARTIFACT_DIR = '/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46';
const VIDEO_PATH = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/isk/content/ISK_PK_004/ISK_PK_004_toko_material_final.mp4';
const CAPTION = 'Rahasia mandor proyek selalu balik belanja: Paku Cap Keris jaminan timbangan pas 25 kg dan baja kokoh anti bengkok. Pemesanan via WA 08198889350 (wa.me/628198889350). #pakucapkeris #intansuarkartika #bahanbangunan';

async function main() {
  if (!fs.existsSync(VIDEO_PATH)) {
    throw new Error(`Video file does not exist: ${VIDEO_PATH}`);
  }

  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const ttTab = tabs.find(t => t.url.includes('tiktokstudio') && t.type === 'page');
  if (!ttTab) {
    throw new Error('TikTok Studio tab not found on port 9333');
  }
  console.log('Target tab:', ttTab.id, ttTab.url);

  const ws = new WebSocket(ttTab.webSocketDebuggerUrl);

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = Math.floor(Math.random() * 1000000);
      const timeout = setTimeout(() => {
        ws.removeEventListener('message', handler);
        reject(new Error(`Timeout waiting for CDP method ${method}`));
      }, 45000);
      const handler = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === id) {
          clearTimeout(timeout);
          ws.removeEventListener('message', handler);
          if (msg.error) reject(new Error(JSON.stringify(msg.error)));
          else resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await new Promise(r => ws.onopen = r);
  console.log('Connected to TikTok Studio CDP');

  // Step 1: Navigate to upload page
  console.log('Navigating to upload page...');
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video' });
  await new Promise(r => setTimeout(r, 6000));

  // Step 2: Locate file input
  console.log('Locating file input...');
  const doc = await send('DOM.getDocument');
  const inputNode = await send('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });
  console.log('Input node:', inputNode);

  if (!inputNode || !inputNode.nodeId) {
    throw new Error('File input node not found');
  }

  // Step 3: Set video file
  console.log('Setting file:', VIDEO_PATH);
  await send('DOM.setFileInputFiles', {
    files: [VIDEO_PATH],
    nodeId: inputNode.nodeId
  });

  // Step 4: Wait for file processing (12 seconds)
  console.log('Waiting for video processing...');
  await new Promise(r => setTimeout(r, 12000));

  // Step 5: Dismiss any modals
  console.log('Dismissing modals if any...');
  await send('Runtime.evaluate', {
    expression: `
      (() => {
        const mengerti = Array.from(document.querySelectorAll("button")).find(b => b.innerText.trim() === "Mengerti");
        if (mengerti) mengerti.click();

        const aktifkan = Array.from(document.querySelectorAll("button")).find(b => b.innerText.trim() === "Aktifkan");
        if (aktifkan) aktifkan.click();
      })()
    `
  });
  await new Promise(r => setTimeout(r, 1500));

  // Step 6: Set Caption
  console.log('Setting caption...');
  const setCaptionExpr = `
    (() => {
      const el = document.querySelector('[contenteditable="true"]');
      if (!el) return { success: false, reason: 'contenteditable not found' };
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, ${JSON.stringify(CAPTION)});
      return { success: true, text: el.innerText };
    })()
  `;
  const captionRes = await send('Runtime.evaluate', { expression: setCaptionExpr, returnByValue: true });
  console.log('Caption set result:', captionRes.result.value);
  await new Promise(r => setTimeout(r, 2000));

  // Step 7: Screenshot before posting
  console.log('Capturing screenshot before posting...');
  const shotBefore = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync(`${ARTIFACT_DIR}/pk004_tiktok_before_post.jpg`, Buffer.from(shotBefore.data, 'base64'));
  console.log('Saved pk004_tiktok_before_post.jpg');

  // Step 8: Click Posting button
  console.log('Clicking Posting button...');
  const clickPostExpr = `
    (() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Posting' && !b.disabled);
      if (!btn) return { success: false, reason: 'Posting button not found or disabled' };
      btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
      btn.click();
      return { success: true };
    })()
  `;
  const postRes = await send('Runtime.evaluate', { expression: clickPostExpr, returnByValue: true });
  console.log('Posting click result:', postRes.result.value);

  // Step 9: Wait 2.5s and check for confirmation modal ("Posting sekarang")
  await new Promise(r => setTimeout(r, 2500));
  console.log('Checking for confirmation modal (Posting sekarang)...');
  const confirmRes = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Posting sekarang' && !b.disabled);
        if (btn) {
          btn.click();
          return { clickedConfirm: true };
        }
        return { clickedConfirm: false };
      })()
    `,
    returnByValue: true
  });
  console.log('Confirmation check result:', confirmRes.result.value);

  // Step 10: Wait 10 seconds for completion
  console.log('Waiting 10 seconds for post to complete...');
  await new Promise(r => setTimeout(r, 10000));

  // Step 11: Screenshot after post
  const shotAfter = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync(`${ARTIFACT_DIR}/pk004_tiktok_after_post.jpg`, Buffer.from(shotAfter.data, 'base64'));
  console.log('Saved pk004_tiktok_after_post.jpg');

  // Step 12: Reload content page to verify
  console.log('Reloading content page to verify listing...');
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 6000));

  const shotContent = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync(`${ARTIFACT_DIR}/pk004_tiktok_studio_live.jpg`, Buffer.from(shotContent.data, 'base64'));
  console.log('Saved pk004_tiktok_studio_live.jpg');

  const contentText = await send('Runtime.evaluate', {
    expression: 'document.body.innerText.slice(0, 1000)',
    returnByValue: true
  });
  console.log('Content list top text:', contentText.result.value);

  ws.close();
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
