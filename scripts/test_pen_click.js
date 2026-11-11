const fs = require('fs');

async function test() {
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const ttTab = tabs.find(t => t.url && t.url.includes('tiktokstudio'));
  const ws = new WebSocket(ttTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (m, p = {}) => new Promise((resolve) => {
    const curId = id++;
    const h = (e) => {
      const g = JSON.parse(e.data);
      if (g.id === curId) {
        ws.removeEventListener('message', h);
        resolve(g.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: curId, method: m, params: p }));
  });

  await new Promise(r => ws.addEventListener('open', r));

  // Hover row 1
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 408, y: 249 });
  await new Promise(r => setTimeout(r, 600));

  // Find Pen icon element
  const penRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const pen = document.querySelector('[data-icon=Pen]');
      if (!pen) return { found: false };
      const r = pen.getBoundingClientRect();
      return {
        found: true,
        x: Math.round(r.left + r.width/2),
        y: Math.round(r.top + r.height/2)
      };
    })()`,
    returnByValue: true
  });
  console.log('Pen element:', penRes.result.value);

  if (penRes.result.value && penRes.result.value.found) {
    const { x, y } = penRes.result.value;
    console.log(`Clicking Pen at (${x}, ${y})...`);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 2000));

    // Check modal or drawer
    const modalCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const modal = document.querySelector('.TUXModal, [role=dialog], [class*="modal"], [class*="drawer"]');
        const inputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable=true]')).map(i => ({
          tag: i.tagName,
          className: i.className,
          val: (i.value || i.innerText || '').slice(0, 50)
        }));
        return {
          hasModal: !!modal,
          inputs
        };
      })()`,
      returnByValue: true
    });
    console.log('Modal check:', modalCheck.result.value);

    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
    fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/pen_clicked_test.jpg', Buffer.from(shot.data, 'base64'));
    console.log('Saved pen_clicked_test.jpg');
  }
  ws.close();
}

test().catch(console.error);
