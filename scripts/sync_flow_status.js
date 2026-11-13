#!/usr/bin/env node
/**
 * sync_flow_status.js
 * Read-only CDP sync (+ optional 360p composer preset check) for Google Flow accounts.
 * Prevents 24h `balance_verified_at` expiry in app/autopilot.py without spending credits.
 *
 * Usage:
 *   node scripts/sync_flow_status.js --character all
 *   node scripts/sync_flow_status.js --character bang_ray --navigate-home --ensure-360p
 */
'use strict';

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const FLOW_CONFIG_PATH = path.join(PROJECT_ROOT, 'config', 'flow_accounts.json');
const CDP_PORTS = [9333, 9334, 9335];

function parseArgs(argv) {
  const args = {
    character: 'all',
    navigateHome: false,
    ensure360p: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--character' && argv[i + 1]) {
      args.character = argv[++i].trim().toLowerCase();
    } else if (a === '--navigate-home') {
      args.navigateHome = true;
    } else if (a === '--ensure-360p') {
      args.ensure360p = true;
    }
  }
  return args;
}

function nowWibIso() {
  const wibMs = Date.now() + 7 * 3600 * 1000;
  return new Date(wibMs).toISOString().slice(0, 19) + '+07:00';
}

function extractProjectId(projectUrl) {
  if (!projectUrl || !projectUrl.includes('/project/')) return null;
  return projectUrl.split('/project/')[1].split(/[/?#]/)[0];
}

function parseCreditsFromMenuText(menuText) {
  if (!menuText) return null;
  const m = String(menuText).match(/(\d[\d.,]*)\s*(?:Google Flow credits|kredit Google Flow)/i);
  if (!m) return null;
  const normalized = m[1].replace(/[.,]/g, '');
  const val = Number.parseInt(normalized, 10);
  return Number.isFinite(val) ? val : null;
}

async function discoverFlowTabs() {
  const all = [];
  for (const port of CDP_PORTS) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (!res.ok) continue;
      const tabs = await res.json();
      for (const t of tabs) {
        if (t.type === 'page' && t.url && t.url.includes('flow.google.com')) {
          all.push({ port, ...t });
        }
      }
    } catch (_) {
      // Port not open
    }
  }
  return all;
}

async function evalOnTab(tab, expr) {
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('WS open timeout')), 5000);
    ws.addEventListener('open', () => { clearTimeout(t); resolve(); });
    ws.addEventListener('error', (e) => { clearTimeout(t); reject(e); });
  });
  let seq = 1;
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = seq++;
    const timer = setTimeout(() => reject(new Error(`Timeout ${method}`)), 10000);
    const onMsg = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id === id) {
        clearTimeout(timer);
        ws.removeEventListener('message', onMsg);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    };
    ws.addEventListener('message', onMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
  try {
    return await expr(send);
  } finally {
    ws.close();
  }
}

