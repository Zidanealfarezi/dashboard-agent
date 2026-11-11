throw new Error('Jalur lama Flow dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const path = require('path');

const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content';

async function run() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json')).json();
  const flowTab = tabs.find(t => t.url && t.url.includes('flow.google.com'));
  if (!flowTab) throw new Error('Flow tab not found');

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const msgId = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + method)), 35000);
    const handler = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === msgId) {
        clearTimeout(timer);
        ws.removeEventListener('message', handler);
        resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });
  await new Promise(r => ws.addEventListener('open', r));

  console.log('Connected to Flow CDP for Shot 2.');

  // 1. Click Done if in detail view
  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Done' || b.getAttribute('aria-label') === 'Done editing scene');
      if (btn) btn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1200));

  // 2. Set prompt for Shot 2
  const promptShot2 = `Authentic handheld smartphone vlog video of Dinda Kemala from character reference sheets inside SOREE Cafe Jalan Veteran in Palembang on Saturday night. Medium close-up framing, vertical 9:16 aspect ratio. Dinda wears her striped taupe-khaki knit cardigan, neat soft beige pashmina hijab, and small gold ring pendant necklace matching the reference sheets. Natural soft white balance 5500K, realistic matte human skin with fine pores, strictly zero plastic AI slop, no heavy yellow filter. Dinda sets down her coffee cup on the wooden table, smiles warmly and speaks directly to the camera in natural conversational Indonesian: "Tempatnya selalu rame anak muda Palembang tapi tetap dapet cozy vibes-nya. Kalau kalian malam minggu biasanya nongkrong di mana nih? Cerita di komen ya!" Natural lip-sync ending at second 6.5, clear authentic Indonesian female voice, documentary smartphone camera aesthetic, no subtitles.`;

  await send('Runtime.evaluate', {
    expression: `(() => {
      const pm = document.querySelector('.ProseMirror');
      if (pm) {
        pm.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
      }
    })()`
  });
  await new Promise(r => setTimeout(r, 400));
  await send('Input.insertText', { text: promptShot2 });
  await new Promise(r => setTimeout(r, 800));

  // 3. Click generate button
  console.log('Clicking Start generation for Shot 2...');
  const clickRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Start generation');
      if (!btn) return { success: false, reason: 'Btn not found' };
      if (btn.disabled) return { success: false, reason: 'Btn disabled' };
      btn.click();
      return { success: true };
    })()`,
    returnByValue: true
  });
  console.log('Generate click result:', clickRes.result.value);

  // 4. Wait for generation to complete
  console.log('Monitoring Shot 2 generation...');
  let finished = false;
  let attempts = 0;

  while (!finished && attempts < 60) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));

    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const batch = document.querySelector('.batch-container');
        if (!batch) return { exists: false };
        const text = batch.innerText.replace(/\\s+/g, ' ');
        const isTarget = text.toLowerCase().includes('anak muda palembang');
        const isGen = text.includes('%') || text.includes('Generating');
        return { exists: true, isTarget, isGen, snippet: text.slice(0, 100) };
      })()`,
      returnByValue: true
    });

    const val = status.result.value;
    console.log(`[Attempt ${attempts}] isTarget: ${val.isTarget} | isGen: ${val.isGen} | ${val.snippet}`);

    if (val.isTarget && !val.isGen) {
      console.log('Shot 2 generation completed in Flow!');
      finished = true;
      break;
    }
  }

  if (!finished) throw new Error('Timeout waiting for Shot 2');

  // Wait 2s for UI to stabilize
  await new Promise(r => setTimeout(r, 2000));

  // 5. Download Shot 2
  console.log('Downloading Shot 2...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const topBatch = document.querySelector('.batch-container');
      const thumb = topBatch ? topBatch.querySelector('img.thumbnail, [class*="thumb"], button[aria-label*="Woman"]') : null;
      if (thumb) thumb.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1500));

  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Download media' || b.innerText.trim() === 'download');
      if (btn) btn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 800));

  await send('Runtime.evaluate', {
    expression: `(() => {
      const menuItems = Array.from(document.querySelectorAll('.cdk-overlay-pane button, [role="menuitem"]'));
      const opt = menuItems.find(m => m.innerText.includes('720p') || m.innerText.includes('Original') || m.innerText.includes('Download'));
      if (opt) opt.click();
    })()`
  });

  // Wait 5s for download to finish
  console.log('Waiting for download to finish in ~/Downloads...');
  await new Promise(r => setTimeout(r, 5000));

  // Find downloaded file
  const files = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
  console.log('Downloaded files:', files);

  if (files.length === 0) throw new Error('No mp4 downloaded in ~/Downloads');

  const latestFile = files[0];
  const srcPath = path.join(DOWNLOADS_DIR, latestFile);
  const destPath = path.join(CONTENT_DIR, 'dinda_soree_shot2_8s.mp4');

  fs.copyFileSync(srcPath, destPath);
  fs.unlinkSync(srcPath);
  console.log(`Shot 2 successfully saved to ${destPath}`);

  ws.close();
}

run().catch((err) => {
  console.error('Shot 2 Error:', err);
  process.exit(1);
});
