// Minimal CDP probe: screenshot + visible text/chips/buttons for the Flow tab.
const fs = require('fs');

const OUT = process.argv[2] || '/Users/zidane/.hermes/cache/scratch/flow_probe.png';

async function main() {
  const tabs = await (await fetch('http://127.0.0.1:9333/json/list')).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes('flow.google.com'));
  if (!tab) throw new Error('Flow page tab not found');
  console.log('TAB', tab.title, tab.url);
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve, reject) => {
    const mid = id++;
    const timer = setTimeout(() => reject(new Error('Timeout ' + m)), 30000);
    const h = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id === mid) { clearTimeout(timer); ws.removeEventListener('message', h); resolve(msg.result); }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  await new Promise(r => ws.addEventListener('open', r));

  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(OUT, Buffer.from(shot.data, 'base64'));
  console.log('SCREENSHOT', OUT);

  const info = await send('Runtime.evaluate', {
    expression: `(() => {
      const vis = el => !!(el && el.offsetParent !== null);
      const text = el => (el ? el.innerText.trim().replace(/\\s+/g,' ') : '');
      const buttons = Array.from(document.querySelectorAll('button')).filter(vis)
        .map(b => ({label: (b.getAttribute('aria-label')||text(b)||'').slice(0,80), disabled: b.disabled}))
        .filter(b => b.label).slice(0,60);
      const pbox = document.querySelector('flow-base-prompt-box');
      const chips = pbox ? Array.from(pbox.querySelectorAll('flow-ingredient-chip, [class*="chip"]')).map(c => c.innerText.trim()).filter(Boolean) : [];
      const durations = Array.from(document.querySelectorAll('[role="option"], button')).filter(vis)
        .map(e => e.innerText.trim()).filter(t => /^(4|6|8|10|12|16)\\s*s|detik|second/i.test(t));
      const bodyText = document.body.innerText.replace(/\\s+/g,' ').slice(0, 4000);
      return {url: location.href, chips, buttons, durations, bodyText};
    })()`,
    returnByValue: true
  });
  console.log(JSON.stringify(info.result.value, null, 2));
  ws.close();
}

main().catch(e => { console.error('ERR', e.message); process.exit(1); });
