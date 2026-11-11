import fs from 'fs';

async function main() {
  const tabs = await fetch("http://127.0.0.1:9333/json/list").then(r => r.json());
  const tt = tabs.find(t => t.url.includes("tiktokstudio") && t.type === "page");
  if (!tt) {
    console.error("No tiktokstudio tab found");
    process.exit(1);
  }

  const ws = new WebSocket(tt.webSocketDebuggerUrl);

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = Math.floor(Math.random() * 1000000);
      const timeout = setTimeout(() => {
        ws.removeEventListener("message", handler);
        reject(new Error(`Timeout waiting for CDP ${method}`));
      }, 30000);
      const handler = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === id) {
          clearTimeout(timeout);
          ws.removeEventListener("message", handler);
          if (msg.error) reject(new Error(JSON.stringify(msg.error)));
          else resolve(msg.result);
        }
      };
      ws.addEventListener("message", handler);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await new Promise(r => ws.onopen = r);
  console.log("Connected to TikTok Studio CDP");

  // Reset scroll to top
  await send("Runtime.evaluate", {
    expression: `
      (() => {
        const c = document.querySelector(".css-snthx");
        if (c) c.scrollTop = 0;
      })()
    `
  });
  await new Promise(r => setTimeout(r, 1000));

  const allRawChunks = [];

  // Scroll systematically in 50 steps
  for (let step = 0; step <= 55; step++) {
    const res = await send("Runtime.evaluate", {
      expression: `
        (() => {
          const c = document.querySelector(".css-snthx");
          if (!c) return { text: "", scrollTop: 0, scrollHeight: 0 };
          const t = c.innerText;
          c.scrollTop += 220;
          return { text: t, scrollTop: c.scrollTop, scrollHeight: c.scrollHeight };
        })()
      `,
      returnByValue: true
    });

    if (res.result && res.result.value && res.result.value.text) {
      allRawChunks.push(res.result.value.text);
    }
    await new Promise(r => setTimeout(r, 350));
  }

  console.log("Collected raw chunks count:", allRawChunks.length);
  const outPath = "/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46/raw_scraped_chunks.json";
  fs.writeFileSync(outPath, JSON.stringify(allRawChunks, null, 2));
  console.log("Saved raw chunks to", outPath);

  ws.close();
}

main().catch(console.error);
