throw new Error('Jalur lama Flow dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const https = require('https');
const path = require('path');
const { execSync } = require('child_process');

const BASE_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER';
const CONTENT_DIR = path.join(BASE_DIR, 'characters/dinda/content');

async function run() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json')).json();
  const flowTab = tabs.find(t => t.url && t.url.includes('flow.google.com'));
  if (!flowTab) throw new Error('Flow tab not found');

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const msgId = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + method)), 30000);
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

  console.log('Connected to Flow CDP for Malam Minggu SOREE Cafe Video.');

  async function clickCoords(x, y) {
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  }

  async function setPrompt(text) {
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
    await send('Input.insertText', { text });
    await new Promise(r => setTimeout(r, 800));
  }

  async function triggerGen() {
    const coords = await send('Runtime.evaluate', {
      expression: `(() => {
        const btn = document.querySelector('.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Start generation');
        if (!btn) return null;
        const rect = btn.getBoundingClientRect();
        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, disabled: btn.disabled };
      })()`,
      returnByValue: true
    });
    if (!coords.result.value) throw new Error('Generate button not found');
    if (coords.result.value.disabled) throw new Error('Generate button is disabled');
    await clickCoords(coords.result.value.x, coords.result.value.y);
  }

  async function waitForVideo(keyword, outputPath) {
    console.log(`Monitoring video generation for [${keyword}]...`);
    let finished = false;
    let attempts = 0;
    let videoSrc = null;

    while (!finished && attempts < 70) {
      attempts++;
      await new Promise(r => setTimeout(r, 4000));

      const status = await send('Runtime.evaluate', {
        expression: `(() => {
          const batch = document.querySelector('.batch-container');
          if (!batch) return { exists: false };
          const text = batch.innerText.replace(/\\s+/g, ' ');
          const isTarget = text.toLowerCase().includes('${keyword.toLowerCase()}');
          const isGen = text.includes('%') || text.includes('Generating');
          const vid = batch.querySelector('video');
          return {
            exists: true,
            isTarget,
            isGen,
            hasVid: !!vid,
            src: vid ? vid.src : null,
            textSnippet: text.slice(0, 100)
          };
        })()`,
        returnByValue: true
      });

      const val = status.result.value;
      console.log(`[Attempt ${attempts}] isTarget: ${val.isTarget} | isGen: ${val.isGen} | hasVid: ${val.hasVid}`);

      if (val.isTarget && !val.isGen && val.hasVid && val.src) {
        console.log('Video generation completed!');
        finished = true;
        videoSrc = val.src;
        break;
      }
    }

    if (!finished || !videoSrc) {
      throw new Error(`Timed out waiting for video ${keyword}`);
    }

    console.log('Downloading video from:', videoSrc);
    await new Promise((resolve, reject) => {
      https.get(videoSrc, (res) => {
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => {
          const buf = Buffer.concat(chunks);
          fs.writeFileSync(outputPath, buf);
          console.log(`Saved video to ${outputPath} (${buf.length} bytes)`);
          resolve();
        });
      }).on('error', reject);
    });
  }

  // ==========================================
  // SHOT 1: Malam Minggu SOREE Cafe (8s)
  // ==========================================
  console.log('\n--- GENERATING SHOT 1: Malam Minggu SOREE Cafe (8s) ---');
  const promptShot1 = `Authentic handheld smartphone vlog video of Dinda Kemala from character reference sheets sitting at a cozy wooden table inside SOREE Cafe Jalan Veteran in Palembang on a vibrant Saturday night. Cozy warm ambient indoor lighting, minimal modern cafe interior with indoor potted plants and soft warm bokeh in the background. Medium shot, vertical 9:16 aspect ratio. Dinda wears her striped taupe-khaki knit cardigan, neat soft beige pashmina hijab, and small gold ring pendant necklace, strictly matching the attached reference sheets. Natural soft daylight white balance 5500K, realistic matte human skin with visible fine pores and authentic facial texture, strictly no yellow or orange tint, no plastic glass skin. Dinda holds an artisan coffee cup naturally on the wooden table, smiling warmly and speaking directly to the camera in natural conversational Indonesian: "Malam minggu gini paling asik emang nongkrong santai di SOREE Cafe Jalan Veteran. Suasananya nyaman banget buat ngobrol atau sekadar nikmatin kopi hangat." Natural lip-sync ending at second 6.5, clear authentic Indonesian female voice, documentary smartphone video aesthetic, no subtitles.`;

  await setPrompt(promptShot1);
  await new Promise(r => setTimeout(r, 600));
  await triggerGen();
  console.log('Shot 1 triggered!');

  const shot1Path = path.join(CONTENT_DIR, 'dinda_soree_shot1_8s.mp4');
  await waitForVideo('malam minggu gini', shot1Path);

  // Brief pause before Shot 2
  await new Promise(r => setTimeout(r, 4000));

  // ==========================================
  // SHOT 2: SOREE Cafe Interaction & CTA (8s)
  // ==========================================
  console.log('\n--- GENERATING SHOT 2: SOREE Cafe Interaction & CTA (8s) ---');
  const promptShot2 = `Authentic handheld smartphone vlog video of Dinda Kemala from character reference sheets inside SOREE Cafe Jalan Veteran in Palembang on Saturday night. Medium close-up framing, vertical 9:16 aspect ratio. Dinda wears her striped taupe-khaki knit cardigan, neat soft beige pashmina hijab, and small gold ring pendant necklace matching the reference sheets. Natural soft white balance 5500K, realistic matte human skin with fine pores, strictly zero plastic AI slop, no heavy yellow filter. Dinda sets down her coffee cup on the wooden table, smiles warmly and speaks directly to the camera in natural conversational Indonesian: "Tempatnya selalu rame anak muda Palembang tapi tetap dapet cozy vibes-nya. Kalau kalian malam minggu biasanya nongkrong di mana nih? Cerita di komen ya!" Natural lip-sync ending at second 6.5, clear authentic Indonesian female voice, documentary smartphone camera aesthetic, no subtitles.`;

  await setPrompt(promptShot2);
  await new Promise(r => setTimeout(r, 600));
  await triggerGen();
  console.log('Shot 2 triggered!');

  const shot2Path = path.join(CONTENT_DIR, 'dinda_soree_shot2_8s.mp4');
  await waitForVideo('anak muda palembang', shot2Path);

  console.log('\nBoth shots generated successfully!');
  ws.close();
}

run().catch((err) => {
  console.error('Video Generation Error:', err);
  process.exit(1);
});
