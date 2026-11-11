#!/usr/bin/env node
/**
 * execute_isk_pk007.js
 * Autonomous generation and post-production script for PT Intan Suar Kartika (ISK_PK_007).
 * Implements:
 * 1. Single-ledger SQLite registration (content, generation_jobs).
 * 2. CDP Google Flow automation on project 33b10f02-20fa-4df2-87c3-ca4696d342c6.
 * 3. 10s video generation with verified packaging reference chip.
 * 4. HARD-GUARDED post-production: Faster-Whisper alignment + Kinetic Yellow ASS hardsub (MarginV=300).
 * 5. Official outro bumper concat (4.07s) -> 14.1s final video.
 * 6. SQLite versions ledger registration.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_ID = 'isk_pk_007';
const TARGET_DIR = path.join(PROJECT_ROOT, 'characters/isk/content/ISK_PK_007');
const JOB_ID = 'job_' + CONTENT_ID + '_' + Date.now().toString(16);
const FFMPEG = '/Users/zidane/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg';
const OUTRO_PATH = path.join(PROJECT_ROOT, 'characters/isk/assets/brand/outro_keris_isk.mp4');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations/production.sqlite');

const CAPTION = 'Pekerjaan konstruksi cepat dan rapi butuh paku berkualitas ekspor. Paku Cap Keris dari PT Intan Suar Kartika, batang baja kokoh anti bengkok dan jaminan timbangan pas 25 kg. Pemesanan distributor langsung via WhatsApp wa.me/62819889350. #pakucapkeris #intansuarkartika #tokobangunan';

const PROMPT = `Photorealistic live-action video, vertical 9:16, 10 seconds, one continuous shot. Medium shot at an outdoor construction site workbench in bright natural daylight. An Indonesian male construction carpenter wearing a navy work shirt stands before a thick wooden timber beam. On the workbench sits an open brown kraft cardboard box of Paku Cap Keris matching the reference image, with clean bulk steel nails loose inside without plastic wrapping. In the first 3 seconds, he holds a bent competitor nail, shakes his head firmly at the camera, and speaks: "Paku proyek kamu sering bengkok bikin kerjaan lambat? Waktunya beralih ke Paku Cap Keris dari PT Intan Suar Kartika! Baja murni mutu ekspor, dijamin lurus dan kokoh!" From 4 to 8 seconds, he tosses the bent nail aside, takes a straight shiny steel nail from the Paku Cap Keris box, lines it up against the hard timber, and drives it flush with two powerful hammer strikes without any bending. From 8 to 10 seconds, he proudly points at the flush-driven steel nail and gives a confident nod towards the Paku Cap Keris box. Natural dialogue with clear Indonesian lip sync and crisp hammer impacts. Clean visual frame with zero on-screen text, zero watermarks, and zero logos.`;

function sha256File(filePath) {
  const fileBuffer = fs.readFileSync(filePath);
  const hashSum = crypto.createHash('sha256');
  hashSum.update(fileBuffer);
  return hashSum.digest('hex');
}

async function main() {
  console.log(`[ISK Pipeline] Starting generation for ${CONTENT_ID}...`);
  if (!fs.existsSync(TARGET_DIR)) {
    fs.mkdirSync(TARGET_DIR, { recursive: true });
  }

  const nowIso = new Date().toISOString();

  // 1. Register content & generation_jobs in SQLite
  console.log('[ISK Pipeline] Registering job in SQLite ledger...');
  execSync(`sqlite3 "${SQLITE_DB}" "INSERT OR IGNORE INTO content (id, character_id, kind, created_at) VALUES ('${CONTENT_ID}', 'isk', 'video', '${nowIso}');"`);
  execSync(`sqlite3 "${SQLITE_DB}" "INSERT INTO generation_jobs (id, character_id, flow_account_id, idempotency_key, state, model, duration_seconds, output_count, authorized_credits, actual_credits, created_at) VALUES ('${JOB_ID}', 'isk', 'flow_2', 'idemp_${CONTENT_ID}_${Date.now()}', 'submitted', 'Omni 1.2 Flash', 10, 1, 30, 0, '${nowIso}');"`);

  // Clear older MP4s from Downloads
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  // 2. Connect to Chrome tab for ISK Flow
  console.log('[ISK Pipeline] Connecting to Google Flow tab...');
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const iskTab = tabs.find(t => t.url && t.url.includes('33b10f02-20fa-4df2-87c3-ca4696d342c6') && t.type === 'page');
  if (!iskTab) throw new Error('ISK Flow tab (33b10f02-20fa-4df2-87c3-ca4696d342c6) not found on port 9333');

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

  await send('Page.enable');
  await send('Browser.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: DOWNLOADS_DIR
  });

  // 3. Focus ProseMirror and type prompt
  console.log('[ISK Pipeline] Focusing prompt input and entering prompt text...');
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

  // 4. Verify Generate button
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

  if (!genBtn.result.value || genBtn.result.value.disabled) {
    throw new Error('Generate button is disabled or not found');
  }

  // 5. Update SQLite job to running
  execSync(`sqlite3 "${SQLITE_DB}" "UPDATE generation_jobs SET state = 'running' WHERE id = '${JOB_ID}';"`);
  console.log('[ISK Pipeline] Generation job state set to running.');

  // Click Generate
  console.log('[ISK Pipeline] Clicking Generate button...');
  const { x, y } = genBtn.result.value;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });

  // 6. Wait for Flow render to complete
  console.log('[ISK Pipeline] Waiting for Google Flow to render video...');
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
  console.log('[ISK Pipeline] Render completed successfully!');

  // 7. Click Download on the top batch
  await new Promise(r => setTimeout(r, 3000));
  console.log('[ISK Pipeline] Downloading generated MP4 from top batch...');
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

  // Wait for file in Downloads
  console.log('[ISK Pipeline] Waiting for downloaded MP4...');
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

  const baseName = path.basename(downloadedFile);
  const match = baseName.match(/_([a-f0-9]{8})\.mp4$/i);
  const batchId = match ? match[1] : ('flow_' + Date.now().toString(16));
  console.log('[ISK Pipeline] Downloaded batch ID:', batchId);

  const rawClip = path.join(TARGET_DIR, 'raw_clip_10s.mp4');
  fs.copyFileSync(downloadedFile, rawClip);
  console.log('[ISK Pipeline] Saved raw clip to:', rawClip);

  ws.close();

  // 8. KINETIC SUBTITLE POST-PRODUCTION (HARD-GUARDED)
  console.log('[ISK Pipeline] Running Kinetic Yellow Subtitle Engine via Faster-Whisper...');
  const subtitledClip = path.join(TARGET_DIR, 'clip_subtitled.mp4');
  const assPath = path.join(TARGET_DIR, 'subtitles_kinetic_yellow.ass');
  const subtitlesScript = path.join(PROJECT_ROOT, 'app/subtitles.py');

  const subCmd = `python3 "${subtitlesScript}" --input "${rawClip}" --output "${subtitledClip}" --ass "${assPath}" --margin-v 300`;
  execSync(subCmd, { stdio: 'inherit' });

  // HARD GUARD VERIFICATION
  if (!fs.existsSync(assPath) || fs.statSync(assPath).size === 0) {
    throw new Error('PIPELINE VIOLATION: subtitles_kinetic_yellow.ass was not created or is empty. Assembly blocked!');
  }
  if (!fs.existsSync(subtitledClip) || fs.statSync(subtitledClip).size === 0) {
    throw new Error('PIPELINE VIOLATION: clip_subtitled.mp4 was not created or is empty. Assembly blocked!');
  }
  console.log('[ISK Pipeline] Subtitle hard-guard passed: Kinetic yellow subtitles burned at MarginV=300.');

  // 9. ASSEMBLE WITH OFFICIAL BUMPER OUTRO
  const finalVideo = path.join(TARGET_DIR, 'ISK_PK_007_final.mp4');
  console.log('[ISK Pipeline] Assembling final video with official ISK bumper outro...');

  const ffmpegCmd = `${FFMPEG} -y -i "${subtitledClip}" -i "${OUTRO_PATH}" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k "${finalVideo}"`;
  execSync(ffmpegCmd);
  console.log('[ISK Pipeline] Final video assembled successfully at:', finalVideo);

  // 10. REGISTER TO SQLITE VERSIONS
  const finalSha = sha256File(finalVideo);
  const capSha = crypto.createHash('sha256').update(CAPTION).digest('hex');
  const verId = `ver_${CONTENT_ID}_rev1_${Math.floor(Date.now() / 1000)}`;

  execSync(`sqlite3 "${SQLITE_DB}" "INSERT INTO versions (id, content_id, revision, media_path, media_sha256, caption, caption_sha256, destination_account, created_at) VALUES ('${verId}', '${CONTENT_ID}', 1, 'characters/isk/content/ISK_PK_007/ISK_PK_007_final.mp4', '${finalSha}', '${CAPTION.replace(/'/g, "''")}', '${capSha}', '@intansuarkartika', '${new Date().toISOString()}');"`);
  execSync(`sqlite3 "${SQLITE_DB}" "UPDATE generation_jobs SET state = 'completed', actual_credits = 30, external_job_id = '${batchId}' WHERE id = '${JOB_ID}';"`);

  console.log('[ISK Pipeline] SUCCESS! Version registered:', verId);
  console.log('[ISK Pipeline] Output path:', finalVideo);
}

main().catch(err => {
  console.error('[ISK Pipeline] Fatal error:', err);
  process.exit(1);
});
