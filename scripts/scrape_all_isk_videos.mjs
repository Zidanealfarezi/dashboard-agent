import fs from 'fs';

async function main() {
  const tabs = await fetch("http://127.0.0.1:9333/json/list").then(r => r.json());
  const tt = tabs.find(t => t.url.includes("tiktokstudio") && t.type === "page");
  if (!tt) {
    console.error("No tiktokstudio page tab found");
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

  // Get max scroll height
  const info = await send("Runtime.evaluate", {
    expression: `
      (() => {
        const c = document.querySelector(".css-snthx");
        return c ? { scrollHeight: c.scrollHeight, clientHeight: c.clientHeight } : null;
      })()
    `,
    returnByValue: true
  });
  console.log("Container info:", info.result.value);
  const maxScroll = (info.result.value && info.result.value.scrollHeight) || 6200;

  const collectedVideos = new Map();

  for (let pos = 0; pos <= maxScroll + 500; pos += 350) {
    await send("Runtime.evaluate", {
      expression: `
        (() => {
          const container = document.querySelector(".css-snthx");
          if (container) container.scrollTop = ${pos};
        })()
      `
    });
    await new Promise(r => setTimeout(r, 400));

    const res = await send("Runtime.evaluate", {
      expression: `
        (() => {
          const container = document.querySelector(".css-snthx");
          if (!container) return "";
          return container.innerText;
        })()
      `,
      returnByValue: true
    });

    const text = res.result && res.result.value;
    if (typeof text === "string") {
      const parts = text.split(/(?=00:\d{2}\n)/);
      for (const p of parts) {
        const lines = p.trim().split("\n").map(l => l.trim()).filter(Boolean);
        if (lines.length >= 4 && /^00:\d{2}$/.test(lines[0])) {
          const key = lines[0] + "_" + (lines[1] || "").slice(0, 35);
          if (!collectedVideos.has(key)) {
            collectedVideos.set(key, {
              duration: lines[0],
              caption: lines[1],
              raw_lines: lines
            });
          }
        }
      }
    }
  }

  console.log("Total unique videos collected:", collectedVideos.size);
  const outPath = "/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46/all_virtual_videos.json";
  fs.writeFileSync(outPath, JSON.stringify(Array.from(collectedVideos.values()), null, 2));
  console.log("Saved to", outPath);

  ws.close();
}

main().catch(console.error);
