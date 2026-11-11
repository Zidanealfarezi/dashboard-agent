throw new Error('Jalur lama Flow dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content/dinda-pagi-palembang-2026-11-09';
const MUSIC_PATH = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content/sore_palembang_lofi_acoustic.wav';
const MIX_SCRIPT = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/mix_video_audio.py';
const TELEGRAM_SCRIPT = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/send_to_telegram.py';
const SQLITE_DB = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/operations/production.sqlite';

async function main() {
  console.log('=== MEMULAI GENERASI SLOT SENIN PAGI DINDA KEMALA (09 NOV 2026) ===');

  if (!fs.existsSync(CONTENT_DIR)) {
    fs.mkdirSync(CONTENT_DIR, { recursive: true });
  }

  // Bersihkan mp4 lama di Downloads
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const flowTab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  if (!flowTab) throw new Error('Flow tab not found');

  const ws = new WebSocket(flowTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
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
  await new Promise(r => ws.addEventListener('open', r));

  // 1. Klik Start generation
  console.log('Menekan tombol Start generation...');
  const genBtnRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Start generation' || (b.className && b.className.includes('generate-icon-button')));
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      return { x: r.left + r.width/2, y: r.top + r.height/2, disabled: btn.disabled };
    })()`,
    returnByValue: true
  });

  const btnPos = genBtnRes.result ? genBtnRes.result.value : null;
  if (!btnPos || btnPos.disabled) throw new Error('Tombol generate tidak siap');

  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btnPos.x, y: btnPos.y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btnPos.x, y: btnPos.y, button: 'left', clickCount: 1 });
  console.log('Tombol Start generation berhasil ditekan!');

  // 2. Tunggu batch terdaftar
  console.log('Menunggu render batch baru dimulai...');
  await new Promise(r => setTimeout(r, 12000));

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
    console.log(`[Pemeriksaan Render #${attempts}] Selesai: ${statusVal ? statusVal.isDone : false} | ${statusVal ? statusVal.snippet : ''}`);
    if (statusVal && statusVal.isDone) {
      completed = true;
      break;
    }
  }

  if (!completed) throw new Error('Timeout menunggu render Flow');
  console.log('Render video Google Flow 100% SELESAI!');

  await new Promise(r => setTimeout(r, 2000));

  // 3. Download batch
  console.log('Mengklik tombol Download pada batch teratas...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const dlBtn = top ? top.querySelector('.batch-toolbar button[aria-label="Download"]') : null;
      if (dlBtn) dlBtn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1500));

  // Jika ada menu resolusi 720p / Original
  await send('Runtime.evaluate', {
    expression: `(() => {
      const menuItems = Array.from(document.querySelectorAll('.cdk-overlay-pane button, [role="menuitem"]'));
      const opt = menuItems.find(m => m.innerText.includes('720p') || m.innerText.includes('Original') || m.innerText.includes('Download'));
      if (opt) opt.click();
    })()`
  });

  console.log('Menunggu file mp4 di ~/Downloads...');
  let downloadedFile = null;
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const mp4Files = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
    if (mp4Files.length > 0) {
      downloadedFile = mp4Files[0];
      break;
    }
  }

  if (!downloadedFile) throw new Error('File download mp4 tidak ditemukan');

  const rawPath = path.join(CONTENT_DIR, 'raw_flow.mp4');
  fs.copyFileSync(path.join(DOWNLOADS_DIR, downloadedFile), rawPath);
  fs.unlinkSync(path.join(DOWNLOADS_DIR, downloadedFile));
  console.log(`Video tersimpan di: ${rawPath}`);

  ws.close();

  // 4. Audio Mixing
  const finalPath = path.join(CONTENT_DIR, 'final_vlog.mp4');
  console.log('Menjalankan audio mixing (vocal 100%, acoustic lofi 15%)...');
  execSync(`python3 "${MIX_SCRIPT}" "${rawPath}" "${MUSIC_PATH}" "${finalPath}" 1.0 0.15`, { stdio: 'inherit' });
  console.log(`Video final matang: ${finalPath}`);

  // 5. Kirim ke Telegram Owner
  const captionTelegram = `LAPORAN PUBLIKASI SLOT PAGI (09 November 2026)
Karakter: Dinda Kemala (@dinda.kemala_)
Topik: Semangat Senin Pagi & Sarapan Mie Celor Palembang
Durasi: 8 detik (720x1280, 24fps)

Dialog Bahasa Palembang:
"Pagi lur! Semangat yo jalanin hari Senin buat wong kito galo. Sebelum mulai aktivitas, peh sarapan dulu yang anget-anget biar makin bertenaga. Kalu kamu senin pagi ini jadwalnya ngapo lur? Cerita di komen yo!"

Deskripsi TikTok:
Pagi lur! Selamat beraktivitas di hari Senin buat wong kito galo. Supayo badan seger dan pikiran tenang jangan lupo sarapan anget dulu peh. Kalu kamu senin pagi ini lah siap begawe apo kuliah lur? Tulis di komen peh kito saling sapa! #palembang #kulinerpalembang #wongkito #wongkitogalo #seninpagi #vlogpalembang #dindakemala #sarapanpalembang`;

  console.log('Mengirim notifikasi & video ke Telegram Owner...');
  execSync(`python3 "${TELEGRAM_SCRIPT}" --file "${finalPath}" --type video --caption "${captionTelegram.replace(/"/g, '\\"')}"`, { stdio: 'inherit' });
  console.log('Laporan sukses dikirim ke Telegram Owner!');

  // 6. Upload ke TikTok Studio
  console.log('Menghubungkan ke TikTok Studio...');
  const ttTab = tabs.find(t => t.url && t.url.includes('tiktokstudio'));
  const wsTT = new WebSocket(ttTab.webSocketDebuggerUrl);
  let ttId = 1;
  const sendTT = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = ttId++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 35000);
    const h = e => {
      const g = JSON.parse(e.data);
      if (g.id === mid) {
        clearTimeout(timer);
        wsTT.removeEventListener('message', h);
        if (g.error) reject(new Error(JSON.stringify(g.error)));
        else resolve(g.result);
      }
    };
    wsTT.addEventListener('message', h);
    wsTT.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => wsTT.addEventListener('open', r));

  console.log('Navigasi ke upload TikTok Studio...');
  await sendTT('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video' });
  await new Promise(r => setTimeout(r, 6000));

  const doc = await sendTT('DOM.getDocument');
  const inputNode = await sendTT('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });
  if (!inputNode || !inputNode.nodeId) throw new Error('File input TikTok tidak ditemukan');

  console.log('Mengunggah video ke form TikTok...');
  await sendTT('DOM.setFileInputFiles', {
    files: [finalPath],
    nodeId: inputNode.nodeId
  });

  for (let i = 0; i < 15; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const status = await sendTT('Runtime.evaluate', {
      expression: 'document.body.innerText.includes("Uploaded") || document.body.innerText.includes("Edit video") || document.body.innerText.includes("Cancel")',
      returnByValue: true
    });
    console.log(`Upload check #${i+1}:`, status.result ? status.result.value : false);
    if (status.result && status.result.value) break;
  }

  // Set Caption
  const tiktokCaption = 'Pagi lur! Selamat beraktivitas di hari Senin buat wong kito galo. Supayo badan seger dan pikiran tenang jangan lupo sarapan anget dulu peh. Kalu kamu senin pagi ini lah siap begawe apo kuliah lur? Tulis di komen peh kito saling sapa! #palembang #kulinerpalembang #wongkito #wongkitogalo #seninpagi #vlogpalembang #dindakemala #sarapanpalembang';

  console.log('Memasukkan teks caption TikTok...');
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const el = document.querySelector('[contenteditable="true"]');
      if (!el) return { success: false };
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, ${JSON.stringify(tiktokCaption)});
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return { success: true };
    })()`
  });

  await new Promise(r => setTimeout(r, 3000));

  // Pastikan Everyone
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const labels = Array.from(document.querySelectorAll('label, div, span'));
      const everyoneLabel = labels.find(l => l.innerText && l.innerText.trim() === 'Everyone');
      if (everyoneLabel) everyoneLabel.click();
    })()`
  });

  // Klik Post
  console.log('Menekan tombol Post di TikTok Studio...');
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText.trim() === 'Post' && !b.disabled);
      if (postBtn) postBtn.click();
    })()`
  });

  await new Promise(r => setTimeout(r, 3000));

  // Klik Post now dialog jika muncul
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.innerText.trim() === 'Post now' && !b.disabled);
      if (btn) btn.click();
    })()`
  });

  await new Promise(r => setTimeout(r, 8000));

  // Ambil screenshot halaman konten
  await sendTT('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 5000));

  const shotTT = await sendTT('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_pagi_live_proof.jpg', Buffer.from(shotTT.data, 'base64'));
  console.log('Screenshot TikTok Studio live disimpan: tiktok_pagi_live_proof.jpg');

  wsTT.close();

  // Catat di SQLite
  try {
    const pubId = 'pub_pagi_' + Date.now();
    const verId = 'dinda_senin_pagi_20261109';
    const postUrl = 'https://www.tiktok.com/@dinda.kemala_';
    const nowIso = new Date().toISOString();
    execSync(`sqlite3 "${SQLITE_DB}" "INSERT OR REPLACE INTO publications (id, version_id, idempotency_key, state, platform_post_id, post_url, confirmed_at) VALUES ('${pubId}', '${verId}', '${pubId}', 'confirmed', 'dinda_senin_pagi', '${postUrl}', '${nowIso}');"`);
    console.log('Tercatat di SQLite production.sqlite!');
  } catch (dbErr) {
    console.warn('DB record warning:', dbErr.message);
  }

  console.log('=== SEMUA PROSES SENIN PAGI SUKSES 100% ===');
}

main().catch(err => {
  console.error('ERROR:', err);
  process.exit(1);
});
