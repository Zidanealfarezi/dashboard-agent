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
    // Click or find the 3 dots (more) menu on the first post row
    const findDots = `
      (() => {
        // Look for buttons with more_vert or svg in the first post row
        const allSvgs = Array.from(document.querySelectorAll('svg'));
        const info = allSvgs.map(s => {
          const rect = s.getBoundingClientRect();
          return {
            rect: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
            parentTag: s.parentElement.tagName,
            parentClass: s.parentElement.className,
            parentAria: s.parentElement.getAttribute('aria-label')
          };
        }).filter(s => s.rect.top > 200 && s.rect.left > 800);
        return info;
      })()
    `;
    const res = await send('Runtime.evaluate', { expression: findDots, returnByValue: true });
    console.log('Action SVGs on the right side:', res.result.value);

    // If found, click the first one
    if (res.result.value && res.result.value.length > 0) {
      const target = res.result.value[0];
      const clickX = target.rect.left + target.rect.width / 2;
      const clickY = target.rect.top + target.rect.height / 2;
      console.log('Dispatching mouse click at:', clickX, clickY);
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: clickX, y: clickY, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: clickX, y: clickY, button: 'left', clickCount: 1 });
      await new Promise(r => setTimeout(r, 1500));

      const menuText = await send('Runtime.evaluate', {
        expression: 'Array.from(document.querySelectorAll(\"div, span, button\")).filter(e => e.innerText && (e.innerText.includes(\"Delete\") || e.innerText.includes(\"Hapus\") || e.innerText.includes(\"Edit\"))).map(e => e.innerText)',
        returnByValue: true
      });
      console.log('Menu text after click:', menuText.result.value);

      const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
      fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_more_menu.jpg', Buffer.from(shot.data, 'base64'));
      console.log('Saved tiktok_more_menu.jpg');
    }

    ws.close();
  };
}

main().catch(console.error);
