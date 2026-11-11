/** TikTok UI operations, fixed selectors only. No private APIs, cookies, downloads or Google tabs. */
import {execFileSync} from 'node:child_process';
import {puppeteer} from '../private/chrome-connector/node_modules/chrome-devtools-mcp/build/src/third_party/index.js';
import {hash} from './tiktok_store.mjs';
import {fileURLToPath} from 'node:url';
const AUTHORIZED_DIR=fileURLToPath(new URL('../private/browser/dinda-automation',import.meta.url));
const OWN='/@dinda.kemala_';
const visible=async el=>el.evaluate(x=>x.getBoundingClientRect().width>0&&x.getBoundingClientRect().height>0);
export class TikTokBrowser {
  constructor(policy){this.policy=policy;this.browser=null;this.createdPages=[];}
  async connect(){
    if(this.policy.browser_endpoint!=='http://127.0.0.1:9333'||this.policy.browser_user_data_dir!==AUTHORIZED_DIR)throw Error('Unexpected endpoint or browser directory');
    const pids=[...new Set(execFileSync('/usr/sbin/lsof',['-t','-iTCP:9333','-sTCP:LISTEN'],{encoding:'utf8'}).trim().split(/\s+/))];
    if(pids.length!==1||!/^\d+$/.test(pids[0]))throw Error('Ambiguous browser listener');
    const args=execFileSync('/bin/ps',['-p',pids[0],'-o','command='],{encoding:'utf8'});
    if(!args.includes(`--user-data-dir=${this.policy.browser_user_data_dir} `)||!args.includes('--remote-debugging-address=127.0.0.1'))throw Error('Authorized dedicated browser not found');
    this.browser=await puppeteer.connect({browserURL:this.policy.browser_endpoint,defaultViewport:null,handleDevToolsAsPage:true});
    return this;
  }
  async readyTargets(predicate){
    for(let attempt=0;attempt<40;attempt++){const targets=this.browser.targets().filter(t=>t.type()==='page'&&predicate(t.url()));if(targets.length&&targets.every(t=>t._session()?.parentSession()))return Promise.all(targets.map(t=>t.page()));await new Promise(resolve=>setTimeout(resolve,50));}
    throw Error('TikTok tab attachment did not become ready; no UI action performed');
  }
  async close(){if(this.browser){try{for(const page of this.createdPages)if(!page.isClosed())await page.close();}finally{await this.browser.disconnect();}}}
  async verify(page){
    const u=new URL(page.url());if(u.hostname!=='www.tiktok.com'||u.pathname.startsWith('/tiktokstudio'))throw Error('Only normal TikTok pages allowed');
    const verified=await page.evaluate(own=>[...document.querySelectorAll('a[href]')].some(x=>x.getAttribute('href')===own&&x.textContent.trim()==='Profile'),OWN);
    if(!verified)throw Error('Logged-in TikTok account is not verified as Dinda');
  }
  async profilePage(){
    const preferred=this.browser.targets().some(t=>t.type()==='page'&&t.url().split('?')[0]==='https://www.tiktok.com'+OWN)?'https://www.tiktok.com'+OWN:'https://www.tiktok.com/';
    const pages=await this.readyTargets(url=>url.split('?')[0]===preferred);
    if(pages.length!==1)throw Error('Keep one operational TikTok home or Dinda profile tab open');
    await this.verify(pages[0]);return pages[0];
  }
  async clickUnique(page,selector){const all=await page.$$(selector);const candidates=[];for(const e of all)if(await visible(e))candidates.push(e);if(candidates.length!==1)throw Error('Control missing or ambiguous: '+selector);await candidates[0].click();}
  async messages(){
    const page=await this.profilePage();await page.bringToFront();
    if(!await page.$('[data-e2e="dm-new-conversation-list"]')){await this.clickUnique(page,'[data-e2e="nav-messages"]');await page.waitForSelector('[data-e2e="dm-new-conversation-list"]',{timeout:10000});}
    return page;
  }
  async chooseConversation(page,name,isRequest=false){
    await this.verify(page);
    // Requests are opened only through their own fixed UI label, never a message link.
    if(isRequest){
      const nodes=await page.$$('button,[role="button"],div');const matches=[];
      for(const n of nodes)if(await n.evaluate(x=>x.children.length===0&&x.textContent.trim()==='Message requests')&&await visible(n))matches.push(n);
      if(matches.length!==1)throw Error('Message requests control unavailable or ambiguous');await matches[0].click();
    }
    const rows=await page.$$('[data-e2e="dm-new-conversation-item"]');const matches=[];
    for(const row of rows)if(await row.evaluate((x,name)=>x.querySelector('[data-e2e="dm-new-conversation-nickname"]')?.textContent.trim()===name,name)&&await visible(row))matches.push(row);
    if(matches.length!==1)throw Error('Conversation name missing or ambiguous');const nickname=await matches[0].$('[data-e2e="dm-new-conversation-nickname"]');await nickname.evaluate(x=>x.click());
    await page.waitForFunction(name=>document.querySelector('[data-e2e="dm-new-chat-nickname"]')?.textContent.trim()===name,{timeout:10000},name);
    return this.readConversation(page,name,isRequest);
  }
  async readConversation(page,name,isRequest){
    await this.verify(page);
    const data=await page.evaluate(({name,isRequest})=>{
      const heading=document.querySelector('[data-e2e="dm-new-chat-nickname"]')?.textContent.trim();if(heading!==name)throw Error('Selected conversation changed');
      const rows=[...document.querySelectorAll('[data-e2e="dm-new-message-list"] [data-e2e="dm-new-chat-item"]')].map(x=>{
        const sender=x.querySelector('[data-e2e="chat-avatar"]')?.closest('a')?.getAttribute('href')||null;
        const actions=x.querySelector('[data-area="Actions"]');const direction=actions?getComputedStyle(actions).flexDirection:null;
        return {id:x.parentElement.getAttribute('data-index'),sender,direction,text:x.querySelector('[data-e2e="dm-new-message-text"]')?.innerText||'',unsupported:x.innerText.includes('isn’t supported')||x.innerText.includes("isn't supported")};
      });
      const handles=[...new Set(rows.map(x=>x.sender).filter(x=>/^\/@[A-Za-z0-9._]+$/.test(x||'')&&x!=='/@dinda.kemala_'))];
      if(handles.length!==1)return {name,is_request:isRequest,blocked:'Recipient identity unavailable'};
      const handle=handles[0].slice(1);for(const row of rows)if(!row.sender&&row.direction==='row')row.sender='/'+handle;const incoming=rows.filter(x=>x.sender==='/'+handle&&x.direction==='row').at(-1);const last=rows.at(-1);
      if(!incoming||!incoming.id||!incoming.text||incoming.unsupported)return {name,handle,is_request:isRequest,blocked:'No supported incoming text with stable ID'};
      return {name,handle,is_request:isRequest,external_id:incoming.id,text:incoming.text,context:rows.slice(-8),last_incoming:last?.id===incoming.id};
    },{name,isRequest});
    if(data.blocked)return {blocked:true,reason:data.blocked,name};
    return {kind:'dm',scope:'dm:'+data.handle,...data,disposition:data.last_incoming?'pending':'already_replied'};
  }
  async scan(store,{limit=5,post_urls=[],include_requests=true,include_comments=true,force=false}={}){
    const observations=[];const skipped=[];const blocked=[];const page=await this.messages();
    const previews=await page.$$eval('[data-e2e="dm-new-conversation-item"]',nodes=>nodes.filter(x=>x.getBoundingClientRect().width>0).map(x=>({name:x.querySelector('[data-e2e="dm-new-conversation-nickname"]')?.textContent.trim(),preview:x.innerText})).filter(x=>x.name));
    for(const row of previews.slice(0,limit)){
      const key='preview:dm:'+row.name;const signature=hash(row.preview);
      if(!force&&store.cursorFresh(key,signature)){skipped.push(row.name);continue;}
      try{const item=await this.chooseConversation(page,row.name);if(item.blocked){blocked.push(item);store.checkpoint(key,signature);continue;}observations.push(store.observe(item));store.checkpoint(key,signature);}catch(e){blocked.push({name:row.name,reason:e.message});}
    }
    if(include_requests){
      // Inspect the requests folder if its exact label exists; do not accept during scan.
      const labels=await page.$$eval('div',nodes=>nodes.filter(x=>x.children.length===0&&x.textContent.trim()==='Message requests'&&x.getBoundingClientRect().width>0).length);
      if(labels===1){
        const leaves=await page.$$('div');for(const node of leaves){if(await node.evaluate(x=>x.children.length===0&&x.textContent.trim()==='Message requests')&&await visible(node)){await node.click();break;}}
        const requests=await page.$$eval('[data-e2e="dm-new-conversation-item"]',nodes=>nodes.filter(x=>x.getBoundingClientRect().width>0).map(x=>x.querySelector('[data-e2e="dm-new-conversation-nickname"]')?.textContent.trim()).filter(Boolean));
        for(const name of requests.slice(0,limit)){try{const item=await this.chooseConversation(page,name,false);item.is_request=true;if(item.blocked)blocked.push(item);else observations.push(store.observe(item));}catch(e){blocked.push({name,reason:e.message});}}
      }
    }
    const targets=include_comments?(post_urls.length?post_urls:await this.ownedPosts()):[];
    for(const url of targets.slice(0,3)){
      try{const comments=await this.comments(url);for(const item of comments)observations.push(store.observe(item));}catch(e){blocked.push({post_url:url,reason:e.message});}
    }
    return {observed:observations.length,unchanged:skipped.length,blocked,pending:store.pending(limit).map(({id,fingerprint,kind,scope,name,handle,text,is_request,post_url,context})=>({id,incoming_fingerprint:fingerprint,kind,scope,name,handle,text,is_request:!!is_request,post_url,context:Array.isArray(context)?context.slice(-4).map(x=>({sender:x.sender,text:x.text.slice(0,600)})):undefined}))};
  }
  async newOwnedPage(url){
    await this.profilePage();
    const page=await this.browser.newPage();this.createdPages.push(page);
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});
    await page.waitForFunction(own=>[...document.querySelectorAll('a[href]')].some(x=>x.getAttribute('href')===own&&x.textContent.trim()==='Profile'),{timeout:10000},OWN);
    await this.verify(page);return page;
  }
  async ownedPosts(){
    const url='https://www.tiktok.com'+OWN;
    const existing=this.browser.targets().filter(t=>t.type()==='page'&&t.url().split('?')[0]===url);
    const page=existing.length?(await this.readyTargets(value=>value.split('?')[0]===url))[0]:await this.newOwnedPage(url);
    await page.waitForSelector('a[href*="/@dinda.kemala_/video/"]',{timeout:10000}).catch(()=>{});
    return page.$$eval('a[href]',nodes=>[...new Set(nodes.map(x=>new URL(x.getAttribute('href'),location.origin).href).filter(x=>/^https:\/\/www\.tiktok\.com\/@dinda\.kemala_\/video\/\d+$/.test(x)))].slice(0,3));
  }
  async videoPage(url){
    if(!/^https:\/\/www\.tiktok\.com\/@dinda\.kemala_\/video\/\d+$/.test(url))throw Error('Only own Dinda video URLs are allowed');
    const found=this.browser.targets().filter(t=>t.type()==='page'&&t.url().split('?')[0]===url);
    const pages=found.length?await this.readyTargets(value=>value.split('?')[0]===url):[await this.newOwnedPage(url)];
    if(pages.length!==1)throw Error('Target video tab is ambiguous');
    const page=pages[0];await this.verify(page);await page.bringToFront();
    if(!await page.$('[data-e2e="comment-level-1"],[data-e2e="comment-input"]')){await page.waitForSelector('[data-e2e="comment-icon"]',{timeout:5000});const buttons=await page.$$('[data-e2e="comment-icon"]');if(!buttons.length)throw Error('Comments control unavailable');const count=await buttons[0].evaluate(x=>x.querySelector('[data-e2e="comment-count"]')?.textContent.trim()||x.textContent.trim());if(count==='0')return page;await buttons[0].evaluate(x=>x.click());await page.waitForSelector('[data-e2e="comment-level-1"],[data-e2e="comment-input"]',{timeout:10000});}
    return page;
  }
  async comments(url){
    const page=await this.videoPage(url);
    const rows=await page.$$eval('[data-e2e="comment-level-1"]',(nodes)=>nodes.map(x=>{
      const container=x.closest('[class*="DivCommentObjectWrapper"]');if(!container)return null;
      const link=container.querySelector('[data-e2e="comment-username-1"] a[href]')||container.querySelector('a[href^="/@"]');
      const handle=link?.getAttribute('href')?.slice(1);const text=x.innerText;
      const replied=[...container.querySelectorAll('[data-e2e="comment-username-2"]')].some(x=>[...x.querySelectorAll('a[href]')].some(a=>a.getAttribute('href')==='/@dinda.kemala_'));
      const hiddenReplies=[...container.querySelectorAll('button,[role="button"],span,p')].some(n=>/^(View|See|Hide).*(repl)/i.test(n.textContent.trim()));
      return {handle,text,replied,hiddenReplies};
    }).filter(Boolean));
    return rows.filter(x=>x.handle&&x.handle!=='@dinda.kemala_').map(row=>({kind:'comment',scope:url,post_url:url,external_id:hash([row.handle,row.text]),handle:row.handle,text:row.text,context:row,disposition:rows.filter(x=>x.handle===row.handle&&x.text===row.text).length!==1?'ambiguous':row.replied?'already_replied':row.hiddenReplies?'needs_thread_inspection':'pending'}));
  }
  async inspect(item){
    const fresh=item.kind==='dm'?await this.chooseConversation(await this.messages(),item.name,item.is_request):(await this.comments(item.post_url)).find(x=>x.external_id===item.external_id);
    if(!fresh||fresh.blocked||fresh.external_id!==item.external_id||fresh.handle!==item.handle)throw Error('Incoming target no longer uniquely identified');
    return {...fresh,fingerprint:hash(fresh.context)};
  }
  async editorFor(item){
    if(item.kind==='dm'){
      const page=await this.profilePage();const editors=await page.$$('[data-e2e="dm-new-input-editor"] [contenteditable="true"]');
      if(editors.length!==1)throw Error('No unique DM editor');return {page,editor:editors[0],sendSelector:'[data-e2e="dm-new-chat-bottom"] [data-e2e="dm-new-send-btn"]'};
    }
    const page=await this.videoPage(item.post_url);const handles=await page.$$('[data-e2e="comment-level-1"]');const candidates=[];
    for(const h of handles)if(await h.evaluate((x,{handle,text})=>x.innerText===text&&[...x.closest('[class*="DivCommentObjectWrapper"]').querySelectorAll('a[href]')].some(a=>a.getAttribute('href')==='/'+handle),item))candidates.push(h);
    if(candidates.length!==1)throw Error('Comment target ambiguous');
    const container=await candidates[0].evaluateHandle(x=>x.closest('[class*="DivCommentObjectWrapper"]'));
    if(!await container.$('[data-e2e="comment-reply-input"]')){const reply=await container.$('[data-e2e="comment-reply-1"]');if(!reply)throw Error('Inline reply control unavailable');await reply.click();}
    const editor=await container.$('[data-e2e="comment-reply-input"] [contenteditable="true"]');if(!editor)throw Error('Inline editor unavailable');
    return {page,editor,container,sendSelector:'[data-e2e="comment-reply-post"]'};
  }
  async checkEditor(editor,expected){const r=await editor.evaluate(x=>({text:x.innerText==='\n'?'':x.innerText,healthy:x.querySelectorAll('[data-block="true"]').length>0}));if(!r.healthy||r.text!==expected)throw Error('Full editor text mismatch or unhealthy editor');return r;}
  async typeOnce(item,text){const ctx=await this.editorFor(item);await this.verify(ctx.page);await this.checkEditor(ctx.editor,'');await ctx.page.bringToFront();await ctx.editor.focus();await ctx.page.keyboard.type(text,{delay:12});await this.checkEditor(ctx.editor,text);return ctx;}
  async clearKnown(ctx,text){await this.checkEditor(ctx.editor,text);const cdp=await ctx.page.createCDPSession();try{await ctx.editor.focus();await cdp.send('Input.dispatchKeyEvent',{type:'rawKeyDown',key:'a',code:'KeyA',commands:['selectAll']});await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA'});await ctx.page.keyboard.press('Backspace');}finally{await cdp.detach();}await this.checkEditor(ctx.editor,'');}
  async send(item,text,metadata){
    if(item.is_request){if(!metadata.accept_request)throw Error('Request acceptance not authorized');const page=await this.profilePage();const buttons=await page.$$('button');const matches=[];for(const b of buttons)if(await b.evaluate(x=>x.textContent.trim()==='Accept')&&await visible(b))matches.push(b);if(matches.length!==1)throw Error('Request accept control ambiguous');await matches[0].click();}
    const before=await this.evidence(item,text);if(before.confirmed)throw Error('Matching outgoing reply already exists');
    const ctx=await this.typeOnce(item,text);await this.verify(ctx.page);
    const fresh= item.kind==='dm'?await this.readConversation(ctx.page,item.name,false):(await this.comments(item.post_url)).find(x=>x.external_id===item.external_id);
    if(!fresh||hash(fresh.context)!==hash(item.context)||fresh.disposition!=='pending')throw Error('Incoming context changed before send');
    await this.checkEditor(ctx.editor,text);
    const button=await (ctx.container||ctx.page).$(ctx.sendSelector);
    if(!button||!await visible(button)||await button.evaluate(x=>x.disabled||x.getAttribute('aria-disabled')==='true'))throw Error('Send control unavailable; nothing clicked');
    await button.click(); // The only submit action. Never Enter or retry.
    try{await ctx.page.waitForFunction(({kind,text})=>kind==='dm'?[...document.querySelectorAll('[data-e2e="dm-new-chat-item"]')].some(x=>x.querySelector('[data-area="Actions"]')&&getComputedStyle(x.querySelector('[data-area="Actions"]')).flexDirection==='row-reverse'&&x.querySelector('[data-e2e="dm-new-message-text"]')?.innerText===text):[...document.querySelectorAll('[data-e2e="comment-level-2"]')].some(x=>x.innerText===text),{timeout:10000},{kind:item.kind,text});}catch{}
    return this.evidence(item,text);
  }
  async evidence(item,text){
    if(item.kind==='dm'){
      const page=await this.profilePage();await this.verify(page);
      return page.evaluate(({text,name,handle})=>{
        const current=document.querySelector('[data-e2e="dm-new-chat-nickname"]')?.textContent.trim();
        const rows=[...document.querySelectorAll('[data-e2e="dm-new-message-list"] [data-e2e="dm-new-chat-item"]')];
        const recipient=rows.some(x=>x.querySelector('[data-e2e="chat-avatar"]')?.closest('a')?.getAttribute('href')==='/'+handle);
        const last=rows.at(-1);const action=last?.querySelector('[data-area="Actions"]');const outgoing=last&&action&&getComputedStyle(action).flexDirection==='row-reverse'&&last.querySelector('[data-e2e="dm-new-message-text"]')?.innerText===text;
        const failed=last&&/failed|couldn.t send|not sent/i.test(last.querySelector('[data-e2e="dm-warning"]')?.innerText||'');
        return {confirmed:!!(current===name&&recipient&&outgoing&&!failed),message_id:outgoing?last.parentElement.getAttribute('data-index'):null,account:'@dinda.kemala_',recipient:handle};
      },{text,name:item.name,handle:item.handle});
    }
    const page=await this.videoPage(item.post_url);return page.evaluate(({handle,incoming,text})=>{
      const parents=[...document.querySelectorAll('[data-e2e="comment-level-1"]')].filter(x=>x.innerText===incoming).map(x=>x.closest('[class*="DivCommentObjectWrapper"]')).filter(c=>c&&[...c.querySelectorAll('a[href]')].some(a=>a.getAttribute('href')==='/'+handle));
      if(parents.length!==1)return{confirmed:false};const c=parents[0];const confirmed=[...c.querySelectorAll('[data-e2e="comment-level-2"]')].some(x=>x.innerText===text&&[...x.parentElement.parentElement.querySelectorAll('a[href]')].some(a=>a.getAttribute('href')==='/@dinda.kemala_'));
      return{confirmed,threading_confirmed:confirmed,account:'@dinda.kemala_',target_author:handle};
    },{handle:item.handle,incoming:item.text,text});
  }
}
