throw new Error('Jalur lama Flow dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content';

async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json')).json();
  const flowTab = tabs.find(t => t.url && t.url.includes('flow.google.com'));
  if (!flowTab) throw new Error('Flow tab not found');

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const msgId = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 35000);
    const handler = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === msgId) {
        clearTimeout(timer);
        ws.removeEventListener('message', handler);
        resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id: msgId, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));

  console.log('Connected to Flow CDP for Shot 2 re-generation with full face references.');

  // Verify chips are present
  const chipsCheck = await send('Runtime.evaluate', {
    expression: `(() => {
      const pBox = document.querySelector('flow-base-prompt-box');
      const chips = pBox ? Array.from(pBox.querySelectorAll('flow-ingredient-chip, [class*="chip"]')).map(c => c.innerText.trim()).filter(Boolean) : [];
      return chips;
    })()`,
    returnByValue: true
  });
  console.log('Chips before prompt:', chipsCheck.result.value);

  // Set Shot 2 Prompt
  const promptShot2 = `Authentic handheld smartphone vlog video of Dinda Kemala strictly matching her facial features, hijab, and outfit from the attached reference sheets inside SOREE Cafe Jalan Veteran in Palembang on Saturday night. Medium close-up framing, vertical 9:16 aspect ratio. Dinda wears her striped taupe-khaki knit cardigan, neat soft beige pashmina hijab, and small gold ring pendant necklace strictly matching the reference sheets. Natural soft white balance 5500K, realistic matte human skin with visible fine pores and authentic texture, strictly zero plastic AI slop, no heavy yellow or orange filter. Dinda sets down her coffee cup on the wooden table, smiles playfully with conversational warmth, speaking directly to the camera in natural conversational Indonesian: "Tempatnya selalu rame anak muda Palembang tapi tetap dapet cozy vibes-nya. Kalau kalian malam minggu biasanya nongkrong di mana nih? Cerita di komen ya!" Natural lip-sync ending at second 6.5, clear authentic Indonesian female voice, documentary smartphone camera aesthetic, no subtitles.`;

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

  // Trigger generation
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
  console.log('Generate result:', clickRes.result.value);
  if (!clickRes.result.value.success) throw new Error('Failed to click generate');

  // Monitor generation
  console.log('Monitoring generation of Shot 2 (with face chips)...');
  // Wait 10s initially for the new batch to be registered
  await new Promise(r => setTimeout(r, 10000));

  let finished = false;
  let attempts = 0;

  while (!finished && attempts < 60) {
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
      console.log('Shot 2 with face chips generation is 100% complete!');
      finished = true;
      break;
    }
  }

  if (!finished) throw new Error('Timeout waiting for Shot 2 generation');

  await new Promise(r => setTimeout(r, 2000));

  // Open detail view
  console.log('Opening detail view for Shot 2...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const thumb = top ? top.querySelector('img.thumbnail, [class*="thumb"], button[aria-label*="Woman"]') : null;
      if (thumb) thumb.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1500));

  // Click Download
  console.log('Clicking Download...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Download media' || b.innerText.trim() === 'download');
      if (btn) btn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 800));

  // Click 720p
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
  console.log('Downloaded files:', files);
  if (files.length === 0) throw new Error('No mp4 downloaded');

  const srcPath = path.join(DOWNLOADS_DIR, files[0]);
  const destPath = path.join(CONTENT_DIR, 'dinda_soree_shot2_8s.mp4');
  fs.copyFileSync(srcPath, destPath);
  fs.unlinkSync(srcPath);
  console.log(`Shot 2 successfully saved to ${destPath}`);

  ws.close();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
