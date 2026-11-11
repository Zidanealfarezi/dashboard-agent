// Navigate the Flow tab to a URL and capture state/screenshot.
const fs = require('fs');
const url = process.argv[2];
const out = process.argv[3] || '/Users/zidane/.hermes/cache/scratch/flow_nav.png';

async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  if (!tab) throw new Error('Flow page tab not found');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 60000);
    const h = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === mid) { clearTimeout(timer); ws.removeEventListener('message', h); resolve(msg.result); }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));
  await send('Page.enable');
  await send('Page.navigate', { url });
  await new Promise(r => setTimeout(r, 6000));
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  const info = await send('Runtime.evaluate', {
    expression: `(() => ({url: location.href, title: document.title, text: document.body.innerText.replace(/\\s+/g,' ').slice(0,3000)}))()`,
    returnByValue: true
  });
  console.log(JSON.stringify(info.result.value, null, 2));
  console.log('SCREENSHOT', out);
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
