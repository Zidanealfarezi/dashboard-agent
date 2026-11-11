throw new Error('Jalur lama TikTok dinonaktifkan. Ikuti docs/production-controls.md.');

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
    console.log('Clicking Post now button...');
    const clickExpr = `
      (() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const btn = buttons.find(b => b.innerText.trim() === 'Post now' && !b.disabled);
        if (!btn) return { success: false, reason: 'Button not found' };
        btn.click();
        return { success: true };
      })()
    `;
    const res = await send('Runtime.evaluate', { expression: clickExpr, returnByValue: true });
    console.log('Click Post now res:', res.result.value);

    // Wait 6 seconds
    await new Promise(r => setTimeout(r, 6000));

    const state = await send('Runtime.evaluate', {
      expression: '({url: location.href, text: document.body.innerText.slice(0, 1000)})',
      returnByValue: true
    });
    console.log('Current state:', state.result.value);

    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
    fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_final_after_post_now.jpg', Buffer.from(shot.data, 'base64'));
    console.log('Saved tiktok_final_after_post_now.jpg');

    ws.close();
  };
}

main().catch(console.error);
