const fs = require('fs');

async function testUpload() {
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const driveTab = tabs.find(t => t.url.includes('drive.google.com'));
  const ws = new WebSocket(driveTab.webSocketDebuggerUrl);

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
    await send('Page.enable');
    await send('DOM.enable');
    await send('Page.setInterceptFileChooserDialog', { enabled: true });

    let chooserParams = null;
    ws.addEventListener('message', async (event) => {
      const msg = JSON.parse(event.data);
      if (msg.method === 'Page.fileChooserOpened') {
        chooserParams = msg.params;
        console.log('>>> FILE CHOOSER OPENED! Mode:', msg.params.mode, 'backendNodeId:', msg.params.backendNodeId);
      }
    });

    const clickItemExpr = `
      (() => {
        const items = Array.from(document.querySelectorAll("[role='menuitem'], .a-v-T"));
        const el = items.find(e => e.innerText && e.innerText.includes("File upload"));
        if (!el) return { found: false };
        el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
        el.click();
        return { found: true, text: el.innerText };
      })()
    `;
    const res = await send('Runtime.evaluate', { expression: clickItemExpr, returnByValue: true });
    console.log('Click item res:', res.result.value);

    // Wait 3 seconds
    await new Promise(r => setTimeout(r, 3000));

    if (chooserParams) {
      console.log('Intercepted successfully! We can now call DOM.setFileInputFiles!');
    } else {
      console.log('Chooser not intercepted yet.');
    }

    ws.close();
  };
}

testUpload().catch(console.error);
