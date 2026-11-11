const fs = require('fs');
const path = require('path');

async function triggerFileInput(send) {
  // 1. Click New button
  await send('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector("[guidedhelpid='new_menu_button']");
      if (!btn) return false;
      btn.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
      btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
      btn.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
      btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
      btn.click();
      return true;
    })()`
  });

  // 2. Wait until menu appears
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 200));
    const hasMenu = await send('Runtime.evaluate', {
      expression: `Array.from(document.querySelectorAll("[role='menuitem'], .a-v-T")).some(e => e.innerText && e.innerText.includes("File upload"))`,
      returnByValue: true
    });
    if (hasMenu.result.value) break;
  }

  // 3. Click File upload item
  await send('Runtime.evaluate', {
    expression: `(() => {
      const items = Array.from(document.querySelectorAll("[role='menuitem'], .a-v-T"));
      const el = items.find(e => e.innerText && e.innerText.includes("File upload"));
      if (!el) return false;
      el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
      el.click();
      return true;
    })()`
  });

  // 4. Wait until input[type="file"] appears in DOM
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 200));
    const doc = await send('DOM.getDocument');
    const inputNode = await send('DOM.querySelector', {
      nodeId: doc.root.nodeId,
      selector: 'input[type="file"]'
    });
    if (inputNode && inputNode.nodeId > 0) {
      return inputNode.nodeId;
    }
  }
  throw new Error('input[type="file"] did not appear in DOM');
}

async function main() {
  const downloadsDir = '/Users/zidane/Downloads';
  const allEntries = fs.readdirSync(downloadsDir, { withFileTypes: true, recursive: true });
  const allFiles = [];

  for (const entry of allEntries) {
    if (entry.isFile() && !entry.name.startsWith('.')) {
      const fullPath = path.join(entry.parentPath || downloadsDir, entry.name);
      allFiles.push(fullPath);
    }
  }

  console.log(`Total files found in Downloads: ${allFiles.length}`);

  // Skip the first 26 files (test file + batch 1)
  const remainingFiles = allFiles.slice(26);
  console.log(`Remaining files to queue: ${remainingFiles.length}`);

  if (remainingFiles.length === 0) {
    console.log('All files already queued!');
    return;
  }

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
    try {
      await send('DOM.enable');
      console.log('Triggering file input for all remaining files...');
      const nodeId = await triggerFileInput(send);
      console.log('Got input nodeId:', nodeId);

      await send('DOM.setFileInputFiles', {
        files: remainingFiles,
        nodeId: nodeId
      });
      console.log(`Successfully queued ALL ${remainingFiles.length} remaining files to Google Drive!`);
      await new Promise(r => setTimeout(r, 4000));
      ws.close();
    } catch (e) {
      console.error('Error during upload:', e);
      ws.close();
    }
  };
}

main().catch(console.error);
