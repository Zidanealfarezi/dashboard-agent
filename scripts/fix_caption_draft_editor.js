const fs = require('fs');

async function fixCaption() {
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

  const captionText = 'Pagi lur! Selamat beraktivitas di hari Senin buat wong kito galo. Supayo badan seger dan pikiran tenang jangan lupo sarapan anget dulu peh. Kalu kamu senin pagi ini lah siap begawe apo kuliah lur? Tulis di komen peh kito saling sapa! #palembang #kulinerpalembang #wongkito #wongkitogalo #seninpagi #vlogpalembang #dindakemala #sarapanpalembang';

  // 1. Focus the DraftEditor
  console.log('Focusing DraftEditor...');
  const focusRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const el = document.querySelector('.public-DraftEditor-content');
      if (!el) return { found: false };
      el.focus();
      const r = el.getBoundingClientRect();
      return { found: true, x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2), text: el.innerText };
    })()`,
    returnByValue: true
  });
  console.log('DraftEditor focus info:', focusRes.result.value);

  if (!focusRes.result.value.found) {
    throw new Error('DraftEditor not found!');
  }

  const { x, y } = focusRes.result.value;
  // Click on the text area to place cursor
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  await new Promise(r => setTimeout(r, 400));

  // 2. Select All using meta+A (Command+A on Mac)
  console.log('Selecting all text with Command+A...');
  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Meta', code: 'MetaLeft', windowsVirtualKeyCode: 91, modifiers: 8 });
  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, modifiers: 8 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, modifiers: 8 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Meta', code: 'MetaLeft', windowsVirtualKeyCode: 91, modifiers: 0 });
  await new Promise(r => setTimeout(r, 300));

  // 3. Press Backspace to delete
  console.log('Pressing Backspace...');
  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
  await new Promise(r => setTimeout(r, 400));

  // 4. Insert new caption via CDP Input.insertText
  console.log('Inserting new caption text via CDP...');
  await send('Input.insertText', { text: captionText });
  await new Promise(r => setTimeout(r, 1500));

  // 5. Check what text is inside now
  const checkText = await send('Runtime.evaluate', {
    expression: `(() => {
      const el = document.querySelector('.public-DraftEditor-content');
      return el ? el.innerText : null;
    })()`,
    returnByValue: true
  });
  console.log('DraftEditor text after insert:', checkText.result.value);

  // 6. Dismiss any hashtag dropdown popup by pressing Escape
  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await new Promise(r => setTimeout(r, 800));

  // 7. Scroll down drawer to make Save button visible and clickable
  console.log('Scrolling down drawer...');
  await send('Runtime.evaluate', {
    expression: `(() => {
      const drawer = document.querySelector('.drawer, .modal, [class*="drawer"], [class*="container"]') || window;
      if (drawer.scrollTo) drawer.scrollTo(0, 9999);
      window.scrollTo(0, 9999);
    })()`
  });
  await new Promise(r => setTimeout(r, 800));

  // 8. Find Save button
  const saveBtnRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('button')).filter(b => {
        const t = b.innerText.trim();
        return t === 'Save' || t === 'Save changes' || t === 'Save edit';
      });
      return buttons.map(b => {
        const r = b.getBoundingClientRect();
        return {
          text: b.innerText.trim(),
          disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
          x: Math.round(r.left + r.width/2),
          y: Math.round(r.top + r.height/2),
          w: Math.round(r.width),
          h: Math.round(r.height)
        };
      });
    })()`,
    returnByValue: true
  });
  console.log('Save buttons found:', saveBtnRes.result.value);

  const saveBtn = (saveBtnRes.result.value || []).find(b => !b.disabled && b.w > 0);
  if (saveBtn) {
    console.log(`Clicking Save button at (${saveBtn.x}, ${saveBtn.y})...`);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: saveBtn.x, y: saveBtn.y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: saveBtn.x, y: saveBtn.y, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 4000));
  } else {
    console.warn('Save button not found or disabled!');
  }

  // 9. Reload page and verify row 1
  console.log('Reloading content page to verify...');
  await send('Page.navigate', { url: 'https://www.tiktok.com/tiktokstudio/content' });
  await new Promise(r => setTimeout(r, 5000));

  const verifyRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const text = document.body.innerText;
      return text.split('\\n').filter(l => l.includes('Pagi lur') || l.includes('final_vlog') || l.includes('Nov 9') || l.includes('Everyone')).slice(0, 8);
    })()`,
    returnByValue: true
  });
  console.log('Verification result on refreshed table:', verifyRes.result.value);

  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_caption_fixed_proof.jpg', Buffer.from(shot.data, 'base64'));
  console.log('Screenshot saved to tiktok_caption_fixed_proof.jpg');

  ws.close();
}

fixCaption().catch(console.error);
