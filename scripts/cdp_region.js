// Dump interactive elements in a y-range (viewport coords) of the Flow page.
const y1 = Number(process.argv[2] || 690), y2 = Number(process.argv[3] || 800);
async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 30000);
    const h = (e) => { const msg = JSON.parse(e.data); if (msg.id === mid) { clearTimeout(timer); ws.removeEventListener('message', h); resolve(msg.result); } };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));
  const res = await send('Runtime.evaluate', {
    expression: `(() => {
      const out = [];
      for (const el of document.querySelectorAll('button,[role=button],input,textarea,[contenteditable=true],span,div')) {
        const r = el.getBoundingClientRect();
        if (r.y < ${y1} || r.y > ${y2} || r.width === 0) continue;
        const t = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g,' ');
        if (!t || t.length > 90) continue;
        if (el.children.length && el.tagName === 'DIV' && el.children.length > 2) continue;
        out.push({tag: el.tagName, role: el.getAttribute('role'), label: el.getAttribute('aria-label'), text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), w: Math.round(r.width), h: Math.round(r.height)});
      }
      const seen = new Set();
      return out.filter(o => { const k=o.tag+o.text+o.x+o.y; if(seen.has(k)) return false; seen.add(k); return true; }).slice(0,80);
    })()`,
    returnByValue: true
  });
  console.log(JSON.stringify(res.result.value, null, 1));
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
