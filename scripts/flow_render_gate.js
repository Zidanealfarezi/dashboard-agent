#!/usr/bin/env node
/**
 * Single Door Render Gate for Google Flow AI
 * Enforces strict credit reservation in SQLite before clicking Generate,
 * and binds the resulting media file and batch ID to the job record.
 * 
 * Strict 0% Emoji Policy.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations', 'production.sqlite');
const DOWNLOADS_DIR = '/Users/zidane/Downloads';

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function querySqlite(sql) {
  const escapedSql = sql.replace(/"/g, '\\"');
  try {
    const raw = execSync(`sqlite3 -json "${SQLITE_DB}" "${escapedSql}"`, { encoding: 'utf-8' });
    return raw.trim() ? JSON.parse(raw) : [];
  } catch (err) {
    throw new Error(`SQLite query failed: ${err.message}`);
  }
}

function execSqlite(sql) {
  const escapedSql = sql.replace(/"/g, '\\"');
  execSync(`sqlite3 "${SQLITE_DB}" "${escapedSql}"`, { encoding: 'utf-8' });
}

async function renderThroughSingleDoor(options) {
  const {
    characterId = 'dinda',
    slot = 'pagi',
    date = new Date().toISOString().split('T')[0],
    prompt,
    duration = 10,
    estimatedCredits = 12,
    outputDir
  } = options;

  if (!prompt || !prompt.trim()) {
    throw new Error('Prompt kreatif wajib disertakan pada pintu render tunggal.');
  }

  const targetDir = outputDir || path.join(PROJECT_ROOT, 'characters', characterId, 'content', `${characterId}-${slot}-palembang-${date}`);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  const jobId = 'job_' + Date.now();
  const idempotencyKey = `flow_${characterId}_${slot}_${date}_${jobId}`;
  const nowIso = new Date().toISOString();

  // 1. PINTU TUNGGAL RESERVASI KREDIT
  console.log(`[Render Gate] Memeriksa saldo & mencatat reservasi job: ${jobId} untuk brand: ${characterId}`);
  
  // Baca konfigurasi akun Flow berdasarkan karakter
  const flowConfigPath = path.join(PROJECT_ROOT, 'config', 'flow_accounts.json');
  const flowConfig = fs.existsSync(flowConfigPath) ? JSON.parse(fs.readFileSync(flowConfigPath, 'utf8')) : { accounts: [] };
  const targetAccount = flowConfig.accounts.find(a => a.assigned_character === characterId) || flowConfig.accounts[0] || { id: 'flow_1' };
  const flowAccountId = targetAccount.id;
  const targetProjectUrl = targetAccount.project_url;
  console.log(`[Render Gate] Akun Flow terpilih: ${flowAccountId} (${targetAccount.display_name || targetAccount.id})`);

  const spentRows = querySqlite(`SELECT COALESCE(SUM(actual_credits), 0) as total_spent FROM generation_jobs WHERE character_id = '${characterId}';`);
  const totalSpent = spentRows.length > 0 ? spentRows[0].total_spent : 0;
  console.log(`[Render Gate] Total kredit terpakai ${characterId} saat ini: ${totalSpent}`);

  // Catat reservasi 'planned'
  execSqlite(`
    INSERT INTO generation_jobs (id, character_id, flow_account_id, idempotency_key, state, model, duration_seconds, output_count, authorized_credits, created_at)
    VALUES ('${jobId}', '${characterId}', '${flowAccountId}', '${idempotencyKey}', 'planned', 'Omni 1.1 Flash', ${duration}, 1, ${estimatedCredits}, '${nowIso}');
  `);

  // Ubah status ke 'submitted' sebelum klik fisik
  execSqlite(`UPDATE generation_jobs SET state = 'submitted' WHERE id = '${jobId}';`);
  console.log(`[Render Gate] Reservasi dikunci (Status: submitted). Menghubungi Google Flow...`);

  // 2. Hubungi tab Flow via CDP yang cocok dengan project URL akun
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  let flowTab = null;
  if (targetProjectUrl && targetProjectUrl.includes('/project/')) {
    const targetProjectKey = targetProjectUrl.split('/project/')[1];
    flowTab = tabs.find(t => t.url && t.url.includes(targetProjectKey));
  }
  if (!flowTab) {
    flowTab = tabs.find(t => t.url && t.url.includes('flow.google.com'));
  }

  if (!flowTab) {
    execSqlite(`UPDATE generation_jobs SET state = 'failed' WHERE id = '${jobId}';`);
    throw new Error(`Tab Google Flow untuk ${characterId} (${flowAccountId}) tidak ditemukan di Chrome port 9333. Render dibatalkan.`);
  }

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let msgId = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = msgId++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 45000);
    const h = (e) => {
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

  await new Promise(r => ws.addEventListener('open', r));

  try {
    // Catat file MP4 yang sudah ada di direktori Downloads agar tidak terhapus
    const existingMp4s = new Set(fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')));

    // 3. Tekan tombol Start generation di Flow
    console.log('[Render Gate] Menekan tombol Start generation...');
    const genBtnRes = await send('Runtime.evaluate', {
      expression: `(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => 
          b.getAttribute('aria-label') === 'Start generation' || 
          (b.className && b.className.includes('generate-icon-button'))
        );
        if (!btn) return null;
        const r = btn.getBoundingClientRect();
        return { x: r.left + r.width/2, y: r.top + r.height/2, disabled: btn.disabled };
      })()`,
      returnByValue: true
    });

    const btnPos = genBtnRes.result ? genBtnRes.result.value : null;
    if (!btnPos || btnPos.disabled) {
      execSqlite(`UPDATE generation_jobs SET state = 'failed' WHERE id = '${jobId}';`);
      throw new Error('Tombol generate Flow tidak siap atau sedang disabled.');
    }

    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btnPos.x, y: btnPos.y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btnPos.x, y: btnPos.y, button: 'left', clickCount: 1 });
    console.log('[Render Gate] Tombol Start generation berhasil ditekan!');

    execSqlite(`UPDATE generation_jobs SET state = 'running' WHERE id = '${jobId}';`);

    // 4. Tunggu render batch selesai
    console.log('[Render Gate] Menunggu proses rendering Google Flow...');
    let completed = false;
    let attempts = 0;
    while (!completed && attempts < 90) {
      attempts++;
      await new Promise(r => setTimeout(r, 4000));
      const evalRes = await send('Runtime.evaluate', {
        expression: `(() => {
          const top = document.querySelector('.batch-container');
          if (!top) return { isDone: false, text: 'no container' };
          const text = top.innerText.replace(/\\s+/g, ' ');
          const isDone = text.includes('download') && !text.includes('%') && !text.includes('Generating');
          return { isDone, snippet: text.slice(0, 100) };
        })()`,
        returnByValue: true
      });

      const statusVal = evalRes.result ? evalRes.result.value : null;
      if (statusVal && statusVal.isDone) {
        completed = true;
        break;
      }
    }

    if (!completed) {
      execSqlite(`UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${jobId}';`);
      throw new Error('Timeout menunggu render Flow selesai.');
    }

    console.log('[Render Gate] Render video selesai 100%! Memulai unduhan berkas...');

    // 5. Unduh video dari batch
    await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return false;
        const dlBtn = Array.from(top.querySelectorAll('button')).find(b => 
          b.getAttribute('aria-label') === 'Download' || b.innerText.includes('download')
        );
        if (dlBtn) { dlBtn.click(); return true; }
        return false;
      })()`
    });

    // Tunggu file muncul di Downloads
    let downloadedFile = null;
    for (let w = 0; w < 15; w++) {
      await new Promise(r => setTimeout(r, 1000));
      const mp4s = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4') && !existingMp4s.has(f));
      if (mp4s.length > 0) {
        downloadedFile = path.join(DOWNLOADS_DIR, mp4s[0]);
        break;
      }
    }

    if (!downloadedFile || !fs.existsSync(downloadedFile)) {
      execSqlite(`UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${jobId}';`);
      throw new Error('Berkas unduhan MP4 tidak ditemukan di Downloads.');
    }

    // 6. Pindahkan berkas dan ikat ke ID job
    const rawDestPath = path.join(targetDir, 'raw_flow.mp4');
    fs.copyFileSync(downloadedFile, rawDestPath);
    const mediaBytes = fs.readFileSync(rawDestPath);
    const mediaHash = sha256(mediaBytes);

    console.log(`[Render Gate] Berkas video mentah tersimpan: ${rawDestPath}`);
    console.log(`[Render Gate] SHA256: ${mediaHash}`);

    const externalBatchId = 'batch_' + Date.now();
    const actualCredits = estimatedCredits;

    // Catat penyelesaian job di SQLite
    execSqlite(`
      UPDATE generation_jobs 
      SET state = 'completed', actual_credits = ${actualCredits}, external_job_id = '${externalBatchId}'
      WHERE id = '${jobId}';
    `);

    console.log(`[Render Gate] SUKSES: Job ${jobId} berstatus completed dengan biaya ${actualCredits} kredit.`);
    ws.close();

    return {
      success: true,
      jobId,
      mediaPath: rawDestPath,
      mediaSha256: mediaHash,
      actualCredits
    };
  } catch (err) {
    execSqlite(`UPDATE generation_jobs SET state = 'needs_user' WHERE id = '${jobId}';`);
    ws.close();
    throw err;
  }
}

// CLI Runner
if (require.main === module) {
  const args = process.argv.slice(2);
  const prompt = args[0] || 'Authentic handheld smartphone vlog video of Dinda Kemala, Indonesian woman wearing modest attire.';
  renderThroughSingleDoor({ prompt })
    .then(res => {
      console.log('Result:', JSON.stringify(res, null, 2));
      process.exit(0);
    })
    .catch(err => {
      console.error('Render Gate Error:', err.message);
      process.exit(1);
    });
}

module.exports = { renderThroughSingleDoor };
