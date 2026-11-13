// Klik tombol "Download media" pada aset yang sedang terbuka, lalu laporkan file baru.
const fs = require('fs');
const path = require('path');
const CDP_PORT = 9333;
const KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';
const DOWNLOADS = '/Users/zidane/Downloads';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const mp4s = () => fs.readdirSync(DOWNLOADS).filter(f => f.toLowerCase().endsWith('.mp4'));

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

  const ctx = await ev(`(() => {
    const all = document.body.innerText.replace(/\\s+/g,' ');
    const b = Array.from(document.querySelectorAll('button')).find(x => /Download media/i.test(x.getAttribute('aria-label')||''));
    const r = b ? b.getBoundingClientRect() : null;
    return { head: all.slice(0, 220), hasBtn: !!b, x: r ? Math.round(r.x + r.width/2) : null, y: r ? Math.round(r.y + r.height/2) : null };
  })()`);
  console.log('konteks:', JSON.stringify(ctx));

  if (ctx.hasBtn) {
    for (const type of ['mousePressed', 'mouseReleased'])
      await send('Input.dispatchMouseEvent', { type, x: ctx.x, y: ctx.y, button: 'left', clickCount: 1 });
    console.log('klik Download media terkirim');
  }

  let fresh = [];
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    fresh = mp4s().filter(f => !before.has(f));
    if (fresh.length) break;
  }
  console.log('file baru:', JSON.stringify(fresh));
  ws.close();
}
main().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
