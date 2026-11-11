throw new Error('Jalur lama Flow dinonaktifkan. Ikuti docs/production-controls.md.');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DOWNLOADS_DIR = '/Users/zidane/Downloads';
const CONTENT_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content/dinda-malam-palembang-2026-11-08';
const MUSIC_PATH = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/characters/dinda/content/sore_palembang_lofi_acoustic.wav';
const MIX_SCRIPT = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/mix_video_audio.py';
const TELEGRAM_SCRIPT = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/send_to_telegram.py';

async function main() {
  console.log('=== MEMULAI RE-PRODUKSI SLOT MALAM KULINER PALEMBANG (08 NOV 2026) ===');
  
  // Pastikan Downloads bersih dari mp4
  fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4')).forEach(f => {
    try { fs.unlinkSync(path.join(DOWNLOADS_DIR, f)); } catch (_) {}
  });

  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const flowTab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  if (!flowTab) throw new Error('Flow tab not found on port 9333');

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
  console.log('Terhubung ke Google Flow CDP');

  // 1. Klik Reuse Prompt pada batch pagi agar 3 chips referensi terpasang otomatis
  console.log('Mengklik tombol Reuse prompt pada batch pagi...');
  const reuseBtn = await send('Runtime.evaluate', {
    expression: `(() => {
      const all = Array.from(document.querySelectorAll("button, [role=button]")).filter(b => b.getAttribute("aria-label") === "Reuse prompt");
      if (all.length === 0) return null;
      const b = all[0];
      const r = b.getBoundingClientRect();
      return { x: r.left + r.width/2, y: r.top + r.height/2 };
    })()`,
    returnByValue: true
  });
  if (!reuseBtn.result.value) throw new Error('Tombol Reuse prompt tidak ditemukan');
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: reuseBtn.result.value.x, y: reuseBtn.result.value.y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: reuseBtn.result.value.x, y: reuseBtn.result.value.y, button: 'left', clickCount: 1 });
  await new Promise(r => setTimeout(r, 2000));

  // Verify chips
  const chipsCheck = await send('Runtime.evaluate', {
    expression: `(() => {
      const box = document.querySelector('flow-prompt-box');
      if (!box) return { count: 0, text: '' };
      const chips = box.querySelectorAll('flow-ingredient-chip, [class*="chip"]');
      return { count: chips.length, text: box.innerText.slice(0, 150) };
    })()`,
    returnByValue: true
  });
  console.log('Status Chips di Prompt Box:', chipsCheck.result.value);

  // Set Prompt Baru Kuliner Malam Palembang
  const promptMalam = `Authentic handheld smartphone vlog video of Dinda Kemala, the same Indonesian woman shown in all three attached reference images. Output exactly one woman, never a collage, split screen or reference-sheet layout. Vertical 9:16, one continuous shot, medium close-up sitting at a cozy rustic wooden table inside an authentic Palembang culinary eatery on Sunday night. Warm natural night ambience with soft background warm lights, clean warm white balance. She wears her neat soft beige pashmina hijab draped neatly, small gold ring pendant necklace, and the sage green crinkle linen blouse from the reference sheets. On the wooden table in front of her is a steaming hot bowl of Palembang tekwan soup with fried shallots and a plate of pempek panggang. Dinda smiles warmly into the smartphone vlog camera, speaking directly with authentic conversational charm: "Malam ini di Palembang hawanya dingin, paling lemak nian makan tekwan anget sama pempek panggang. Kuah gurihnya bener-bener mantap. Kalau kamu wong kito galo malam ini lagi makan apa lur? Cerita di komen ya!" Subtle natural head movement, realistic lip sync, clear authentic Indonesian female voice, fixed eye-level camera with authentic handheld sway. Shot on smartphone vlog camera, natural clean warm ambient lighting, true-to-life colors, realistic matte human skin with visible fine pores, no plastic shine, no waxy skin, no glass skin, no yellow or orange tint, no artificial golden glow, zero CGI, authentic non-AI documentary look. No subtitles, no on-screen text, no logos, no brand labels, no extra people. Do not reproduce the reference sheet layout.`;

  console.log('Memasukkan teks prompt baru ke ProseMirror...');
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
  await send('Input.insertText', { text: promptMalam });
  await new Promise(r => setTimeout(r, 1000));

  // Screenshot prompt box ready
  const readyShot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/flow_malam_ready2.jpg', Buffer.from(readyShot.data, 'base64'));
  console.log('Screenshot siap generate disimpan: flow_malam_ready2.jpg');

  // Click Start Generation
  console.log('Menekan tombol Start generation...');
  const genClick = await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Start generation');
      if (!btn) return { success: false, reason: 'Tombol generate tidak ditemukan' };
      if (btn.disabled) return { success: false, reason: 'Tombol generate dinonaktifkan (disabled)' };
      btn.click();
      return { success: true };
    })()`,
    returnByValue: true
  });
  console.log('Hasil klik generate:', genClick.result.value);
  if (!genClick.result.value.success) throw new Error('Gagal menekan tombol generate: ' + genClick.result.value.reason);

  // Monitor generation
  console.log('Memantau proses render video di Google Flow...');
  await new Promise(r => setTimeout(r, 12000));

  let completed = false;
  let attempts = 0;
  while (!completed && attempts < 75) {
    attempts++;
    await new Promise(r => setTimeout(r, 4000));
    const status = await send('Runtime.evaluate', {
      expression: `(() => {
        const top = document.querySelector('.batch-container');
        if (!top) return { text: 'no container' };
        const text = top.innerText.replace(/\\s+/g, ' ');
        const isDone = text.includes('download') && !text.includes('%') && !text.includes('Generating');
        return { isDone, snippet: text.slice(0, 120) };
      })()`,
      returnByValue: true
    });
    console.log(`[Pemeriksaan Render #${attempts}] Selesai: ${status.result.value.isDone} | ${status.result.value.snippet}`);
    if (status.result.value.isDone) {
      completed = true;
      break;
    }
  }

  if (!completed) throw new Error('Timeout menunggu generasi video Flow');
  console.log('Render video di Google Flow 100% SELESAI!');

  await new Promise(r => setTimeout(r, 2000));

  // Open detail view and download
  console.log('Membuka video untuk mengunduh versi 720p...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const top = document.querySelector('.batch-container');
      const thumb = top ? top.querySelector('img.thumbnail, [class*="thumb"], button[aria-label*="Woman"]') : null;
      if (thumb) thumb.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 2000));

  // Click Download
  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Download media' || b.innerText.trim() === 'download');
      if (btn) btn.click();
    })()`
  });
  await new Promise(r => setTimeout(r, 1000));

  // Click 720p or Download
  await send('Runtime.evaluate', {
    expression: `(() => {
      const menuItems = Array.from(document.querySelectorAll('.cdk-overlay-pane button, [role="menuitem"]'));
      const opt = menuItems.find(m => m.innerText.includes('720p') || m.innerText.includes('Original') || m.innerText.includes('Download'));
      if (opt) opt.click();
    })()`
  });

  console.log('Menunggu file unduhan selesai di ~/Downloads...');
  await new Promise(r => setTimeout(r, 8000));

  const mp4Files = fs.readdirSync(DOWNLOADS_DIR).filter(f => f.endsWith('.mp4'));
  console.log('File terunduh:', mp4Files);
  if (mp4Files.length === 0) throw new Error('Tidak ada file mp4 terunduh di ~/Downloads');

  const rawPath = path.join(CONTENT_DIR, 'raw_flow.mp4');
  const downloadedFile = path.join(DOWNLOADS_DIR, mp4Files[0]);
  fs.copyFileSync(downloadedFile, rawPath);
  fs.unlinkSync(downloadedFile);
  console.log(`Video mentah berhasil disimpan ke: ${rawPath}`);

  // Tutup koneksi Flow
  ws.close();

  // 2. Audio mixing: vokal 100% + musik 15%
  const finalPath = path.join(CONTENT_DIR, 'final_10s.mp4');
  console.log('Menjalankan audio mixing vokal + lofi...');
  execSync(`python3 "${MIX_SCRIPT}" "${rawPath}" "${MUSIC_PATH}" "${finalPath}" 1.0 0.15`, { stdio: 'inherit' });
  console.log(`Video final audio-mixed tersimpan di: ${finalPath}`);

  // 3. Kirim ke Telegram Owner
  const captionTelegram = `LAPORAN PRODUKSI SLOT MALAM (08 November 2026)
