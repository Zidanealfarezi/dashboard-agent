const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/isk/content/ISK_PK_006');
const JOB_ID = '0a983ff281964bddb2d206df2682f54e';
const FFMPEG = '/Users/zidane/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg';
const OUTRO_PATH = path.join(PROJECT_ROOT, 'characters/isk/assets/brand/outro_keris_isk.mp4');

const PROMPT = `Photorealistic live-action video, vertical 9:16, 10 seconds, one continuous shot. Medium shot in a woodworking workshop in bright morning natural daylight. An Indonesian male carpenter in a navy work shirt stands at his wooden workbench. On the workbench sits an open brown cardboard box of Paku Cap Keris matching the attached reference image, with clean bulk steel nails loose inside without plastic wrapping. In the first 3 seconds, he holds up a bent low-quality nail with a disappointed look, shakes his head and says, "Paku murahan baru dihantam sekali langsung bengkok? Waktunya beralih ke Paku Cap Keris dari PT Intan Suar Kartika! Baja murni standar mutu ekspor, dijamin lurus dan kokoh!" From 4 to 8 seconds, he tosses the bent nail away, picks up a sturdy straight steel nail from the Paku Cap Keris box, shows it confidently to the camera, points at its solid shank, and smiles with pride. From 8 to 10 seconds, he holds the clean nail ready against a thick wooden plank with his hammer raised. Natural Indonesian dialogue with clear lip sync and authentic workshop sound. Completely clean visual frame with zero on-screen text, zero subtitles, and zero logos.`;

async function main() {
  if (!fs.existsSync(TARGET_DIR)) {
    fs.mkdirSync(TARGET_DIR, { recursive: true });
  }

  // Bersihkan MP4 lama di Downloads
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const iskTab = tabs.find(t => t.url && t.url.includes('33b10f02-20fa-4df2-87c3-ca4696d342c6') && t.type === 'page');
  if (!iskTab) throw new Error('ISK Flow tab not found on port 9333');

  const ws = new WebSocket(iskTab.webSocketDebuggerUrl);
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

  console.log('Connected to ISK Flow tab.');

  await send('Page.enable');
  await send('Browser.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: DOWNLOADS_DIR
  });

  // 1. Focus dan masukkan prompt lengkap via Input.insertText
  console.log('Focusing ProseMirror and clearing old text...');
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

  console.log('Typing full prompt text...');
  await send('Input.insertText', { text: PROMPT });
  await new Promise(r => setTimeout(r, 1000));

  // 2. Verifikasi tombol Mulai pembuatan
  const genBtn = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.generate-icon-button');
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      return {
        x: r.x + r.width / 2,
        y: r.y + r.height / 2,
        disabled: btn.disabled || btn.getAttribute('aria-disabled') === 'true'
      };
    })()`,
    returnByValue: true
  });

  console.log('Generate button state:', genBtn.result.value);
  if (!genBtn.result.value || genBtn.result.value.disabled) {
    throw new Error('Generate button is disabled or not found');
  }

  // 3. Update SQLite state to 'running'
  execSync(`sqlite3 "${path.join(PROJECT_ROOT, 'operations/production.sqlite')}" "UPDATE generation_jobs SET state = 'running' WHERE id = '${JOB_ID}';"`);
  console.log('SQLite job state set to running.');

  // 4. Klik Mulai pembuatan
  console.log('Dispatching click to Generate button...');
  const { x, y } = genBtn.result.value;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  console.log('Generate clicked successfully!');

  // 5. Tunggu proses render Flow selesai
  console.log('Waiting for generation batch to appear and finish...');
  await new Promise(r => setTimeout(r, 12000));

  let completed = false;
  let attempts = 0;
  while (!completed && attempts < 90) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));
    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { isDone: false, snippet: 'no container' };
        const text = top.innerText.replace(/\\s+/g, ' ');
        const isDone = (text.includes('download') || text.includes('Unduh') || text.includes('unduh')) && !text.includes('%') && !text.includes('Generating') && !text.includes('Membuat');
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

  // 6. Unduh video dari top batch
  await new Promise(r => setTimeout(r, 3000));
  console.log('Clicking Download on top batch...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const btn = top ? top.querySelector('button[aria-label*="Download"], button[aria-label*="Unduh"], button[aria-label*="download"]') : null;
      if (btn) {
        btn.click();
        return 'clicked top batch download';
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

  const rawClip = path.join(TARGET_DIR, 'raw_flow_clip.mp4');
  fs.copyFileSync(downloadedFile, rawClip);
  console.log('Raw Flow video clip saved to:', rawClip);

  ws.close();

  // 7. Post-Production: Generate Kinetic Yellow Subtitles (MarginV = 300)
  console.log('Generating Kinetic Yellow Subtitles via Faster-Whisper alignment...');
  const subtitledClip = path.join(TARGET_DIR, 'clip_subtitled.mp4');
  const assPath = path.join(TARGET_DIR, 'subtitles_kinetic_yellow.ass');
  const subtitlesScript = path.join(PROJECT_ROOT, 'app/subtitles.py');

  const subCmd = `python3 "${subtitlesScript}" --input "${rawClip}" --output "${subtitledClip}" --ass "${assPath}" --margin-v 300`;
  execSync(subCmd, { stdio: 'inherit' });

  // HARD GUARD: Enforce that subtitle file exists and subtitled clip is valid
  if (!fs.existsSync(assPath) || fs.statSync(assPath).size === 0) {
    throw new Error('PIPELINE VIOLATION: subtitles_kinetic_yellow.ass was not created or is empty. Outro assembly blocked!');
  }
  if (!fs.existsSync(subtitledClip) || fs.statSync(subtitledClip).size === 0) {
    throw new Error('PIPELINE VIOLATION: clip_subtitled.mp4 was not created or is empty. Outro assembly blocked!');
  }
  console.log('Kinetic subtitle successfully burned into clip with MarginV=300.');

  // 8. Gabungkan clip bersubtitle dengan master outro bumper resmi ISK (4.0667 detik)
  const finalVideo = path.join(TARGET_DIR, 'ISK_PK_006_final.mp4');
  console.log('Assembling final video with official ISK bumper outro...');

  // Concat using FFmpeg filter_complex
  const ffmpegCmd = `${FFMPEG} -y -i "${subtitledClip}" -i "${OUTRO_PATH}" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k "${finalVideo}"`;
  execSync(ffmpegCmd);
  console.log('Final video assembled successfully at:', finalVideo);

  // 9. Update generation_jobs actual_credits & external_job_id
  execSync(`sqlite3 "${path.join(PROJECT_ROOT, 'operations/production.sqlite')}" "UPDATE generation_jobs SET state = 'completed', actual_credits = 30, external_job_id = '${batchId}' WHERE id = '${JOB_ID}';"`);
  console.log('generation_jobs updated to completed.');

  console.log('ALL STEPS FINISHED SUCCESSFULLY!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
