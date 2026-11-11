const fs = require('fs');

async function test() {
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
  await send('Page.navigate', { url: 'https://www.tiktok.com/@dinda.kemala_/video/7705959892703513876' });
  await new Promise(r => setTimeout(r, 4000));

  const textRes = await send('Runtime.evaluate', {
    expression: `(() => {
      const h1 = document.querySelector('h1');
      return {
        title: document.title,
        h1Text: h1 ? h1.innerText : null
      };
    })()`,
    returnByValue: true
  });
  console.log('Video page content:', textRes.result.value);

  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
  fs.writeFileSync('/Users/zidane/.gemini/antigravity/brain/542843fd-c8fe-4922-9aad-0bfcd039e339/tiktok_live_video_view.jpg', Buffer.from(shot.data, 'base64'));
  console.log('Saved screenshot: tiktok_live_video_view.jpg');
  ws.close();
}

test().catch(console.error);
