// Probe: temukan aset video terbaru di proyek Flow Bang Ray dan unduh.
const fs = require('fs');
const path = require('path');
const CDP_PORT = 9333;
const KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';
const DOWNLOADS = '/Users/zidane/Downloads';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
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

  const cards = await ev(`(() => {
    const nodes = Array.from(document.querySelectorAll('[role=group], .video-card, .asset-card, .media-card, mat-card, article'));
    const out = [];
    for (const n of nodes) {
      const t = (n.innerText || '').replace(/\\s+/g, ' ').trim();
      if (!t) continue;
      const r = n.getBoundingClientRect();
      if (r.width < 40 || r.height < 40) continue;
      out.push({ text: t.slice(0, 70), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) });
      if (out.length >= 12) break;
    }
    return out;
  })()`);
  console.log('kartu terlihat:', JSON.stringify(cards, null, 1));

  const dlBtns = await ev(`(() => {
    const bs = Array.from(document.querySelectorAll('button')).filter(b => /unduh|download/i.test((b.getAttribute('aria-label')||'') + (b.innerText||'')));
    return bs.slice(0,8).map(b => { const r=b.getBoundingClientRect(); return { label:(b.getAttribute('aria-label')||b.innerText||'').trim().slice(0,40), x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2) }; });
  })()`);
  console.log('tombol unduh:', JSON.stringify(dlBtns, null, 1));
  ws.close();
}
main().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
