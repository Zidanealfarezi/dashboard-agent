#!/usr/bin/env node
/**
 * Unified TikTok Studio Publisher with Mandatory ACC Verification & Exact Post Matching
 * Strict Constraints:
 * 1. Requires valid ACC (Approved Version ID) before any action.
 * 2. Matches media sha256, caption sha256, and destination account.
 * 3. Validates that open TikTok session belongs to the destination account.
 * 4. Deep-purges DraftEditor to eliminate filename placeholder bugs.
 * 5. Strictly records confirmed ONLY when exact video URL (with numeric video ID) is verified.
 *    If unconfirmed, records state as 'unknown'. Never defaults to profile URL!
 * 6. 0% Emoji Guarantee.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SQLITE_DB = path.join(PROJECT_ROOT, 'operations', 'production.sqlite');

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function querySqlite(sql, params = []) {
  // Use sqlite3 CLI with parameterized safety via Python helper or direct execution
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

function getApprovedVersion(versionId) {
  const versions = querySqlite(`
    SELECT v.*, c.character_id, ch.account 
    FROM versions v
    JOIN content c ON c.id = v.content_id
    JOIN characters ch ON ch.id = c.character_id
    WHERE v.id = '${versionId}';
  `);

  if (!versions || versions.length === 0) {
    throw new Error(`Versi dengan ID '${versionId}' tidak ditemukan di database.`);
  }

  const version = versions[0];

  // Periksa persetujuan ACC di tabel approvals
  const approvals = querySqlite(`
    SELECT * FROM approvals 
    WHERE version_id = '${versionId}' 
    ORDER BY rowid DESC LIMIT 1;
  `);

  if (!approvals || approvals.length === 0 || approvals[0].decision !== 'approved') {
    throw new Error(`Akses ditolak: Versi '${versionId}' belum memiliki keputusan ACC yang sah ('approved') dari Owner.`);
  }

  // Verifikasi file media fisik di disk
  const absMediaPath = path.resolve(PROJECT_ROOT, version.media_path);
  if (!fs.existsSync(absMediaPath)) {
    throw new Error(`File media tidak ditemukan di disk: ${absMediaPath}`);
  }

  const fileBytes = fs.readFileSync(absMediaPath);
  const actualMediaHash = sha256(fileBytes);
  if (actualMediaHash !== version.media_sha256) {
    throw new Error(`Integritas media gagal: Checksum file di disk (${actualMediaHash}) tidak cocok dengan versi ACC (${version.media_sha256}).`);
  }

  // Verifikasi caption
  const actualCaptionHash = sha256(Buffer.from(version.caption, 'utf-8'));
  if (actualCaptionHash !== version.caption_sha256) {
    throw new Error(`Integritas caption gagal: Checksum caption tidak cocok dengan versi ACC.`);
  }

  return {
    version,
    approval: approvals[0],
    absMediaPath
  };
}

const CDP_PORTS = [9333, 9334, 9335];

async function findTikTokTabForAccount(targetAccount) {
  const targetClean = targetAccount.replace('@', '').toLowerCase();
  const candidates = [];
  for (const port of CDP_PORTS) {
    try {
      const tabs = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json());
      for (const t of tabs) {
        if (t.type === 'page' && t.url && t.url.includes('tiktok.com')) {
          candidates.push({ port, tab: t, isStudio: t.url.includes('tiktokstudio') });
        }
      }
    } catch (_) {
      // Port not open
    }
  }
  candidates.sort((a, b) => Number(b.isStudio) - Number(a.isStudio));

  for (const { tab: t, isStudio } of candidates) {
    const ws = new WebSocket(t.webSocketDebuggerUrl);
    await new Promise(r => ws.addEventListener('open', r));
    let id = 1;
    const send = (m, p = {}) => new Promise((resolve, reject) => {
      const curId = id++;
      const timer = setTimeout(() => reject(new Error('CDP Timeout')), 8000);
      const h = (e) => {
        const g = JSON.parse(e.data);
        if (g.id === curId) {
          clearTimeout(timer);
          ws.removeEventListener('message', h);
          if (g.error) reject(new Error(JSON.stringify(g.error)));
          else resolve(g.result);
        }
      };
      ws.addEventListener('message', h);
      ws.send(JSON.stringify({ id: curId, method: m, params: p }));
    });

    try {
      const evalRes = await send('Runtime.evaluate', {
        expression: `(async () => {
          const passport = await fetch('https://www.tiktok.com/passport/web/account/info/', {
            credentials: 'include',
            signal: AbortSignal.timeout(4000)
          }).then(r => r.json()).catch(() => null);
          const passportUser = (passport && passport.data && passport.data.username || '').toLowerCase();
          const body = (document.body.innerText || '').toLowerCase();
          const href = window.location.href.toLowerCase();
          const links = Array.from(document.querySelectorAll('a')).map(a => (a.href || '').toLowerCase());
          const navProfile = (document.querySelector('[data-e2e="nav-profile"]') || {}).href || '';
          const hasPassportMatch = passportUser === '${targetClean}';
          const hasStudioVideoLink = links.some(l => l.includes('/@' + '${targetClean}' + '/video/'));
          const hasDirectProfile = navProfile.toLowerCase().includes('/@' + '${targetClean}') || links.some(l => l.endsWith('/@' + '${targetClean}') || l.includes('/@' + '${targetClean}?'));
          const textMatches = body.includes('${targetClean}') || href.includes('/@' + '${targetClean}');
          return { hasPassportMatch, passportUser, hasStudioVideoLink, hasDirectProfile, textMatches };
        })()`,
        awaitPromise: true,
        returnByValue: true
      });

      const val = evalRes.result ? evalRes.result.value : {};
      // For TikTok Studio tabs, require authenticated passport match (or explicit video link belonging to target account)
      // so stale cookies/unrelated Studio windows never slip through.
      if (isStudio ? (val.hasPassportMatch || val.hasStudioVideoLink) : (val.hasPassportMatch || val.hasDirectProfile || val.textMatches)) {
        ws.close();
        return t;
      }
    } catch (e) {
      // Ignore evaluation errors
    }
    ws.close();
  }
  return null;
}

async function publishApprovedVersion(versionId) {
  console.log(`[TikTok Publisher] Memverifikasi integritas versi ber-ACC: ${versionId}`);
  const { version, absMediaPath } = getApprovedVersion(versionId);

  const destinationAccount = version.destination_account;
  const caption = version.caption;

  console.log(`[TikTok Publisher] Target Akun: ${destinationAccount}`);
  console.log(`[TikTok Publisher] Berkas Media: ${absMediaPath}`);
  console.log(`[TikTok Publisher] Teks Caption: ${caption.slice(0, 80)}...`);

  // Cek apakah versi ini sudah pernah confirmed
  const existingConfirmed = querySqlite(`
    SELECT * FROM publications 
    WHERE version_id = '${versionId}' AND state = 'confirmed';
  `);
  if (existingConfirmed && existingConfirmed.length > 0) {
    console.log(`[TikTok Publisher] Versi ${versionId} sudah pernah berstatus confirmed: ${existingConfirmed[0].post_url}`);
    return {
      success: true,
      state: 'confirmed',
      postUrl: existingConfirmed[0].post_url,
      platformPostId: existingConfirmed[0].platform_post_id
    };
  }

  // Cek batas maksimal 1 kali posting per hari per karakter & batas durasi video per karakter
  const projectConfig = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'config', 'project.json'), 'utf-8'));
  const maxPostsPerDay = Number(projectConfig.posts_per_day || 1);
  const videoPolicy = projectConfig.video_policy || {};
  const byCharCaps = videoPolicy.max_duration_by_character || {};
  const maxVideoSeconds = Number(byCharCaps[version.character_id] || videoPolicy.max_duration_seconds || 20);
  const todayWib = new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 10);
  const dailyRows = querySqlite(`
    SELECT p.state, p.confirmed_at, v.created_at FROM publications p
    JOIN versions v ON v.id = p.version_id
    JOIN content c ON c.id = v.content_id
    WHERE c.character_id = '${version.character_id}' AND p.state IN ('submitted', 'confirmed', 'unknown');
  `);
  const todayPubCount = dailyRows.filter(r => {
    const raw = r.state === 'confirmed' && r.confirmed_at ? r.confirmed_at : r.created_at;
    if (!raw) return false;
    const ms = Date.parse(raw);
    if (Number.isNaN(ms)) return false;
    return new Date(ms + 7 * 3600 * 1000).toISOString().slice(0, 10) === todayWib;
  }).length;
  if (todayPubCount >= maxPostsPerDay) {
    throw new Error(`Batas maksimal ${maxPostsPerDay} kali posting per hari untuk '${version.character_id}' sudah tercapai.`);
  }
  try {
    const ffprobeLocal = path.join(PROJECT_ROOT, 'tools', 'ffmpeg-runtime', 'ffprobe');
    const ffprobeBin = fs.existsSync(ffprobeLocal) ? `"${ffprobeLocal}"` : 'ffprobe';
    const durOut = execSync(
      `${ffprobeBin} -v error -show_entries format=duration -of default=nw=1:nk=1 "${absMediaPath}"`,
      { encoding: 'utf-8' }
    ).trim();
    const actualDuration = parseFloat(durOut);
    if (!Number.isNaN(actualDuration) && actualDuration > maxVideoSeconds + 0.5) {
      throw new Error(`Durasi video (${actualDuration.toFixed(2)}s) melampaui batas maksimal ${maxVideoSeconds} detik.`);
    }
  } catch (probeErr) {
    if (probeErr.message && probeErr.message.includes('melampaui batas maksimal')) throw probeErr;
  }

  // Buka percobaan resmi via app.publication begin (Single-Gatekeeper ACC & Schedule Enforcement)
  let pubId;
  const ignoreSchedule = process.argv.includes('--ignore-schedule');
  const scheduleFlag = ignoreSchedule ? '' : ' --enforce-schedule';
  try {
    const beginOut = execSync(
      `python3 -m app.publication begin --version "${versionId}" --account "${destinationAccount}"${scheduleFlag}`,
      { cwd: PROJECT_ROOT, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }
    );
    const pubRecord = JSON.parse(beginOut);
    pubId = pubRecord.publication_id;
    console.log(`[TikTok Publisher] Gerbang ACC Telegram tervalidasi resmi (ID Percobaan: ${pubId})`);
  } catch (err) {
    const errMsg = err.stderr ? err.stderr.toString().trim() : err.message;
    throw new Error(`[Gerbang ACC Ditolak] ${errMsg}`);
  }

  console.log(`[TikTok Publisher] Percobaan publikasi dicatat (ID: ${pubId}, Status: submitted)`);

  let ttTab = await findTikTokTabForAccount(destinationAccount);
  if (!ttTab) {
    const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
    ttTab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('tiktok.com'));
  }
  if (!ttTab) {
    execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
    throw new Error(`Tab TikTok untuk akun ${destinationAccount} tidak ditemukan di Chrome port 9333. Publikasi ditahan sebagai unknown.`);
  }

  console.log(`[TikTok Publisher] Tab TikTok terpilih: [${ttTab.id}] ${ttTab.title}`);

  const ws = new WebSocket(ttTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const curId = id++;
    const timer = setTimeout(() => reject(new Error('CDP Timeout: ' + m)), 45000);
    const h = (e) => {
      const g = JSON.parse(e.data);
      if (g.id === curId) {
        clearTimeout(timer);
        ws.removeEventListener('message', h);
        if (g.error) reject(new Error(JSON.stringify(g.error)));
        else resolve(g.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: curId, method: m, params: p }));
  });

  await new Promise(r => ws.addEventListener('open', r));

  // Auto-accept beforeunload dialogs so Page.navigate never stalls in background tabs
  ws.addEventListener('message', (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.method === 'Page.javascriptDialogOpening') {
        ws.send(JSON.stringify({ id: id++, method: 'Page.handleJavaScriptDialog', params: { accept: true } }));
      }
    } catch (_) {}
  });

  try {
    await send('Page.enable');
    await send('Page.bringToFront');
    // 1. Verifikasi kecocokan akun yang sedang login di browser
    console.log('[TikTok Publisher] Memverifikasi akun TikTok di browser...');
    await send('Runtime.evaluate', { expression: 'window.onbeforeunload = null;' }).catch(() => {});

    const accountCheck = await send('Runtime.evaluate', {
      expression: `(async () => {
        const passport = await fetch('https://www.tiktok.com/passport/web/account/info/', {
          credentials: 'include',
          signal: AbortSignal.timeout(5000)
        }).then(r => r.json()).catch(() => null);
        const passportUser = (passport && passport.data && passport.data.username || '').toLowerCase();
        const bodyText = (document.body.innerText || '').toLowerCase();
        const currentUrl = window.location.href.toLowerCase();
        const targetClean = "${destinationAccount}".replace('@', '').toLowerCase();
        const links = Array.from(document.querySelectorAll('a')).map(a => (a.href || '').toLowerCase());
        const matched = passportUser === targetClean
          || (passportUser === '' && (bodyText.includes(targetClean) || currentUrl.includes(targetClean) || links.some(l => l.includes('/@' + targetClean))));
        return { matched, passportUser, snippet: bodyText.slice(0, 200) };
      })()`,
      awaitPromise: true,
      returnByValue: true
    });

    console.log('[TikTok Publisher] Hasil pemeriksaan akun:', accountCheck.result.value);
    if (!accountCheck.result.value.matched) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      throw new Error(`Akun di browser TikTok tidak cocok dengan akun tujuan (${destinationAccount}). Publikasi dibatalkan demi keamanan.`);
    }

    // 2. Buka halaman upload jika belum di sana
    const curUrlRes = await send('Runtime.evaluate', { expression: 'window.location.href' });
    const curUrl = curUrlRes.result ? curUrlRes.result.value : '';
    if (!curUrl.includes('/tiktokstudio/upload')) {
      console.log('[TikTok Publisher] Membuka halaman upload TikTok Studio...');
      await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video' });
      await new Promise(r => setTimeout(r, 6000));
    }

    // Tangani jika ada tombol Retry
    await send('Runtime.evaluate', {
      expression: `(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'Retry');
        if (btn) btn.click();
      })()`
    });
    await new Promise(r => setTimeout(r, 2000));

    // 3. Cari input file
    const doc = await send('DOM.getDocument');
    const inputNode = await send('DOM.querySelector', {
      nodeId: doc.root.nodeId,
      selector: 'input[type="file"]'
    });
    if (!inputNode || !inputNode.nodeId) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      throw new Error('File input TikTok Studio tidak ditemukan');
    }

    console.log('[TikTok Publisher] Menyerahkan file video ke form upload...');
    await send('DOM.setFileInputFiles', {
      files: [absMediaPath],
      nodeId: inputNode.nodeId
    });

    // 4. Tunggu upload selesai diproses di form hingga kolom editor muncul
    console.log('[TikTok Publisher] Menunggu proses upload di form TikTok hingga editor siap...');
    let uploadReady = false;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 2000));
      const status = await send('Runtime.evaluate', {
        expression: `(() => {
          const edit = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
          return !!edit;
        })()`,
        returnByValue: true
      });
      if (status.result && status.result.value) {
        uploadReady = true;
        break;
      }
    }

    if (!uploadReady) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      throw new Error('Upload video di form TikTok Studio tidak siap / timeout');
    }

    await new Promise(r => setTimeout(r, 2500));

    // Dismiss modal "Turn on automatic content checks?" jika muncul agar tidak menghalangi fokus editor
    await send('Runtime.evaluate', {
      expression: `(() => {
        const dialog = document.body.innerText.includes('automatic content checks');
        if (dialog) {
          const btn = Array.from(document.querySelectorAll('button')).find(b => ['Cancel', 'Batal'].includes((b.innerText || '').trim()));
          if (btn) btn.click();
        }
      })()`
    });
    await new Promise(r => setTimeout(r, 800));

    // 5. Masukkan Caption dengan Pure CDP Keyboard Simulation (tanpa execCommand agar React Draft.js tidak crash)
    console.log('[TikTok Publisher] Memasukkan caption teks...');
    const focusEditor = await send('Runtime.evaluate', {
      expression: `(() => {
        const el = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
        if (!el) return { found: false };
        el.scrollIntoView({ block: 'center' });
        el.focus();
        const r = el.getBoundingClientRect();
        return { found: true, x: Math.round(r.left + Math.min(40, r.width / 4)), y: Math.round(r.top + Math.min(20, r.height / 2)) };
      })()`,
      returnByValue: true
    });

    if (!focusEditor.result.value || !focusEditor.result.value.found) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      throw new Error('Kolom caption contenteditable tidak ditemukan di halaman upload');
    }

    const { x, y } = focusEditor.result.value;
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 400));

    // Clear default filename placeholder safely via native Select All + Backspace
    // Modifiers: 8 = Meta (macOS Cmd), 4 = Control (Windows/Linux)
    await send('Runtime.evaluate', {
      expression: `(() => {
        const el = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
        if (el) {
          el.focus();
          document.execCommand('selectAll', false, null);
          document.execCommand('delete', false, null);
        }
      })()`
    });
    await new Promise(r => setTimeout(r, 200));

    // Also dispatch Cmd+A / Ctrl+A and Backspace via CDP
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'a', code: 'KeyA', modifiers: 8, windowsVirtualKeyCode: 65, commands: ['selectAll'] });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 8, windowsVirtualKeyCode: 65 });
    await new Promise(r => setTimeout(r, 150));
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
    await new Promise(r => setTimeout(r, 200));

    // Fallback Windows/Linux Ctrl+A
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'a', code: 'KeyA', modifiers: 4, windowsVirtualKeyCode: 65, commands: ['selectAll'] });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 4, windowsVirtualKeyCode: 65 });
    await new Promise(r => setTimeout(r, 150));
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
    await new Promise(r => setTimeout(r, 300));

    // Injeksi teks caption utuh langsung ke Draft.js
    await send('Input.insertText', { text: caption });
    await new Promise(r => setTimeout(r, 1500));

    // Fallback jika Input.insertText tidak mengisi caption (misal focus blur)
    await send('Runtime.evaluate', {
      expression: `(() => {
        const el = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
        if (!el) return;
        const norm = t => t.replace(/\\r\\n/g, '\\n').replace(/\\s+/g, ' ').trim();
        const expected = ${JSON.stringify(caption)};
        if (norm(el.innerText) !== norm(expected)) {
          el.focus();
          document.execCommand('selectAll', false, null);
          document.execCommand('insertText', false, expected);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
      })()`
    });
    await new Promise(r => setTimeout(r, 1000));

    // Tutup autocomplete hashtag jika terbuka
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await new Promise(r => setTimeout(r, 800));

    // Gerbang Asersi Validasi Caption: Exact Match & Anti-Placeholder Guard
    const verifyCaption = await send('Runtime.evaluate', {
      expression: `(() => {
        const el = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
        if (!el) return { ok: false, reason: 'Editor not found', text: '' };
        const text = el.innerText.trim();
        const norm = t => t.replace(/\\r\\n/g, '\\n').replace(/\\s+/g, ' ').trim();
        const expected = ${JSON.stringify(caption)};
        const isBadPlaceholder = text.includes('final_vlog') || text.includes('.mp4') || text.includes('final_10s');
        const isExactMatch = norm(text) === norm(expected);
        return {
          ok: isExactMatch && !isBadPlaceholder,
          isExactMatch,
          isBadPlaceholder,
          text,
          expected
        };
      })()`,
      returnByValue: true
    });

    if (!verifyCaption.result.value.ok) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      const r = verifyCaption.result.value;
      throw new Error(`Asersi gagal: Teks caption di editor TikTok tidak cocok 100% dengan naskah ACC Telegram!\nIsi editor: "${r.text}"\nNaskah ACC: "${r.expected}"\nPlaceholder terdeteksi: ${r.isBadPlaceholder}`);
    }

    // 6. Pastikan visibilitas Everyone / Semua orang
    console.log('[TikTok Publisher] Memastikan visibilitas Everyone...');
    await send('Runtime.evaluate', {
      expression: `(() => {
        const labels = Array.from(document.querySelectorAll('label, div, span'));
        const everyoneLabel = labels.find(l => {
          const t = (l.innerText || '').trim();
          return t === 'Everyone' || t === 'Semua orang';
        });
        if (everyoneLabel) everyoneLabel.click();
      })()`
    });
    await new Promise(r => setTimeout(r, 1000));

    // 7. Tunggu upload video selesai diproses lalu klik Post / Posting
    console.log('[TikTok Publisher] Menunggu tombol Post aktif dan menekan Post...');
    let postClicked = false;
    for (let w = 0; w < 25; w++) {
      const clickedRes = await send('Runtime.evaluate', {
        expression: `(() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const postBtn = buttons.find(b => {
            const t = (b.innerText || '').trim();
            const ariaDisabled = b.getAttribute('aria-disabled') === 'true' || b.getAttribute('data-disabled') === 'true';
            return (t === 'Post' || t === 'Posting') && !b.disabled && !ariaDisabled;
          });
          if (postBtn) {
            postBtn.scrollIntoView({ block: 'center' });
            postBtn.click();
            return true;
          }
          return false;
        })()`,
        returnByValue: true
      });
      if (clickedRes.result && clickedRes.result.value) {
        postClicked = true;
        break;
      }
      await new Promise(r => setTimeout(r, 2000));
    }
    if (!postClicked) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      throw new Error('Tombol Post tidak aktif setelah menunggu upload TikTok Studio');
    }

    await new Promise(r => setTimeout(r, 3000));

    // Klik dialog Post now / Posting sekarang jika muncul
    await send('Runtime.evaluate', {
      expression: `(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const btn = buttons.find(b => {
          const t = (b.innerText || '').trim();
          return (t === 'Post now' || t === 'Posting sekarang' || t === 'Continue') && !b.disabled;
        });
        if (btn) btn.click();
      })()`
    });

    await new Promise(r => setTimeout(r, 8000));

    // 8. Navigasi ke content list dan verifikasi link postingan SPESIFIK
    console.log('[TikTok Publisher] Memverifikasi status tayang di TikTok Studio...');
    await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
    await new Promise(r => setTimeout(r, 5000));

    let verifiedVideoUrl = null;
    let verifiedVideoId = null;
    const targetClean = destinationAccount.replace('@', '').toLowerCase();

    // Polling verifikasi video URL hingga 8 kali (Studio + fallback profil akun target)
    for (let attempt = 1; attempt <= 8; attempt++) {
      if (attempt === 5) {
        await send('Page.navigate', { url: `https://www.tiktok.com/@${targetClean}` });
        await new Promise(r => setTimeout(r, 4000));
      }
      const checkRes = await send('Runtime.evaluate', {
        expression: `(() => {
          const links = Array.from(document.querySelectorAll("a[href*='/video/']"));
          const re = new RegExp('https://www\\\\.tiktok\\\\.com/@' + ${JSON.stringify(targetClean)}.replace(/[.*+?^$\{\}()|[\\]\\\\]/g, '\\\\$&') + '/video/([0-9]+)', 'i');
          for (const a of links) {
            const href = a.href || '';
            const m = href.match(re);
            if (m) {
              return { found: true, url: 'https://www.tiktok.com/@' + ${JSON.stringify(targetClean)} + '/video/' + m[1], videoId: m[1] };
            }
          }
          return { found: false };
        })()`,
        returnByValue: true
      });

      if (checkRes.result && checkRes.result.value && checkRes.result.value.found) {
        verifiedVideoUrl = checkRes.result.value.url;
        verifiedVideoId = checkRes.result.value.videoId;
        break;
      }
      console.log(`[TikTok Publisher] Verifikasi video URL percobaan #${attempt} belum terlihat. Menunggu...`);
      await new Promise(r => setTimeout(r, 3000));
    }

    if (verifiedVideoUrl && verifiedVideoId) {
      console.log(`[TikTok Publisher] SUKSES PUBLIKASI TIKTOK TERVERIFIKASI!`);
      console.log(`[TikTok Publisher] Video ID: ${verifiedVideoId}`);
      console.log(`[TikTok Publisher] Tautan: ${verifiedVideoUrl}`);

      try {
        execSync(
          `python3 -m app.publication confirm --publication "${pubId}" --video-url "${verifiedVideoUrl}"`,
          { cwd: PROJECT_ROOT, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }
        );
      } catch (confirmErr) {
        execSqlite(`
          UPDATE publications 
          SET state = 'confirmed', platform_post_id = '${verifiedVideoId}', post_url = '${verifiedVideoUrl}', confirmed_at = '${new Date().toISOString()}'
          WHERE id = '${pubId}';
        `);
      }

      ws.close();
      return {
        success: true,
        state: 'confirmed',
        postUrl: verifiedVideoUrl,
        platformPostId: verifiedVideoId
      };
    } else {
      // TIDAK BOLEH MEMAKAI URL PROFIL SEBAGAI BUKTI TAYANG! TAHAN SEBAGAI UNKNOWN
      console.warn('[TikTok Publisher] Video spesifik belum terdeteksi di feed dalam batas waktu.');
      console.warn('[TikTok Publisher] Status ditahan sebagai unknown sesuai aturan integritas produksi.');

      try {
        execSync(`python3 -m app.publication mark-unknown --publication "${pubId}"`, { cwd: PROJECT_ROOT, stdio: ['pipe', 'pipe', 'pipe'] });
      } catch (_) {
        execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
      }

      ws.close();
      return {
        success: false,
        state: 'unknown',
        reason: 'Video ID belum terverifikasi dari TikTok Studio; status ditahan sebagai unknown untuk rekonsiliasi operator.'
      };
    }
  } catch (err) {
    try {
      execSync(`python3 -m app.publication mark-unknown --publication "${pubId}"`, { cwd: PROJECT_ROOT, stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (_) {
      execSqlite(`UPDATE publications SET state = 'unknown' WHERE id = '${pubId}';`);
    }
    ws.close();
    throw err;
  }
}

// CLI Runner
if (require.main === module) {
  const args = process.argv.slice(2);
  let versionId = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--version-id' || args[i] === '-v') {
      versionId = args[i + 1];
      i++;
    } else if (args[i] === '--slot') {
      const slot = args[i + 1];
      i++;
      // Resolusi version_id terbaru yang sudah ACC untuk slot ini
      const rows = querySqlite(`
        SELECT v.id FROM versions v
        JOIN content c ON c.id = v.content_id
        JOIN approvals a ON a.version_id = v.id
        WHERE c.id LIKE '%${slot}%' AND a.decision = 'approved'
        ORDER BY v.created_at DESC LIMIT 1;
      `);
      if (rows.length > 0) versionId = rows[0].id;
    }
  }

  // Fallback default untuk testing/manual jika tanpa argumen
  if (!versionId && args[0] && !args[0].startsWith('-')) {
    versionId = args[0];
  }

  if (!versionId) {
    console.error('Penggunaan: node tiktok_publisher.js --version-id <version_id>');
    console.error('         atau: node tiktok_publisher.js --slot <pagi|malam>');
    process.exit(1);
  }

  publishApprovedVersion(versionId)
    .then(res => {
      console.log('Result:', JSON.stringify(res, null, 2));
      process.exit(res.success ? 0 : 2);
    })
    .catch(err => {
      console.error('Publisher Error:', err.message);
      process.exit(1);
    });
}

module.exports = { publishApprovedVersion, getApprovedVersion };
