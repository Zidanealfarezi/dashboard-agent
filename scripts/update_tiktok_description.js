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
    // Find editors
    const expr = `
      (() => {
        const el = document.querySelector('[contenteditable="true"]');
        if (!el) return { found: false };
        return {
          found: true,
          className: el.className,
          text: el.innerText
        };
      })()
    `;
    const check = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
    console.log('Editor check:', check.result.value);

    // Set caption & hashtags
    const captionText = 'Weekend gini paling enak me-time sambil cari ide konten baru di cafe favorit Palembang. Suasananya adem banget! Kalau kalian lagi recharge energi tim rebahan apa tim ngopi santai? #palembang #kulinerpalembang #cafepalembang #dailyvlog #dindakemala #hijabootd';

    const updateExpr = `
      (() => {
        const el = document.querySelector('[contenteditable="true"]');
        if (!el) return false;
        el.focus();
        // Select all and replace
        document.execCommand('selectAll', false, null);
        document.execCommand('insertText', false, ${JSON.stringify(captionText)});
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return el.innerText;
      })()
    `;
    const updateRes = await send('Runtime.evaluate', { expression: updateExpr, returnByValue: true });
    console.log('Update res:', updateRes.result.value);

    // Wait 2 seconds
    await new Promise(r => setTimeout(r, 2000));

    // Inspect Post / Schedule buttons
    const buttonsExpr = `
      Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.innerText.trim(),
        disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
        className: b.className
      })).filter(b => b.text && (b.text.includes('Post') || b.text.includes('Schedule') || b.text.includes('Save') || b.text.includes('Draft')))
    `;
    const btnRes = await send('Runtime.evaluate', { expression: buttonsExpr, returnByValue: true });
    console.log('Action buttons:', btnRes.result.value);

    // Take screenshot
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
    fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_studio_with_caption.jpg', Buffer.from(shot.data, 'base64'));
    console.log('Screenshot saved to tiktok_studio_with_caption.jpg');

    ws.close();
  };
}

main().catch(console.error);
