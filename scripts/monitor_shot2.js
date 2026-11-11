const fs = require('fs');
const path = require('path');

const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content';

async function monitorAndDownloadShot2() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json')).json();
  const flowTab = tabs.find(t => t.url && t.url.includes('flow.google.com'));
  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise(r => {
    const msgId = id++;
    const handler = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === msgId) {
        ws.removeEventListener('message', handler);
        r(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id: msgId, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));

  console.log('Monitoring Batch 0 for Shot 2 completion...');
  let finished = false;
  let attempts = 0;

  while (!finished && attempts < 50) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));

    const check = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { text: 'no top' };
        const text = top.innerText;
        const isDone = text.includes('download') && !text.includes('%') && !text.includes('Generating');
        return { isDone, textSnippet: text.slice(0, 100) };
      })()`,
      returnByValue: true
    });

    console.log(`[Attempt ${attempts}] isDone: ${check.result.value.isDone} | ${check.result.value.textSnippet.replace(/\\s+/g, ' ')}`);

    if (check.result.value.isDone) {
      console.log('Shot 2 generation is 100% complete!');
      finished = true;
      break;
    }
  }

  if (!finished) throw new Error('Timeout waiting for Shot 2');

  // Click top batch thumbnail
  console.log('Opening detail view for Shot 2...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const thumb = top ? top.querySelector('img.thumbnail, [class*="thumb"], button[aria-label*="Woman"]') : null;
      if (thumb) thumb.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1500));

  // Click download button
  console.log('Clicking Download...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Download media' || b.innerText.trim() === 'download');
      if (btn) btn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 800));

  // Click 720p option
  await send('Runtime.evaluate', {
    expression: `(() => {
      const menuItems = Array.from(document.querySelectorAll('.cdk-overlay-pane button, [role="menuitem"]'));
      const opt = menuItems.find(m => m.innerText.includes('720p') || m.innerText.includes('Original') || m.innerText.includes('Download'));
      if (opt) opt.click();
    })()`
  });

  console.log('Waiting for download to finish in ~/Downloads...');
  await new Promise(r => setTimeout(r, 6000));

  const files = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
  console.log('Downloaded files in Downloads:', files);

  if (files.length === 0) throw new Error('No mp4 file found in ~/Downloads');

  const srcPath = path.join(DOWNLOADS_DIR, files[0]);
  const destPath = path.join(CONTENT_DIR, 'dinda_soree_shot2_8s.mp4');

  fs.copyFileSync(srcPath, destPath);
  fs.unlinkSync(srcPath);
  console.log(`Shot 2 successfully saved to ${destPath}`);

  ws.close();
}

monitorAndDownloadShot2().catch(console.error);