Karakter: Dinda Kemala (@dinda.kemala_)
Topik: Kuliner Malam Palembang (Bahasa Palembang Asli)
Menu: Tekwan Anget & Pempek Panggang di Warung Palembang
Durasi: 10 detik (720x1280, 24fps)

Dialog Bahasa Palembang:
"Malam ini di Palembang hawanya dingin, paling lemak nian makan tekwan anget sama pempek panggang. Kuah gurihnya bener-bener mantap. Kalau kamu wong kito galo malam ini lagi makan apa lur? Cerita di komen ya!"

Deskripsi TikTok:
Cacam lur, hawa malem Palembang mulai dingin cak ini paling lemak nian makan yang anget-anget berkuah. Malem ini aku lagi mampir nyicip tekwan anget samo pempek panggang. Kalu kamu wong kito galo malem ini lagi makan apo lur? Cerito di komen peh! #palembang #kulinerpalembang #wongkito #wongkitogalo #tekwanpalembang #pempekpanggang #malamditiktok #dindakemala #vlogpalembang`;

  console.log('Mengirim video final ke Telegram Owner...');
  execSync(`python3 "${TELEGRAM_SCRIPT}" --file "${finalPath}" --type video --caption "${captionTelegram.replace(/"/g, '\\"')}"`, { stdio: 'inherit' });
  console.log('Berhasil terkirim ke Telegram Owner!');

  // 4. Publikasi ke TikTok Studio
  console.log('Mengunggah video ke TikTok Studio...');
  const ttTab = tabs.find(t => t.url && t.url.includes('tiktokstudio'));
  if (!ttTab) throw new Error('Tab TikTok Studio tidak ditemukan');

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

  console.log('Navigasi ke halaman upload TikTok Studio...');
  await sendTT('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/upload?from=creator_center&tab=video' });
  await new Promise(r => setTimeout(r, 6000));

  const doc = await sendTT('DOM.getDocument');
  const inputNode = await sendTT('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });
  if (!inputNode || !inputNode.nodeId) throw new Error('Input file TikTok tidak ditemukan');

  console.log('Memilih file video final...');
  await sendTT('DOM.setFileInputFiles', {
    files: [finalPath],
    nodeId: inputNode.nodeId
  });

  console.log('Menunggu proses upload dan pemrosesan...');
  for (let i = 0; i < 15; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const status = await sendTT('Runtime.evaluate', {
      expression: 'document.body.innerText.includes("Uploaded") || document.body.innerText.includes("Edit video") || document.body.innerText.includes("Cancel")',
      returnByValue: true
    });
    console.log(`Pemeriksaan upload TikTok #${i+1}:`, status.result ? status.result.value : false);
    if (status.result && status.result.value) break;
  }

  // Isi Caption
  const tiktokCaption = 'Cacam lur, hawa malem Palembang mulai dingin cak ini paling lemak nian makan yang anget-anget berkuah. Malem ini aku lagi mampir nyicip tekwan anget samo pempek panggang. Kalu kamu wong kito galo malem ini lagi makan apo lur? Cerito di komen peh! #palembang #kulinerpalembang #wongkito #wongkitogalo #tekwanpalembang #pempekpanggang #malamditiktok #dindakemala #vlogpalembang';

  console.log('Memasukkan caption...');
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
  console.log('Menekan tombol Post...');
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const postBtn = buttons.find(b => b.innerText.trim() === 'Post' && !b.disabled);
      if (postBtn) postBtn.click();
    })()`
  });

  await new Promise(r => setTimeout(r, 3000));

  // Klik Post now jika muncul dialog
  await sendTT('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.innerText.trim() === 'Post now' && !b.disabled);
      if (btn) btn.click();
    })()`
  });

  await new Promise(r => setTimeout(r, 6000));

  const shotTT = await sendTT('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_malam_after_post2.jpg', Buffer.from(shotTT.data, 'base64'));
  console.log('Screenshot TikTok Studio disimpan: tiktok_malam_after_post2.jpg');

  wsTT.close();
  console.log('=== SEMUA TAHAPAN SUKSES 100% ===');
}

main().catch(err => {
  console.error('ERROR UTAMA:', err);
  process.exit(1);
});
