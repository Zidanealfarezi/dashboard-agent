/** Durable, fail-closed engagement queue. No network or browser access. */
import {DatabaseSync} from 'node:sqlite';
import {createHash, randomUUID} from 'node:crypto';
export const hash = value => createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
export function validateText(text) {
  if(typeof text!=='string'||!text.trim()||text!==text.trim()||text.length>500)throw Error('Reply must contain 1–500 trimmed characters');
  if(!/^[\p{L}\p{M}\s.,!?'’\-]+$/u.test(text))throw Error('Reply must be plain text without emoji, links, numbers or contact details');
  return text;
}
export class EngagementStore {
  constructor(path) {
    this.db=new DatabaseSync(path);this.db.exec(`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=3000;
      CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, scope TEXT NOT NULL, fingerprint TEXT NOT NULL, payload TEXT NOT NULL, disposition TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,digest TEXT NOT NULL,created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS replies(id TEXT PRIMARY KEY,batch_id TEXT NOT NULL,item_id TEXT NOT NULL UNIQUE,text TEXT NOT NULL,text_hash TEXT NOT NULL,incoming_hash TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,evidence TEXT,updated_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS checkpoints(scope TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,checked_at TEXT NOT NULL);`);
    // A process lost during submission must never silently retry on the next start.
  }
  transaction(fn){this.db.exec('BEGIN IMMEDIATE');try{const r=fn();this.db.exec('COMMIT');return r;}catch(e){this.db.exec('ROLLBACK');throw e;}}
  observe(item){
    const now=new Date().toISOString();const fingerprint=hash(item.context);
    const id=hash([item.kind,item.scope,item.external_id]);
    this.db.prepare(`INSERT INTO items VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET fingerprint=excluded.fingerprint,payload=excluded.payload,disposition=excluded.disposition,last_seen=excluded.last_seen`).run(id,item.scope,fingerprint,JSON.stringify(item),item.disposition,now,now);
    this.db.prepare('INSERT INTO checkpoints VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET fingerprint=excluded.fingerprint,checked_at=excluded.checked_at').run(item.scope,fingerprint,now);
    return {...item,id,fingerprint};
  }
  cursor(scope){return this.db.prepare('SELECT fingerprint FROM checkpoints WHERE scope=?').get(scope)?.fingerprint;}
  cursorFresh(scope,fingerprint,ttl_seconds=60){const row=this.db.prepare('SELECT fingerprint,checked_at FROM checkpoints WHERE scope=?').get(scope);return !!row&&row.fingerprint===fingerprint&&Date.now()-Date.parse(row.checked_at)<ttl_seconds*1000;}
  checkpoint(scope,fingerprint){this.db.prepare('INSERT INTO checkpoints VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET fingerprint=excluded.fingerprint,checked_at=excluded.checked_at').run(scope,fingerprint,new Date().toISOString());}
  pending(limit=5){return this.db.prepare(`SELECT i.* FROM items i LEFT JOIN replies r ON r.item_id=i.id WHERE i.disposition='pending' AND r.id IS NULL ORDER BY i.last_seen DESC LIMIT ?`).all(limit).map(r=>({...JSON.parse(r.payload),id:r.id,fingerprint:r.fingerprint}));}
  item(id){const row=this.db.prepare('SELECT * FROM items WHERE id=?').get(id);if(!row)throw Error('Unknown incoming item');return {...JSON.parse(row.payload),id:row.id,fingerprint:row.fingerprint,disposition:row.disposition};}
  prepare(replies,max=5){
    if(!Array.isArray(replies)||!replies.length||replies.length>max)throw Error('Invalid batch size');
    if(new Set(replies.map(x=>x.item_id)).size!==replies.length)throw Error('Duplicate item in batch');
    return this.transaction(()=>{
      const id=randomUUID();const now=new Date().toISOString();const plans=[];
      for(const reply of replies){
        validateText(reply.text);const item=this.item(reply.item_id);
        if(item.disposition!=='pending'||item.fingerprint!==reply.incoming_fingerprint)throw Error('Incoming message changed or is not replyable');
        if(item.is_request&&!reply.accept_request)throw Error('Explicit request acceptance is required');
        if(this.db.prepare('SELECT id FROM replies WHERE item_id=?').get(item.id))throw Error('Item already has a reply action; inspect it instead of retrying');
        const plan={id:randomUUID(),item_id:item.id,text:reply.text,text_hash:hash(reply.text),incoming_hash:item.fingerprint,accept_request:!!reply.accept_request};plans.push(plan);
      }
      const digest=hash(plans);this.db.prepare('INSERT INTO batches VALUES(?,?,?)').run(id,digest,now);
      for(const p of plans)this.db.prepare('INSERT INTO replies VALUES(?,?,?,?,?,?,?,?,?,?)').run(p.id,id,p.item_id,p.text,p.text_hash,p.incoming_hash,'prepared',0,JSON.stringify({accept_request:p.accept_request}),now);
      return {batch_id:id,digest,count:plans.length};
    });
  }
  batch(id,digest){const b=this.db.prepare('SELECT * FROM batches WHERE id=?').get(id);if(!b||b.digest!==digest)throw Error('Batch digest mismatch');return this.db.prepare('SELECT * FROM replies WHERE batch_id=? ORDER BY rowid').all(id).map(r=>({...r,item:this.item(r.item_id),metadata:JSON.parse(r.evidence||'{}')}));}
  claim(id){return this.transaction(()=>{const r=this.db.prepare('SELECT * FROM replies WHERE id=?').get(id);if(!r||r.state!=='prepared'||r.attempts!==0)throw Error('Reply is not fresh; reconcile instead of resending');const item=this.item(r.item_id);if(item.disposition!=='pending'||item.fingerprint!==r.incoming_hash||hash(r.text)!==r.text_hash)throw Error('Incoming or reply bytes changed');this.db.prepare("UPDATE replies SET state='submitting',attempts=1,updated_at=? WHERE id=?").run(new Date().toISOString(),id);return r;});}
  finish(id,state,evidence){if(!['confirmed','unknown','blocked'].includes(state))throw Error('Invalid state');const r=this.db.prepare('SELECT state FROM replies WHERE id=?').get(id);if(!r||r.state!=='submitting')throw Error('No claimed action');this.db.prepare('UPDATE replies SET state=?,evidence=?,updated_at=? WHERE id=?').run(state,JSON.stringify(evidence),new Date().toISOString(),id);}
  reconcile(id,evidence){const r=this.db.prepare('SELECT state FROM replies WHERE id=?').get(id);if(!r||!['submitting','unknown'].includes(r.state))throw Error('Only uncertain sends may be reconciled');if(evidence.confirmed!==true)return {state:r.state};this.db.prepare("UPDATE replies SET state='confirmed',evidence=?,updated_at=? WHERE id=?").run(JSON.stringify(evidence),new Date().toISOString(),id);return {state:'confirmed'};}
  status(){return {items:this.db.prepare('SELECT disposition,count(*) count FROM items GROUP BY disposition').all(),replies:this.db.prepare('SELECT state,count(*) count FROM replies GROUP BY state').all(),uncertain:this.db.prepare("SELECT id,item_id,state FROM replies WHERE state IN ('submitting','unknown')").all()};}
  close(){this.db.close();}
}
export async function commitBatch({store,driver,policy,batch_id,digest,dry_run=true}){
  if(!policy.live_sending_ready||policy.account!=='@dinda.kemala_'||policy.execution_mode!=='explicit_manual_session')throw Error('Engagement permission is not ready');
  const plans=store.batch(batch_id,digest);if(plans.length>policy.max_replies_per_run)throw Error('Batch exceeds permitted cap');
  const results=[];
  if(plans.some(p=>['unknown','submitting'].includes(p.state)))return {dry_run,batch_id,held_for_reconciliation:true,results:plans.map(p=>({id:p.id,state:p.state,skipped:true}))};
  for(const plan of plans){
    if(plan.state!=='prepared'||plan.attempts!==0){results.push({id:plan.id,state:plan.state,skipped:true});continue;}
    if(!policy[plan.item.kind==='dm'?'dm_reply_enabled':'comment_reply_enabled'])throw Error('Reply surface disabled');
    const fresh=await driver.inspect(plan.item);
    if(fresh.fingerprint!==plan.incoming_hash||fresh.disposition!=='pending')throw Error('Conversation/comment changed; rescan required');
    if(dry_run){results.push({id:plan.id,state:'prepared',dry_run:true,account_verified:true,target_verified:true});continue;}
    // Durable claim BEFORE request acceptance, typing, or clicking Send. Any ambiguity holds it.
    store.claim(plan.id);
    try{
      const evidence=await driver.send(plan.item,plan.text,plan.metadata);
      store.finish(plan.id,evidence.confirmed?'confirmed':'unknown',evidence);
      results.push({id:plan.id,state:evidence.confirmed?'confirmed':'unknown',evidence});
      if(!evidence.confirmed)break;
    }catch(error){store.finish(plan.id,'unknown',{error:error.message,no_retry:true});results.push({id:plan.id,state:'unknown',error:error.message});break;}
  }
  return {dry_run,batch_id,results};
}
