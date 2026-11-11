// Inspect DOM around prompt bar: elements with text Video/720p/8s, buttons, rects.
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
      const walk = document.querySelectorAll('*');
      for (const el of walk) {
        if (el.children.length > 3) continue;
        const t = (el.innerText||'').trim();
        if (!t || t.length > 60) continue;
        if (/720p|Video|8s|9:16|Omni|credit/i.test(t)) {
          const r = el.getBoundingClientRect();
          if (r.width === 0) continue;
          out.push({tag: el.tagName, cls: (el.className||'').toString().slice(0,60), text: t.replace(/\\s+/g,' '), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)});
        }
      }
      return out.slice(0, 60);
    })()`,
    returnByValue: true
  });
  console.log(JSON.stringify(res.result.value, null, 1));
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
