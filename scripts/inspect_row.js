const fs = require('fs');

async function main() {
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const ttTab = tabs.find(t => t.url.includes('tiktokstudio'));
  const ws = new WebSocket(ttTab.webSocketDebuggerUrl);

  function send(method, params = {}) {
    return new Promise((resolve) => {
      const id = Math.floor(Math.random() * 100000);
      const handler = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === id) {
          ws.removeEventListener('message', handler);
          resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  ws.onopen = async () => {
    const expr = `
      (() => {
        // Find the table or list container
        const postTexts = Array.from(document.querySelectorAll('*')).filter(el => 
          el.innerText && el.innerText.includes('Malam di Palembang emang gak pernah gagal') && el.children.length === 0
        );
        const firstPost = postTexts[0];
        if (!firstPost) return { found: false };
        // Walk up parents to find row
        let p = firstPost.parentElement;
        while (p && p.tagName !== 'BODY') {
          if (p.querySelector('svg') || p.innerText.includes('Actions') || p.innerText.includes('Everyone')) {
            const svgs = Array.from(p.querySelectorAll('svg')).map(s => ({
              outer: s.outerHTML.slice(0, 100),
              parentTag: s.parentElement.tagName,
              parentClass: s.parentElement.className
            }));
            return {
              found: true,
              parentTag: p.tagName,
              parentClass: p.className,
              svgs: svgs
            };
          }
          p = p.parentElement;
        }
        return { found: false };
      })()
    `;
    const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
    console.log(JSON.stringify(res.result.value, null, 2));
    ws.close();
  };
}

main().catch(console.error);
