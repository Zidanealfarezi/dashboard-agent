// Setelah klik Download, pilih opsi kualitas yang muncul (jika ada) dan tunggu file baru.
const fs = require('fs');
const CDP_PORT = 9333;
const KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';
const DOWNLOADS = '/Users/zidane/Downloads';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const mp4s = () => fs.readdirSync(DOWNLOADS).filter(f => /\.(mp4|webm)$/i.test(f));

async function main() {
  const before = new Set(mp4s());
  const tabs = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes(KEY));
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 1; const pending = new Map();
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.t); pending.delete(m.id); m.error ? p.j(new Error(JSON.stringify(m.error))) : p.r(m.result); }
  });
  const send = (method, params = {}) => new Promise((r, j) => {
    const mid = id++; const t = setTimeout(() => { pending.delete(mid); j(new Error('timeout ' + method)); }, 40000);
    pending.set(mid, { r, j, t }); ws.send(JSON.stringify({ id: mid, method, params }));
  });
  const ev = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.value;

  await send('Page.enable');
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS });

  // Buka menu download lewat tombol toolbar aset
  const dl = await ev(`(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => /^download$/i.test((x.getAttribute('aria-label')||'').trim()) || /Download media/i.test(x.getAttribute('aria-label')||''));
    if (!b) return null; const r = b.getBoundingClientRect();
    return { x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) };
  })()`);
  console.log('tombol download:', JSON.stringify(dl));
  if (!dl) throw new Error('tombol download tidak ada');
  for (const type of ['mousePressed', 'mouseReleased'])
    await send('Input.dispatchMouseEvent', { type, x: dl.x, y: dl.y, button: 'left', clickCount: 1 });
  await sleep(2000);

  const menu = await ev(`(() => {
    const nodes = Array.from(document.querySelectorAll('.cdk-overlay-container li, .cdk-overlay-container button, [role=menuitem], [role=option]'));
    return nodes.map(n => (n.innerText || n.getAttribute('aria-label') || '').replace(/\\s+/g,' ').trim()).filter(Boolean).slice(0, 12);
  })()`);
  console.log('menu setelah klik:', JSON.stringify(menu));

  if (menu.length) {
    const pos = await ev(`(() => {
      const nodes = Array.from(document.querySelectorAll('.cdk-overlay-container li, .cdk-overlay-container button, [role=menuitem], [role=option]'));
      const target = nodes.find(n => /360|unduh|download|mp4/i.test((n.innerText||'') + ' ' + (n.getAttribute('aria-label')||'')));
      if (!target) return null; const r = target.getBoundingClientRect();
      return { label: (target.innerText||'').trim().slice(0,30), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) };
    })()`);
    console.log('pilihan:', JSON.stringify(pos));
    if (pos) {
      for (const type of ['mousePressed', 'mouseReleased'])
        await send('Input.dispatchMouseEvent', { type, x: pos.x, y: pos.y, button: 'left', clickCount: 1 });
    }
  }

  let fresh = [];
  for (let i = 0; i < 90; i++) {
    await sleep(1000);
    fresh = mp4s().filter(f => !before.has(f));
    if (fresh.length) break;
  }
  console.log('file baru:', JSON.stringify(fresh));
  ws.close();
}
main().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
