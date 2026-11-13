// Probe read-only: struktur komposer Flow untuk proyek Bang Ray.
const CDP_PORT = 9333;
const FLOW_PROJECT_KEY = '3d61dd46-62f0-42c0-9ff0-24c2cbf07b0d';

async function main() {
  const tabs = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && t.url && t.url.includes(FLOW_PROJECT_KEY));
  if (!tab) throw new Error('tab tidak ditemukan');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 1;
  const send = (method, params = {}) => new Promise((res, rej) => {
    const mid = id++;
    const t = setTimeout(() => rej(new Error('timeout ' + method)), 30000);
    const h = e => { const m = JSON.parse(e.data); if (m.id !== mid) return; clearTimeout(t); ws.removeEventListener('message', h); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  const out = await send('Runtime.evaluate', {
    expression: `(() => {
      const pm = document.querySelector('.ProseMirror');
      const trigger = document.querySelector('button[aria-label="Settings trigger"]');
      const files = Array.from(document.querySelectorAll('input[type=file]')).map(i => ({ accept: i.accept, multiple: i.multiple }));
      const buttons = Array.from(document.querySelectorAll('button')).slice(0, 40).map(b => (b.getAttribute('aria-label') || b.innerText || '').trim()).filter(Boolean).slice(0, 30);
      return {
        url: location.href,
        hasProseMirror: !!pm,
        promptText: pm ? pm.innerText.slice(0, 200) : null,
        settings: trigger ? trigger.innerText.replace(/\\s+/g, ' ') : null,
        fileInputs: files,
        buttons
      };
    })()`,
    returnByValue: true
  });
  console.log(JSON.stringify(out.result.value, null, 2));
  ws.close();
}
main().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
