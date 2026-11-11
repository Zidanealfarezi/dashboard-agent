// Click at viewport coords on Flow tab, then dump screenshot + body text.
const fs = require('fs');
const x = Number(process.argv[2]);
const y = Number(process.argv[3]);
const out = process.argv[4] || '/Users/zidane/.hermes/cache/scratch/flow_click.png';

async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  if (!tab) throw new Error('Flow page tab not found');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 40000);
    const h = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === mid) { clearTimeout(timer); ws.removeEventListener('message', h); resolve(msg.result); }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  await new Promise(r => setTimeout(r, 2500));
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  const info = await send('Runtime.evaluate', {
    expression: `(() => ({text: document.body.innerText.replace(/\\s+/g,' ').slice(0,4000)}))()`,
    returnByValue: true
  });
  console.log(info.result.value.text);
  console.log('SCREENSHOT', out);
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
