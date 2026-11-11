import {readFileSync,openSync,closeSync,unlinkSync,writeFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {EngagementStore,commitBatch} from './tiktok_store.mjs';
import {TikTokBrowser} from './tiktok_browser.mjs';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export async function operate(operation,args={},options={}){
  const policy=JSON.parse(readFileSync(path.join(ROOT,'config/engagement.json'),'utf8'));
  if(policy.account!=='@dinda.kemala_'||!policy.navigation_enabled)throw Error('Dinda engagement not authorized');
  const lock=path.join(ROOT,'operations/tiktok-adapter.lock');let fd;
  try{fd=openSync(lock,'wx',0o600);writeFileSync(fd,String(process.pid));}
  catch(error){if(error.code!=='EEXIST')throw error;throw Error('Another adapter operation or stale lock exists; inspect before continuing');}
  let store,driver;
  try{
    store=new EngagementStore(options.db_path||path.join(ROOT,'operations/tiktok-engagement.sqlite'));
    if(operation==='status')return {...store.status(),account:policy.account,execution_mode:policy.execution_mode,scheduler_enabled:false};
    if(operation==='prepare')return store.prepare(args.replies,policy.max_replies_per_run);
    driver=await (options.driver_factory?options.driver_factory(policy):new TikTokBrowser(policy)).connect();
    if(operation==='scan'){const started=performance.now();const result=await driver.scan(store,args);return {account:policy.account,execution_mode:policy.execution_mode,duration_ms:Math.round(performance.now()-started),...result,uncertain:store.status().uncertain,sent:false};}
    if(operation==='commit')return await commitBatch({store,driver,policy,...args,dry_run:args.dry_run!==false});
    if(operation==='reconcile'){
      const plans=store.batch(args.batch_id,args.digest);const results=[];
      for(const plan of plans){if(!['unknown','submitting'].includes(plan.state)){results.push({id:plan.id,state:plan.state});continue;}
        // Opening the exact target is allowed; reconciliation never accepts/inputs/sends.
        try{await driver.inspect(plan.item);const evidence=await driver.evidence(plan.item,plan.text);results.push({id:plan.id,...store.reconcile(plan.id,evidence)});}catch(e){results.push({id:plan.id,state:plan.state,error:e.message});}}
      return {results,no_send:true};
    }
    if(operation==='probe'){
      const item=await driver.chooseConversation(await driver.messages(),args.recipient_name);
      if(item.blocked||item.handle!==args.recipient_handle||item.is_request)throw Error('Probe recipient not verified or not accepted');
      const text='Halo kak makasih sudah menyapa';const ctx=await driver.typeOnce(item,text);
      await driver.clearKnown(ctx,text);return {account:policy.account,recipient:item.handle,exact_text_verified:true,empty_after_clear:true,sent:false};
    }
    throw Error('Unknown adapter operation');
  }finally{try{if(driver)await driver.close();}finally{if(store)store.close();closeSync(fd);if(existsSync(lock)&&readFileSync(lock,'utf8')===String(process.pid))unlinkSync(lock);}}
}
