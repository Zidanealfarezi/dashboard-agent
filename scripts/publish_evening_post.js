throw new Error('Jalur lama TikTok dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');

async function main() {
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  let ttTab = tabs.find(t => t.url.includes('tiktokstudio'));
  if (!ttTab) {
    throw new Error('TikTok Studio tab not found on port 9333');
  }

  const ws = new WebSocket(ttTab.webSocketDebuggerUrl);

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = Math.floor(Math.random() * 1000000);
      const timeout = setTimeout(() => {
        ws.removeEventListener('message', handler);
        reject(new Error(`Timeout waiting for CDP method ${method}`));
      }, 30000);
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

  await new Promise((resolve) => { ws.onopen = resolve; });
  console.log('Connected to TikTok Studio tab via CDP');

  // Navigate to upload page
  console.log('Navigating to upload page...');
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video' });

  // Wait 6 seconds for upload page to load
  await new Promise(r => setTimeout(r, 6000));

  // Find file input
  const doc = await send('DOM.getDocument');
  const inputNode = await send('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });
  console.log('Input node:', inputNode);

  if (!inputNode || !inputNode.nodeId) {
    throw new Error('File input node not found');
  }

  const videoPath = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content/dinda_palembang_malam_15s.mp4';
  if (!fs.existsSync(videoPath)) {
    throw new Error(`Video file does not exist: ${videoPath}`);
  }

  console.log('Setting file:', videoPath);
  await send('DOM.setFileInputFiles', {
    files: [videoPath],
    nodeId: inputNode.nodeId
  });

  // Wait 8 seconds for video upload and processing
  console.log('Waiting for video processing...');
  await new Promise(r => setTimeout(r, 8000));

  // Check upload state
  const stateCheck = await send('Runtime.evaluate', {
    expression: 'document.body.innerText.slice(0, 800)',
    returnByValue: true
  });
  console.log('Page text after upload:', stateCheck.result.value);

  // Set Caption
  const captionText = 'Malam di Palembang emang gak pernah gagal. Mandangin lampu Jembatan Ampera dari tepian Sungai Musi hawanya adem banget bikin betah. Kalau kalian biasanya malam gini nongkrong di mana? #palembang #jembatanampera #sungaimusi #malamditiktok #dindakemala #vlogmalam';

  const updateCaptionExpr = `
    (() => {
      const el = document.querySelector('[contenteditable="true"]');
      if (!el) return { success: false, reason: 'contenteditable not found' };
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, ${JSON.stringify(captionText)});
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return { success: true, text: el.innerText };
    })()
  `;
  const updateCaptionRes = await send('Runtime.evaluate', { expression: updateCaptionExpr, returnByValue: true });
  console.log('Caption update:', updateCaptionRes.result.value);

  // Wait 3 seconds
  await new Promise(r => setTimeout(r, 3000));

  // Verify visibility option (Ensure "Everyone" / Public is selected)
  const visibilityExpr = `
    (() => {
      const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
      const labels = Array.from(document.querySelectorAll('label, div, span'));
      const everyoneLabel = labels.find(l => l.innerText && l.innerText.trim() === 'Everyone');
      if (everyoneLabel) {
        everyoneLabel.click();
        return 'Clicked Everyone label';
      }
      return 'Everyone label not found';
    })()
  `;
  const visRes = await send('Runtime.evaluate', { expression: visibilityExpr, returnByValue: true });
  console.log('Visibility check:', visRes.result.value);

  // Take screenshot before posting
  const shotBefore = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/evening_post_before_click.jpg', Buffer.from(shotBefore.data, 'base64'));
  console.log('Saved evening_post_before_click.jpg');

  // Click Post button
  console.log('Looking for Post button...');
  const clickPostExpr = `
    (() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText.trim() === 'Post' && !b.disabled);
      if (!postBtn) {
        return { success: false, reason: 'Post button not found or disabled', buttons: buttons.map(b => b.innerText.trim()) };
      }
      postBtn.click();
      return { success: true };
    })()
  `;
  const postRes = await send('Runtime.evaluate', { expression: clickPostExpr, returnByValue: true });
  console.log('Post click result:', postRes.result.value);

  // Wait 7 seconds
  await new Promise(r => setTimeout(r, 7000));

  // Take screenshot after posting
  const shotAfter = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/evening_post_after_click.jpg', Buffer.from(shotAfter.data, 'base64'));
  console.log('Saved evening_post_after_click.jpg');

  const afterState = await send('Runtime.evaluate', {
    expression: '({url: location.href, text: document.body.innerText.slice(0, 1000)})',
    returnByValue: true
  });
  console.log('After post state:', afterState.result.value);

  ws.close();
}

main().catch(console.error);
