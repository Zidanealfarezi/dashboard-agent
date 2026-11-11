#!/usr/bin/env node
/**
 * Pinterest Outfit Crawler for Dinda Kemala (AI Influencer)
 * Autonomously searches Pinterest for high-res aesthetic modest/hijab outfit pins.
 */

import fs from 'node:fs';
import path from 'node:path';
import https from 'node:https';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Import Puppeteer from chrome-connector
const mcpPath = path.resolve(__dirname, '../private/chrome-connector/node_modules/chrome-devtools-mcp/build/src/third_party/index.js');
const { puppeteer } = await import(mcpPath);

// Default aesthetic queries matching Dinda's persona
const DINDA_OUTFIT_QUERIES = [
  'hijab ootd aesthetic minimalist',
  'modest outfit earth tone hijab casual',
  'cafe ootd hijab pastel minimalist',
  'cardigan rajut hijab aesthetic ootd',
  'kulot linen hijab style casual aesthetic',
  'korean modest hijab outfit chic',
  'sage green hijab outfit aesthetic',
  'blazer casual hijab aesthetic chic'
];

// Parse CLI args
const args = process.argv.slice(2);
let query = '';
let limit = 3;
let outDir = path.resolve(__dirname, '../characters/dinda/wardrobe/inbox');

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--query' && args[i + 1]) {
    query = args[++i];
  } else if (args[i] === '--limit' && args[i + 1]) {
    limit = parseInt(args[++i], 10);
  } else if (args[i] === '--outdir' && args[i + 1]) {
    outDir = path.resolve(args[++i]);
  }
}

if (!query) {
  // Pick random query from curated list
  query = DINDA_OUTFIT_QUERIES[Math.floor(Math.random() * DINDA_OUTFIT_QUERIES.length)];
}

console.log(`[Pinterest Crawler] Searching Pinterest for: "${query}" (Target: ${limit} pins)`);

fs.mkdirSync(outDir, { recursive: true });

async function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      if (response.statusCode === 200) {
        response.pipe(file);
        file.on('finish', () => {
          file.close(resolve);
        });
      } else {
        file.close();
        fs.unlink(dest, () => {});
        reject(new Error(`Failed to download ${url}: status ${response.statusCode}`));
      }
    }).on('error', (err) => {
      file.close();
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function run() {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--blink-settings=imagesEnabled=true'
    ]
  });

  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1280, height: 900 });

    const searchUrl = `https://www.pinterest.com/search/pins/?q=${encodeURIComponent(query)}`;
    console.log(`[Pinterest Crawler] Navigating to: ${searchUrl}`);
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 25000 });

    // Wait for pins to populate
    await new Promise((r) => setTimeout(r, 4500));

    // Extract pin image URLs
    const pinUrls = await page.evaluate(() => {
      const results = [];
      const imgElements = document.querySelectorAll('img[src*="pinimg.com"]');
      for (const img of imgElements) {
        const src = img.src;
        // Filter out small icons, avatars, banners
        if (
          src &&
          !src.includes('60x60') &&
          !src.includes('avatar') &&
          !src.includes('profile') &&
          !src.includes('75x75')
        ) {
          // Convert thumbnail to 736x high-res
          const highRes = src.replace(/\/(236x|474x)\//, '/736x/');
          const alt = img.alt || '';
          if (!results.some((r) => r.url === highRes)) {
            results.push({ url: highRes, title: alt });
          }
        }
      }
      return results;
    });

    console.log(`[Pinterest Crawler] Found ${pinUrls.length} outfit pins matching aesthetic criteria.`);

    const savedPins = [];
    const timestamp = Date.now();

    for (let i = 0; i < Math.min(limit, pinUrls.length); i++) {
      const pin = pinUrls[i];
      const filename = `pinterest_outfit_${timestamp}_${i + 1}.jpg`;
      const destPath = path.join(outDir, filename);

      try {
        console.log(`[Pinterest Crawler] Downloading Pin #${i + 1}: ${pin.url}`);
        await downloadFile(pin.url, destPath);
        savedPins.push({
          id: `pin_${timestamp}_${i + 1}`,
          query: query,
          title: pin.title,
          image_path: destPath,
          url: pin.url,
          downloaded_at: new Date().toISOString()
        });
      } catch (err) {
        console.error(`Failed to download ${pin.url}:`, err.message);
      }
    }

    const metaFile = path.join(outDir, `batch_${timestamp}.json`);
    fs.writeFileSync(metaFile, JSON.stringify(savedPins, null, 2));

    console.log(`[Pinterest Crawler] Successfully saved ${savedPins.length} outfit inspirations to: ${outDir}`);
    console.log(JSON.stringify({ status: 'success', count: savedPins.length, pins: savedPins }, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error('[Pinterest Crawler Error]:', err);
  process.exit(1);
});
