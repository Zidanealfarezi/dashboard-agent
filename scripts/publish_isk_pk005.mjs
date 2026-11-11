throw new Error('Jalur ad-hoc dinonaktifkan. Gunakan scripts/tiktok_publisher.js atau app.publication sesuai docs/production-controls.md');

import fs from 'fs';

const ARTIFACT_DIR = '/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46';
const VIDEO_PATH = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/isk/content/ISK_PK_005/ISK_PK_005_banting_tang_final.mp4';
const CAPTION = 'Paku baru dihantam sekali langsung bengkok? Pakai Paku Cap Keris dari PT Intan Suar Kartika, batang baja kokoh anti bengkok dan timbangan pas 25 kg. Pemesanan via WA 08198889350 (wa.me/628198889350). #pakucapkeris #intansuarkartika #tokobangunan';

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

  // Step 4: Wait for file processing (10 seconds)
  console.log('Waiting for video processing...');
  await new Promise(r => setTimeout(r, 10000));

  // Step 5: Check page text
  const stateCheck = await send('Runtime.evaluate', {
    expression: 'document.body.innerText.slice(0, 500)',
    returnByValue: true
  });
  console.log('Page state after file set:', stateCheck.result.value);

  // Step 6: Set Caption
  console.log('Setting caption...');
  const setCaptionExpr = `
    (() => {
      const el = document.querySelector('[contenteditable="true"]');
      if (!el) return { success: false, reason: 'contenteditable not found' };
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, ${JSON.stringify(CAPTION)});
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return { success: true, text: el.innerText };
    })()
  `;
  const captionRes = await send('Runtime.evaluate', { expression: setCaptionExpr, returnByValue: true });
  console.log('Caption set result:', captionRes.result.value);
  await new Promise(r => setTimeout(r, 3000));

  // Step 7: Take screenshot before posting
  console.log('Capturing screenshot before posting...');
  const shotBefore = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync(`${ARTIFACT_DIR}/pk005_tiktok_before_post.jpg`, Buffer.from(shotBefore.data, 'base64'));
  console.log('Saved pk005_tiktok_before_post.jpg');

  // Step 8: Click Post button
  console.log('Looking for Post / Posting button...');
  const clickPostExpr = `
    (() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const postBtn = buttons.find(b => {
        const t = b.innerText.trim();
        return (t === 'Post' || t === 'Posting' || t === 'Unggah') && !b.disabled;
      });
      if (!postBtn) {
        return { success: false, reason: 'Post button not found', buttons: buttons.map(b => b.innerText.trim()).filter(Boolean) };
      }
      postBtn.click();
      return { success: true, buttonText: postBtn.innerText.trim() };
    })()
  `;
  const postRes = await send('Runtime.evaluate', { expression: clickPostExpr, returnByValue: true });
  console.log('Post click result:', postRes.result.value);

  // Step 9: Wait 8 seconds
  console.log('Waiting 8 seconds after clicking post...');
  await new Promise(r => setTimeout(r, 8000));

  // Step 10: Take screenshot after posting
  console.log('Capturing screenshot after posting...');
  const shotAfter = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync(`${ARTIFACT_DIR}/pk005_tiktok_after_post.jpg`, Buffer.from(shotAfter.data, 'base64'));
  console.log('Saved pk005_tiktok_after_post.jpg');

  // Step 11: Check after post status
  const afterCheck = await send('Runtime.evaluate', {
    expression: '({ url: location.href, text: document.body.innerText.slice(0, 800) })',
    returnByValue: true
  });
  console.log('After post state:', afterCheck.result.value);

  ws.close();
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
