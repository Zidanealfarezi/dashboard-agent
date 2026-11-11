/** High-level Hermes tools; browser actions execute in code, never model-generated JS. */
import {McpServer,StdioServerTransport,zod} from '../private/chrome-connector/node_modules/chrome-devtools-mcp/build/src/third_party/index.js';
import {operate} from '../app/tiktok_adapter.mjs';
import {readFileSync} from 'node:fs';
if(process.argv[2]==='--operation'){
  try{const operation=process.argv[3];const args=process.argv[4]?JSON.parse(readFileSync(process.argv[4],'utf8')):{};console.log(JSON.stringify(await operate(operation,args),null,2));}
  catch(e){console.error(JSON.stringify({error:e.message,sent:false}));process.exitCode=1;}
}else{
 const server=new McpServer({name:'dinda-tiktok-adapter',version:'1.0.0'});
 let queue=Promise.resolve();
 const register=(name,description,inputSchema,operation)=>server.registerTool(name,{description,inputSchema},args=>{
   const next=queue.then(async()=>{try{return {content:[{type:'text',text:JSON.stringify(await operate(operation,args))}]};}catch(e){return {isError:true,content:[{type:'text',text:JSON.stringify({error:e.message,no_automatic_retry:true})}]};}});queue=next.catch(()=>{});return next;
 });
 register('scan_engagement','Read verified Dinda inbox/requests and comments on specified OWN open video tabs. Return only new unanswered text and compact context. No sends or accepts.',{limit:zod.number().int().min(1).max(5).default(5),post_urls:zod.array(zod.string().url()).max(3).default([]),include_requests:zod.boolean().default(true),include_comments:zod.boolean().default(true),force:zod.boolean().default(false)},'scan');
 register('prepare_replies','Persist a batch of AI-written plain text replies bound to incoming fingerprints. No browser/send. Returns immutable batch ID and digest. Escalate sensitive requests instead of drafting a commitment.',{replies:zod.array(zod.object({item_id:zod.string(),incoming_fingerprint:zod.string(),text:zod.string(),accept_request:zod.boolean().default(false)})).min(1).max(5)},'prepare');
 register('commit_replies','Recheck account, selected recipient/thread, incoming context, full editor text, duplicate state and permission, then click exactly once per item. Defaults to dry_run; dry_run=false actually sends. Uncertain outcomes are held, never retried.',{batch_id:zod.string(),digest:zod.string(),dry_run:zod.boolean().default(true)},'commit');
 register('reconcile_replies','Read-only inspection of uncertain send results. Never resends.',{batch_id:zod.string(),digest:zod.string()},'reconcile');
 register('engagement_status','Read local queue and uncertain actions without contacting the browser.',{},'status');
 await server.connect(new StdioServerTransport());
}
