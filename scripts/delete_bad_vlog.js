const fs = require('fs');

async function deleteBadPost() {
  const tabs = await fetch('http://127.0.0.1:9333/json/list').then(r => r.json());
  const ttTab = tabs.find(t => t.url && t.url.includes('tiktok'));
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
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 5000));

  // 1. Hover row 1 to reveal actions
  console.log('Hovering row 1...');
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 408, y: 249 });
  await new Promise(r => setTimeout(r, 800));

  // 2. Click the three dots button at (1537, 249)
  console.log('Clicking three dots at (1537, 249)...');
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 1537, y: 249, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 1537, y: 249, button: 'left', clickCount: 1 });
  await new Promise(r => setTimeout(r, 1500));

  // 3. Find Delete menu item
  const deleteItemRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const items = Array.from(document.querySelectorAll('[role=menuitem], .TUXMenuItem, li, div, span')).filter(el => {
        const t = el.innerText ? el.innerText.trim() : '';
        return t === 'Delete' || t === 'Hapus';
      });
      return items.map(el => {
        const r = el.getBoundingClientRect();
        return {
          text: el.innerText.trim(),
          x: Math.round(r.left + r.width/2),
          y: Math.round(r.top + r.height/2),
          w: Math.round(r.width),
          h: Math.round(r.height)
        };
      }).filter(i => i.w > 0 && i.h > 0);
    })()`,
    returnByValue: true
  });
  console.log('Delete items found:', deleteItemRes.result.value);

  const delItem = (deleteItemRes.result.value || [])[0];
  if (delItem) {
    console.log(`Clicking Delete option at (${delItem.x}, ${delItem.y})...`);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: delItem.x, y: delItem.y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: delItem.x, y: delItem.y, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 2000));

    // 4. Click Confirm Delete modal
    const confirmBtnRes = await send('Runtime.evaluate', {
      expression: `(() => {
        const buttons = Array.from(document.querySelectorAll('button')).filter(b => {
          const t = b.innerText.trim();
          return t === 'Delete' || t === 'Hapus' || t === 'Confirm';
        });
        return buttons.map(b => {
          const r = b.getBoundingClientRect();
          return {
            text: b.innerText.trim(),
            x: Math.round(r.left + r.width/2),
            y: Math.round(r.top + r.height/2),
            w: Math.round(r.width),
            h: Math.round(r.height)
          };
        }).filter(b => b.w > 0 && b.h > 0);
      })()`,
      returnByValue: true
    });
    console.log('Confirm delete buttons:', confirmBtnRes.result.value);

    const confirmBtn = (confirmBtnRes.result.value || [])[0];
    if (confirmBtn) {
      console.log(`Clicking Confirm Delete button at (${confirmBtn.x}, ${confirmBtn.y})...`);
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: confirmBtn.x, y: confirmBtn.y, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: confirmBtn.x, y: confirmBtn.y, button: 'left', clickCount: 1 });
      await new Promise(r => setTimeout(r, 4000));
    }
  }

  // 5. Reload to verify
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 4000));

  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/after_delete_bad_vlog.jpg', Buffer.from(shot.data, 'base64'));
  console.log('Saved after_delete_bad_vlog.jpg');
  ws.close();
}

deleteBadPost().catch(console.error);
