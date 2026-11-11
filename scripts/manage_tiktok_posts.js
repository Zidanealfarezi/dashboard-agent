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
    // Find more actions buttons in the posts table
    const inspectExpr = `
      (() => {
        // Look for buttons or icons in the Actions column
        const buttons = Array.from(document.querySelectorAll('button, [role="button"], span, div'));
        const actionElements = buttons.filter(b => {
          const title = b.getAttribute('title') || '';
          const aria = b.getAttribute('aria-label') || '';
          const text = b.innerText ? b.innerText.trim() : '';
          return title.includes('Delete') || aria.includes('Delete') || aria.includes('More') || title.includes('More') || text === 'Delete' || b.className.includes('action');
        }).map(b => ({
          tag: b.tagName,
          title: b.getAttribute('title'),
          aria: b.getAttribute('aria-label'),
          text: b.innerText ? b.innerText.trim() : '',
          className: b.className
        }));
        return actionElements;
      })()
    `;
    const res = await send('Runtime.evaluate', { expression: inspectExpr, returnByValue: true });
    console.log('Action elements:', res.result.value);

    // Take screenshot of the post table
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
    fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_posts_actions.jpg', Buffer.from(shot.data, 'base64'));
    console.log('Saved tiktok_posts_actions.jpg');

    ws.close();
  };
}

main().catch(console.error);
