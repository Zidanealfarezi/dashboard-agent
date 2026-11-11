/** Read-only verification of the complete TikTok DM editor, using the installed runtime. */
import {execFileSync} from 'node:child_process';
import {McpServer, StdioServerTransport, zod, puppeteer} from '../private/chrome-connector/node_modules/chrome-devtools-mcp/build/src/third_party/index.js';
const EXPECTED_DIR = '/Users/zidane/Documents/ChatGPT/AI INFLUENCER/private/browser/dinda-automation';
const server = new McpServer({name: 'dinda-editor-guard', version: '1.0.0'});
server.registerTool('inspect_dm_draft', {
  description: 'Read the complete visible DM editor on the verified Dinda account. Use before Send; refuses a different recipient/account, ambiguous editors or an unscoped browser. Does not type or send.',
  inputSchema: {
    expected_recipient_handle: zod.string().regex(/^@[A-Za-z0-9._]+$/),
    expected_recipient_name: zod.string().min(1).max(100),
    expected_text: zod.string().max(1000),
  },
}, async (args) => inspectOrClear(args, false));
async function inspectOrClear({expected_recipient_handle: handle, expected_recipient_name: name, expected_text: expected}, clear) {
  let browser;
  try {
    const pids = [...new Set(execFileSync('/usr/sbin/lsof', ['-t', '-iTCP:9333', '-sTCP:LISTEN'], {encoding:'utf8'}).trim().split(/\s+/))];
    if (pids.length !== 1 || !/^\d+$/.test(pids[0])) throw Error('Ambiguous browser listener');
    const command = execFileSync('/bin/ps', ['-p', pids[0], '-o', 'command='], {encoding:'utf8'});
    if (!command.includes(`--user-data-dir=${EXPECTED_DIR} `) || !command.includes('--remote-debugging-address=127.0.0.1')) throw Error('Browser is not the authorized isolated instance');
    browser = await puppeteer.connect({browserURL:'http://127.0.0.1:9333', defaultViewport:null});
    const candidates = [];
    for (const page of await browser.pages()) {
      const url = new URL(page.url());
      if (url.hostname !== 'www.tiktok.com' || url.pathname.startsWith('/tiktokstudio')) continue;
      const state = await page.evaluate(({handle, name}) => {
        const own = [...document.querySelectorAll('a[href="/@dinda.kemala_"]')].some(x => x.textContent.trim() === 'Profile');
        const editors = [...document.querySelectorAll('[contenteditable="true"][aria-label="Send a message..."]')].filter(x=>x.getBoundingClientRect().width>0);
        if (!editors.length) return null;
        const editor = editors[0];
        let panel = editor.parentElement;
        while (panel && ![...panel.querySelectorAll('h2')].some(x => x.textContent.trim() === name)) panel = panel.parentElement;
        const recipient = Boolean(panel && [...panel.querySelectorAll('a[href]')].some(x => x.getAttribute('href') === '/' + handle));
        return {own_account_verified:own, recipient_verified:recipient, editor_count:editors.length, text:editor.innerText, react_blocks:editor.querySelectorAll('[data-block="true"]').length};
      }, {handle, name});
      if (state) candidates.push({state, page});
    }
    if (candidates.length !== 1) throw Error('No unique visible TikTok DM editor');
    const {state, page} = candidates[0];
    if (!state.own_account_verified || !state.recipient_verified || state.editor_count !== 1) throw Error('Account or selected recipient cannot be verified');
    if (clear) {
      const current = state.text === '\n' ? '' : state.text;
      if (current !== expected || state.react_blocks < 1) throw Error('Draft differs from expected text or editor is unhealthy; refused to clear');
      const editor = await page.$('[contenteditable="true"][aria-label="Send a message..."]');
      await page.bringToFront();
      await editor.focus();
      const session = await page.createCDPSession();
      try {
        await session.send('Input.dispatchKeyEvent', {type:'rawKeyDown', key:'a', code:'KeyA', commands:['selectAll']});
        await session.send('Input.dispatchKeyEvent', {type:'keyUp', key:'a', code:'KeyA'});
        await page.keyboard.press('Backspace');
      } finally { await session.detach(); }
      state.text = await editor.evaluate(x=>x.innerText);
      const empty = !state.text.trim();
      return {isError:!empty, content:[{type:'text', text:JSON.stringify({cleared:empty, text:empty?'':state.text, sent:false, own_account_verified:true, recipient_verified:true})}]};
    }
    const text = state.text === '\n' ? '' : state.text;
    const result = {...state, text, character_count:[...text].length, expected_character_count:[...expected].length, exact_match:text===expected, editor_healthy:state.react_blocks>0, sent:false};
    return {content:[{type:'text', text:JSON.stringify(result)}]};
  } catch (error) {
    return {isError:true, content:[{type:'text', text:JSON.stringify({verified:false, sent:false, error:error.message})}]};
  } finally {
    if (browser) await browser.disconnect();
  }
}
server.registerTool('clear_dm_draft', {
  description:'Clear only the exact known unsent DM draft, after verifying the Dinda account and selected recipient. Uses the browser selectAll editing command, not OS shortcut guessing. Never sends or deletes a message.',
  inputSchema:{expected_recipient_handle:zod.string().regex(/^@[A-Za-z0-9._]+$/), expected_recipient_name:zod.string().min(1).max(100), expected_text:zod.string().min(1).max(1000)},
}, args=>inspectOrClear(args, true));
server.registerTool('inspect_comment_reply_draft', {
  description:'Verify full text in the inline REPLY editor attached to a specific incoming comment on an owned Dinda video. Rejects the generic top-level comment editor. Read only.',
  inputSchema:{post_url:zod.string().url(), expected_comment_author:zod.string().regex(/^@[A-Za-z0-9._]+$/), expected_comment_text:zod.string().min(1).max(1000), expected_text:zod.string().max(1000)},
}, async ({post_url, expected_comment_author:author, expected_comment_text:incoming, expected_text:expected})=>{
  let browser;
  try{
    const url=new URL(post_url);
    if(url.origin!=='https://www.tiktok.com'||!/^\/@dinda\.kemala_\/video\/\d+$/.test(url.pathname))throw Error('Only owned Dinda video URLs allowed');
    const pids=[...new Set(execFileSync('/usr/sbin/lsof',['-t','-iTCP:9333','-sTCP:LISTEN'],{encoding:'utf8'}).trim().split(/\s+/))];
    if(pids.length!==1||!/^\d+$/.test(pids[0]))throw Error('Ambiguous browser listener');
    const command=execFileSync('/bin/ps',['-p',pids[0],'-o','command='],{encoding:'utf8'});
    if(!command.includes(`--user-data-dir=${EXPECTED_DIR} `)||!command.includes('--remote-debugging-address=127.0.0.1'))throw Error('Wrong browser instance');
    browser=await puppeteer.connect({browserURL:'http://127.0.0.1:9333',defaultViewport:null});
    const pages=(await browser.pages()).filter(p=>p.url().split('?')[0]===post_url);
    if(pages.length!==1)throw Error('Own video page not unique');
    const state=await pages[0].evaluate(({author,incoming,expected})=>{
      const own=[...document.querySelectorAll('a[href="/@dinda.kemala_"]')].some(x=>x.textContent.trim()==='Profile');
      const editors=[...document.querySelectorAll('[data-e2e="comment-reply-input"] [contenteditable="true"]')].filter(x=>x.getBoundingClientRect().width>0);
      if(editors.length!==1)return{own_account_verified:own,reply_mode:false,editor_count:editors.length};
      const editor=editors[0];const container=editor.closest('[class*="DivCommentObjectWrapper"]');
      const target=Boolean(container&&[...container.querySelectorAll('a[href]')].some(x=>x.getAttribute('href')==='/'+author)&&[...container.querySelectorAll('*')].some(x=>x.children.length===0&&x.textContent.trim()===incoming));
      const text=editor.innerText==='\n'?'':editor.innerText;
      return{own_account_verified:own,reply_mode:true,target_verified:target,text,character_count:[...text].length,exact_match:text===expected,editor_healthy:editor.querySelectorAll('[data-block="true"]').length>0,sent:false};
    },{author,incoming,expected});
    if(!state.own_account_verified||!state.reply_mode||!state.target_verified)throw Error('Inline reply target/account not verified');
    return{content:[{type:'text',text:JSON.stringify(state)}]};
  }catch(error){return{isError:true,content:[{type:'text',text:JSON.stringify({verified:false,sent:false,error:error.message})}]};}
  finally{if(browser)await browser.disconnect();}
});
await server.connect(new StdioServerTransport());
