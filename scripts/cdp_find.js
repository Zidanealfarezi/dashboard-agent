// Find elements whose text matches a needle, including shadow roots (depth 3).
const needle = process.argv[2] || 'What do you want';
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
      const found = [];
      function scan(root, depth) {
        if (depth > 4 || !root) return;
        for (const el of root.querySelectorAll('*')) {
          const t = (el.textContent||'').trim();
          if (t && t.length < 120 && t.toLowerCase().includes(${JSON.stringify(needle)}.toLowerCase())) {
            const r = el.getBoundingClientRect();
            found.push({tag: el.tagName, cls: (el.className||'').toString().slice(0,80), text: t.replace(/\\s+/g,' '), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), depth});
          }
          if (el.shadowRoot) scan(el.shadowRoot, depth+1);
        }
      }
      scan(document, 0);
      return found.slice(0, 25);
    })()`,
    returnByValue: true
  });
  console.log(JSON.stringify(res.result.value, null, 1));
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