async function syncOneAccount(account, tabs, options) {
  const projectId = extractProjectId(account.project_url);
  if (!projectId) {
    return { id: account.id, character: account.assigned_character, ok: false, reason: 'No project_url UUID' };
  }
  let tab = tabs.find(t => t.url && t.url.includes(projectId));
  if (!tab) {
    // Auto-Recovery Proaktif: Buka tab baru di browser otomasi via CDP
    console.log(`[Auto-Recovery] Tab Flow ${projectId} (${account.assigned_character}) belum terbuka. Membuka otomatis via CDP...`);
    for (const port of CDP_PORTS) {
      try {
        const createRes = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(account.project_url)}`, { method: 'PUT' });
        if (createRes.ok) {
          await new Promise(r => setTimeout(r, 6500));
          const freshRes = await fetch(`http://127.0.0.1:${port}/json/list`);
          if (freshRes.ok) {
            const freshTabs = await freshRes.json();
            const matched = freshTabs.find(t => t.url && t.url.includes(projectId));
            if (matched) {
              tab = { port, ...matched };
              break;
            }
          }
        }
      } catch (_) {}
    }
  }
  if (!tab) {
    return { id: account.id, character: account.assigned_character, ok: false, reason: `Flow tab ${projectId} not open and auto-open failed` };
  }

  return await evalOnTab(tab, async (send) => {
    if (options.navigateHome && (tab.url.includes('/edit/') || tab.url.includes('/scenes/'))) {
      await send('Page.navigate', { url: account.project_url });
      await new Promise(r => setTimeout(r, 3500));
    }

    const menuClick = await send('Runtime.evaluate', {
      expression: `(() => {
        const el = Array.from(document.querySelectorAll('div[role=button], button')).find(n => (n.innerText || '').includes('PRO'));
        if (!el) return { found: false };
        el.click();
        return { found: true };
      })()`,
      returnByValue: true,
    });

    let credits = null;
    let menuSnippet = '';
    if (menuClick.result?.value?.found) {
      await new Promise(r => setTimeout(r, 700));
      const readRes = await send('Runtime.evaluate', {
        expression: `(() => {
          const overlay = document.querySelector('.cdk-overlay-container');
          const text = overlay ? overlay.innerText.replace(/\\s+/g, ' ').trim() : '';
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
          const backdrop = document.querySelector('.cdk-overlay-backdrop');
          if (backdrop) backdrop.click();
          return text;
        })()`,
        returnByValue: true,
      });
      menuSnippet = readRes.result?.value || '';
      credits = parseCreditsFromMenuText(menuSnippet);
    }

    let settingsBefore = null;
    let settingsAfter = null;
    let switched360p = false;

    const trig = await send('Runtime.evaluate', {
      expression: `(() => {
        const b = document.querySelector('button[aria-label*="Settings trigger"], button[aria-label*="Pemicu setelan"]');
        return b ? b.innerText.replace(/\\s+/g, ' ').trim() : null;
      })()`,
      returnByValue: true,
    });
    settingsBefore = trig.result?.value || null;
    settingsAfter = settingsBefore;

    if (options.ensure360p && settingsBefore && !settingsBefore.includes('360p')) {
      await send('Runtime.evaluate', {
        expression: `(() => {
          const b = document.querySelector('button[aria-label*="Settings trigger"], button[aria-label*="Pemicu setelan"]');
          if (b) b.click();
        })()`,
      });
      await new Promise(r => setTimeout(r, 500));
      const pick = await send('Runtime.evaluate', {
        expression: `(() => {
          const opts = Array.from(document.querySelectorAll('button, [role=option], [role=menuitem], .mat-mdc-menu-item'));
          const opt360 = opts.find(el => /\\b360p\\b/i.test(el.innerText || '') && el.offsetParent !== null);
          if (opt360) {
            opt360.click();
            return true;
          }
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
          return false;
        })()`,
        returnByValue: true,
      });
      switched360p = Boolean(pick.result?.value);
      await new Promise(r => setTimeout(r, 400));
      const closeAndRead = await send('Runtime.evaluate', {
        expression: `(() => {
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
          const b = document.querySelector('button[aria-label*="Settings trigger"], button[aria-label*="Pemicu setelan"]');
          return b ? b.innerText.replace(/\\s+/g, ' ').trim() : null;
        })()`,
        returnByValue: true,
      });
      settingsAfter = closeAndRead.result?.value || settingsBefore;
    }

    return {
      id: account.id,
      character: account.assigned_character,
      ok: credits !== null,
      credits,
      settingsBefore,
      settingsAfter,
      switched360p,
      menuSnippet: credits === null ? menuSnippet.slice(0, 140) : undefined,
    };
  });
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const raw = fs.readFileSync(FLOW_CONFIG_PATH, 'utf-8');
  const config = JSON.parse(raw);
  const targets = config.accounts.filter((a) =>
    options.character === 'all'
      ? ['dinda', 'isk', 'bang_ray'].includes(a.assigned_character)
      : a.assigned_character === options.character
  );

  if (targets.length === 0) {
    throw new Error(`No matching Flow account for --character ${options.character}`);
  }

  const tabs = await discoverFlowTabs();
  const stamp = nowWibIso();
  const results = [];
  let updatedCount = 0;

  for (const acct of targets) {
    const res = await syncOneAccount(acct, tabs, options);
    results.push(res);
    if (res.ok && Number.isFinite(res.credits)) {
      acct.verified_balance = res.credits;
      acct.balance_verified = true;
      acct.balance_verified_at = stamp;
      acct.connected = true;
      acct.balance_source = `Sinkronisasi CDP otomatis ${stamp}: ${res.credits} kredit Google Flow (${acct.project_title || acct.id}).`;
      updatedCount += 1;
    }
  }

  if (updatedCount > 0) {
    const tmpPath = `${FLOW_CONFIG_PATH}.tmp`;
    fs.writeFileSync(tmpPath, JSON.stringify(config, null, 2) + '\n', 'utf-8');
    fs.renameSync(tmpPath, FLOW_CONFIG_PATH);
  }

  console.log(JSON.stringify({ timestamp: stamp, updated: updatedCount, results }, null, 2));
  if (results.some(r => !r.ok)) {
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error('[sync_flow_status]', err.message);
    process.exit(1);
  });
}

module.exports = { parseCreditsFromMenuText, extractProjectId };
