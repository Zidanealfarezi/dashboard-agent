// Click an element by CSS selector on the Flow tab, then screenshot + text.
const fs = require('fs');
const sel = process.argv[2];
const out = process.argv[3] || '/Users/zidane/.hermes/cache/scratch/flow_sel.png';
async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 40000);
    const h = (e) => { const msg = JSON.parse(e.data); if (msg.id === mid) { clearTimeout(timer); ws.removeEventListener('message', h); resolve(msg.result); } };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));
  const r = await send('Runtime.evaluate', {
    expression: `(() => { const el = document.querySelector(${JSON.stringify(sel)}); if(!el) return 'NOT FOUND'; el.click(); return 'clicked'; })()`,
    returnByValue: true
  });
  console.log('CLICK', r.result.value);
  await new Promise(r => setTimeout(r, 2000));
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  const info = await send('Runtime.evaluate', { expression: `(() => document.body.innerText.replace(/\\s+/g,' ').slice(-2500))()`, returnByValue: true });
  console.log(info.result.value);
  console.log('SCREENSHOT', out);
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
