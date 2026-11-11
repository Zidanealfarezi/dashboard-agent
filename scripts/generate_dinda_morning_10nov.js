const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/dinda/content/dinda-pagi-palembang-2026-11-10');
const JOB_ID = 'ea42a7adfa8a4aea8e434d7a4487d3a8';

const PROMPT = `Authentic handheld smartphone vlog video of Dinda Kemala, the same Indonesian woman shown in all three attached reference images. Output exactly one woman, never a collage, split screen or reference-sheet layout. Vertical 9:16, one continuous shot, medium close-up standing outside near Museum Sultan Mahmud Badaruddin II Palembang in the soft morning daylight. She is wearing a sage green crinkle linen blouse, cream culottes, and a neat cream pashmina hijab with a small gold ring necklace. Daylight neutral white balance at 5500K, true-to-life colors, realistic matte human skin with visible fine pores, no plastic shine, no waxy skin, no glass skin, no yellow or orange tint, no artificial golden glow, zero CGI, authentic non-AI documentary look. She smiles warmly at the camera, speaks naturally to the lens about the upcoming traditional game event, gesturing gently with her hand. Handheld vertical 9:16 framing, subject centered, stable face, natural micro-expressions, honest morning vlog atmosphere, no text overlay, no logo.`;

async function main() {
  if (!fs.existsSync(TARGET_DIR)) {
    fs.mkdirSync(TARGET_DIR, { recursive: true });
  }

  // Bersihkan file MP4 lama di Downloads
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const dindaTab = tabs.find(t => t.url && t.url.includes('3e9fe2ca-ee39-4235-81a1-9d8bfdee9603') && t.type === 'page');
  if (!dindaTab) throw new Error('Dinda Flow tab not found on port 9333');

  const ws = new WebSocket(dindaTab.webSocketDebuggerUrl);
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

  console.log('Connected to Dinda Flow tab.');

  // Set download behavior
  await send('Page.enable');
  await send('Browser.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: DOWNLOADS_DIR
  });

  // 1. Pastikan teks prompt terisi
  console.log('Setting prompt text in ProseMirror...');
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
  await send('Input.insertText', { text: PROMPT });
  await new Promise(r => setTimeout(r, 1000));

  // 2. Set durasi 10s via settings modal bila belum 10s
  const currentSettings = await send('Runtime.evaluate', {
    expression: "document.querySelector('button[aria-label=\"Settings trigger\"]').innerText",
    returnByValue: true
  });
  console.log('Current settings text:', currentSettings.result.value);

  if (!currentSettings.result.value.includes('10s')) {
    console.log('Opening settings trigger to select 10s...');
    await send('Runtime.evaluate', {
      expression: `(() => {
        const btn = document.querySelector('button[aria-label="Settings trigger"]');
        if (btn) btn.click();
      })()`
    });
    await new Promise(r => setTimeout(r, 1000));

    const selected10s = await send('Runtime.evaluate', {
      expression: `(() => {
        const overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) return false;
        const all = Array.from(overlay.querySelectorAll('button, [role=button], mat-button-toggle, [class*=toggle]'));
        const target = all.find(b => b.innerText.trim() === '10s');
        if (target) {
          target.click();
          return true;
        }
        return false;
      })()`,
      returnByValue: true
    });
    console.log('Selected 10s toggle:', selected10s.result.value);
    await new Promise(r => setTimeout(r, 1000));

    // Close settings modal
    await send('Runtime.evaluate', {
      expression: `(() => {
        const backdrop = document.querySelector('.cdk-overlay-backdrop');
        if (backdrop) backdrop.click();
        else {
          const btn = document.querySelector('button[aria-label="Settings trigger"]');
          if (btn) btn.click();
        }
      })()`
    });
    await new Promise(r => setTimeout(r, 1000));
  }

  // 3. Verifikasi tombol Start generation
  const genBtn = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Start generation');
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, disabled: btn.disabled || btn.getAttribute('aria-disabled') === 'true' };
    })()`,
    returnByValue: true
  });
  console.log('Gen button status:', genBtn.result.value);
  if (!genBtn.result.value || genBtn.result.value.disabled) {
    throw new Error('Generate button not ready or disabled');
  }

  // 4. Update SQLite state to 'running'
  execSync(`sqlite3 "${path.join(PROJECT_ROOT, 'operations/production.sqlite')}" "UPDATE generation_jobs SET state = 'running' WHERE id = '${JOB_ID}';"`);
  console.log('Job state updated to running in SQLite.');

  // 5. Klik Start Generation
  console.log('Clicking Start generation...');
  const { x, y } = genBtn.result.value;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  console.log('Start generation clicked!');

  // 6. Pantau proses generate sampai selesai
  console.log('Waiting for generation batch to appear and complete...');
  await new Promise(r => setTimeout(r, 12000));

  let completed = false;
  let attempts = 0;
  while (!completed && attempts < 90) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));
    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { text: 'no container' };
        const text = top.innerText.replace(/\\s+/g, ' ');
        const isDone = text.includes('download') && !text.includes('%') && !text.includes('Generating');
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

  if (!completed) throw new Error('Timeout waiting for Flow render');
  console.log('Render 100% completed!');

  // 7. Unduh video langsung dari download button
  await new Promise(r => setTimeout(r, 3000));
  console.log('Clicking Download media...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const btn = top ? top.querySelector('button[aria-label="Download"], button[aria-label="Download media"]') : null;
      if (btn) {
        btn.click();
        return 'clicked top batch download';
      }
      const anyBtn = Array.from(document.querySelectorAll('button')).find(b => (b.getAttribute('aria-label')||'').toLowerCase().includes('download'));
      if (anyBtn) {
        anyBtn.click();
        return 'clicked any download';
      }
      return 'no download button found';
    })()`,
    returnByValue: true
  });

  // Tunggu file muncul di Downloads
  console.log('Waiting for file in Downloads...');
  let downloadedFile = null;
  for (let w = 0; w < 30; w++) {
    await new Promise(r => setTimeout(r, 1000));
    const mp4s = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
    if (mp4s.length > 0) {
      downloadedFile = path.join(DOWNLOADS_DIR, mp4s[0]);
      break;
    }
  }

  if (!downloadedFile || !fs.existsSync(downloadedFile)) {
    throw new Error('Downloaded MP4 not found in Downloads folder');
  }

  console.log('Downloaded file found:', downloadedFile);
  const baseName = path.basename(downloadedFile);
  const match = baseName.match(/_([a-f0-9]{8})\.mp4$/i);
  const batchId = match ? match[1] : ('flow_' + Date.now().toString(16));
  console.log('Extracted batch ID:', batchId);

  const rawDest = path.join(TARGET_DIR, 'raw_flow.mp4');
  fs.copyFileSync(downloadedFile, rawDest);
  console.log('Raw video saved to:', rawDest);

  ws.close();
  console.log('FLOW GENERATION FINISHED SUCCESSFULLY!');
  console.log(JSON.stringify({ success: true, batchId, rawDest }));
}

main().catch(err => {
  console.error('Generation error:', err);
  process.exit(1);
});
