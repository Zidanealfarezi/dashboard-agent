import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { randomBytes, timingSafeEqual } from 'node:crypto';

const db = new DatabaseSync(process.env.EXAM_DB || 'exam.db');
const assets = new Map([['/', ['index.html','text/html']], ['/app.js',['app.js','text/javascript']], ['/style.css',['style.css','text/css']]].map(([path,[file,type]])=>[path,[readFileSync(new URL('./public/'+file,import.meta.url)),type]]));
db.exec(`PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, role TEXT NOT NULL, code TEXT UNIQUE NOT NULL, pin TEXT NOT NULL, name TEXT NOT NULL, class_name TEXT);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, prompt TEXT NOT NULL, options TEXT NOT NULL, answer INTEGER NOT NULL, explanation TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY, title TEXT NOT NULL, starts INTEGER NOT NULL, ends INTEGER NOT NULL, released INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS exam_questions(exam_id INTEGER REFERENCES exams(id), position INTEGER NOT NULL, prompt TEXT NOT NULL, options TEXT NOT NULL, answer INTEGER NOT NULL, explanation TEXT NOT NULL, PRIMARY KEY(exam_id,position));
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id), user_id INTEGER NOT NULL REFERENCES users(id), submitted INTEGER NOT NULL DEFAULT 0, submitted_at INTEGER, UNIQUE(exam_id,user_id));
CREATE TABLE IF NOT EXISTS answers(attempt_id INTEGER REFERENCES attempts(id), position INTEGER NOT NULL, choice INTEGER NOT NULL, updated INTEGER NOT NULL, PRIMARY KEY(attempt_id,position));`);
const get = db.prepare('SELECT * FROM users WHERE code=?');
if (!get.get('SISWA01')) {
  db.prepare('INSERT INTO users(role,code,pin,name,class_name) VALUES(?,?,?,?,?)').run('student','SISWA01','1234','Alya Demo','8A');
  db.prepare('INSERT INTO users(role,code,pin,name) VALUES(?,?,?,?)').run('teacher','GURU01','1234','Bu Rina Demo');
  const items = [
    ['Hasil dari 3/4 + 2/3 adalah ...',['17/12','5/7','6/7','13/12'],0,'Samakan penyebut menjadi 12: 9/12 + 8/12 = 17/12.'],
    ['Jika 5x = 35, nilai x adalah ...',['5','6','7','8'],2,'Bagi kedua sisi dengan 5.'],
    ['Luas persegi panjang dengan panjang 12 cm dan lebar 5 cm adalah ...',['17 cm²','34 cm²','60 cm²','120 cm²'],2,'Luas = panjang × lebar.'],
    ['Keliling persegi dengan sisi 9 cm adalah ...',['18 cm','27 cm','36 cm','81 cm'],2,'Keliling persegi = 4 × sisi.'],
    ['Rata-rata dari 6, 8, 10, dan 12 adalah ...',['8','9','10','36'],1,'Jumlah 36 dibagi 4 sama dengan 9.'],
    ['Perbandingan 15 : 25 dalam bentuk paling sederhana adalah ...',['3 : 5','5 : 3','15 : 5','2 : 5'],0,'Bagi kedua bilangan dengan 5.'],
    ['Sebuah segitiga bersudut 50° dan 60°. Sudut ketiganya ...',['60°','70°','80°','90°'],1,'Jumlah sudut segitiga 180°.'],
    ['Bentuk desimal dari 3/5 adalah ...',['0,3','0,5','0,6','0,8'],2,'3 dibagi 5 sama dengan 0,6.'],
    ['-7 + 12 = ...',['-19','-5','5','19'],2,'Bergerak 12 satuan ke kanan dari -7.'],
    ['Volume kubus dengan rusuk 4 cm adalah ...',['16 cm³','32 cm³','48 cm³','64 cm³'],3,'Volume = rusuk³ = 4 × 4 × 4.'],
    ['Jika y - 9 = 4, nilai y adalah ...',['5','9','13','36'],2,'Tambahkan 9 pada kedua sisi.'],
    ['25% dari 200 adalah ...',['25','40','50','75'],2,'25% = 1/4; seperempat dari 200 adalah 50.'],
    ['FPB dari 18 dan 24 adalah ...',['3','6','9','12'],1,'Faktor persekutuan terbesar adalah 6.'],
    ['KPK dari 4 dan 6 adalah ...',['8','10','12','24'],2,'Kelipatan persekutuan terkecilnya 12.'],
    ['Jarak 120 km ditempuh dalam 3 jam. Kecepatan rata-ratanya ...',['30 km/jam','40 km/jam','60 km/jam','360 km/jam'],1,'Kecepatan = jarak ÷ waktu.'],
    ['Koordinat titik yang berada di sumbu-x adalah ...',['(0, 4)','(3, 0)','(2, 2)','(-1, 5)'],1,'Di sumbu-x, koordinat y bernilai 0.'],
    ['Luas lingkaran berjari-jari 7 cm (π = 22/7) adalah ...',['44 cm²','88 cm²','154 cm²','308 cm²'],2,'Luas = πr² = 22/7 × 49 = 154.'],
    ['Peluang muncul angka genap saat melempar dadu adalah ...',['1/6','1/3','1/2','2/3'],2,'Ada 3 hasil genap dari 6 kemungkinan.'],
    ['Suku berikutnya dari 2, 5, 8, 11, ... adalah ...',['12','13','14','15'],2,'Pola bertambah 3.'],
    ['Bentuk sederhana dari 2(a + 3) adalah ...',['2a + 3','2a + 5','2a + 6','a + 6'],2,'Kalikan 2 ke setiap suku di dalam kurung.']
  ];
  const ins=db.prepare('INSERT INTO questions(prompt,options,answer,explanation) VALUES(?,?,?,?)');
  for(const q of items) ins.run(q[0],JSON.stringify(q[1]),q[2],q[3]);
  const now=Date.now(), exam=db.prepare('INSERT INTO exams(title,starts,ends) VALUES(?,?,?)').run('Ujian Matematika SMP - Demo',now-60000,now+86400000).lastInsertRowid;
  const snap=db.prepare('INSERT INTO exam_questions(exam_id,position,prompt,options,answer,explanation) VALUES(?,?,?,?,?,?)');
  items.forEach((q,i)=>snap.run(exam,i+1,q[0],JSON.stringify(q[1]),q[2],q[3]));
}
const send=(res,status,data,headers={})=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',...headers});res.end(JSON.stringify(data));};
const body=async req=>{let s='';for await(const c of req){s+=c;if(s.length>100000)throw Error('too large');}return JSON.parse(s||'{}');};
const cookie='exam_session';
function auth(req){const raw=(req.headers.cookie||'').split(';').map(x=>x.trim()).find(x=>x.startsWith(cookie+'='));if(!raw)return null;const token=decodeURIComponent(raw.slice(cookie.length+1));const row=db.prepare('SELECT u.*,s.token FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?').get(token,Date.now());return row||null;}
function need(user,role){return user&&user.role===role;}
function safeQuestion(q){return {position:q.position,prompt:q.prompt,options:JSON.parse(q.options)};}
async function handler(req,res){
 try{
  const url=new URL(req.url,'http://localhost'), path=url.pathname, method=req.method, user=auth(req);
  if(method==='GET'&&assets.has(path)){const [content,type]=assets.get(path);res.writeHead(200,{'Content-Type':type+'; charset=utf-8','X-Content-Type-Options':'nosniff'});return res.end(content);}
  if(method==='POST'&&path==='/api/login'){const b=await body(req);if(typeof b.code!=='string'||typeof b.pin!=='string'||b.code.length>30||b.pin.length>30)return send(res,400,{error:'Data masuk tidak valid.'});const u=get.get(b.code.trim().toUpperCase());if(!u||u.pin.length!==b.pin.length||Buffer.byteLength(u.pin)!==Buffer.byteLength(b.pin)||!timingSafeEqual(Buffer.from(u.pin),Buffer.from(b.pin)))return send(res,401,{error:'Kode atau PIN salah.'});const token=randomBytes(32).toString('hex');db.prepare('INSERT INTO sessions VALUES(?,?,?)').run(token,u.id,Date.now()+86400000);return send(res,200,{role:u.role,name:u.name},{'Set-Cookie':`${cookie}=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400`});}
  if(method==='POST'&&path==='/api/logout'){if(user)db.prepare('DELETE FROM sessions WHERE token=?').run(user.token);return send(res,200,{ok:true},{'Set-Cookie':`${cookie}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0`});}
  if(path==='/api/me'&&method==='GET')return send(res,200,user?{role:user.role,name:user.name}:{role:null});
  if(!user)return send(res,401,{error:'Silakan masuk kembali.'});
  if(path==='/api/practice'&&method==='GET'&&need(user,'student'))return send(res,200,{questions:Array.from({length:5},(_,i)=>({prompt:'Berapa hasil dari '+(i+4)+' × '+(i+2)+'?', options:[(i+4)*(i+2)-2,(i+4)*(i+2),(i+4)*(i+2)+2,(i+4)*(i+2)+4].map(String),answer:1,explanation:'Hasil perkaliannya adalah '+((i+4)*(i+2))+'.'}))});
  if((path==='/api/exam'&&method==='GET'||path==='/api/start'&&method==='POST')&&need(user,'student')){const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get();if(!e)return send(res,404,{error:'Belum ada ujian.'});const a=db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id);if(Date.now()>=e.ends&&a&&!a.submitted)db.prepare('UPDATE attempts SET submitted=1,submitted_at=? WHERE id=?').run(e.ends,a.id);const attempt=db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id);if(method==='POST'&&!attempt&&Date.now()>=e.starts&&Date.now()<e.ends){db.prepare('INSERT OR IGNORE INTO attempts(exam_id,user_id) VALUES(?,?)').run(e.id,user.id);}
   const current=db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id), qs=db.prepare('SELECT position,prompt,options FROM exam_questions WHERE exam_id=? ORDER BY position').all(e.id), ans=current?db.prepare('SELECT position,choice,updated FROM answers WHERE attempt_id=?').all(current.id):[];
   return send(res,200,{exam:{id:e.id,title:e.title,starts:e.starts,ends:e.ends,released:!!e.released},serverNow:Date.now(),attempt:current?{submitted:!!current.submitted,submittedAt:current.submitted_at}:null,questions:current&&!current.submitted?qs.map(safeQuestion):[],answers:ans});}
  if(path==='/api/answer'&&method==='POST'&&need(user,'student')){const b=await body(req);if(!Number.isInteger(b.position)||!Number.isInteger(b.choice)||b.choice<0||b.choice>3)return send(res,400,{error:'Jawaban tidak valid.'});const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get(),a=e&&db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id);if(!a||b.examId!==e.id||a.submitted||Date.now()>=e.ends)return send(res,409,{error:'Ujian sudah ditutup.'});const q=db.prepare('SELECT 1 FROM exam_questions WHERE exam_id=? AND position=?').get(e.id,b.position);if(!q)return send(res,400,{error:'Nomor soal tidak valid.'});db.prepare('INSERT INTO answers VALUES(?,?,?,?) ON CONFLICT(attempt_id,position) DO UPDATE SET choice=excluded.choice,updated=excluded.updated').run(a.id,b.position,b.choice,Date.now());return send(res,200,{ok:true,savedAt:Date.now()});}
  if(path==='/api/submit'&&method==='POST'&&need(user,'student')){const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get(),a=e&&db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id);if(!a)return send(res,409,{error:'Ujian belum dimulai.'});if(!a.submitted)db.prepare('UPDATE attempts SET submitted=1,submitted_at=? WHERE id=?').run(Math.min(Date.now(),e.ends),a.id);return send(res,200,{ok:true,submitted:true});}
  if(path==='/api/result'&&method==='GET'&&need(user,'student')){const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get();if(!e||!e.released)return send(res,403,{error:'Hasil belum dirilis.'});const a=db.prepare('SELECT * FROM attempts WHERE exam_id=? AND user_id=?').get(e.id,user.id);if(!a||!a.submitted)return send(res,403,{error:'Belum ada hasil.'});const score=db.prepare('SELECT count(*) n FROM answers a JOIN exam_questions q ON q.exam_id=? AND q.position=a.position WHERE a.attempt_id=? AND a.choice=q.answer').get(e.id,a.id).n;return send(res,200,{score,total:db.prepare('SELECT count(*) n FROM exam_questions WHERE exam_id=?').get(e.id).n});}
  if(need(user,'teacher')){
   if(path==='/api/bank'&&method==='GET')return send(res,200,{questions:db.prepare('SELECT id,prompt,options,answer FROM questions ORDER BY id').all().map(q=>({...q,options:JSON.parse(q.options)}))});
   if(path==='/api/bank'&&method==='POST'){const b=await body(req);if(typeof b.prompt!=='string'||b.prompt.trim().length<3||b.prompt.length>500||!Array.isArray(b.options)||b.options.length!==4||b.options.some(x=>typeof x!=='string'||x.length>160)||!Number.isInteger(b.answer)||b.answer<0||b.answer>3)return send(res,400,{error:'Soal perlu teks, empat pilihan, dan satu kunci.'});const r=db.prepare('INSERT INTO questions(prompt,options,answer,explanation) VALUES(?,?,?,?)').run(b.prompt.trim(),JSON.stringify(b.options),b.answer,String(b.explanation||'').slice(0,500));return send(res,200,{id:r.lastInsertRowid});}
   if(path.startsWith('/api/bank/')&&method==='PUT'){const id=Number(path.split('/').pop()),b=await body(req);if(!Number.isInteger(id)||typeof b.prompt!=='string'||b.prompt.length>500||!Array.isArray(b.options)||b.options.length!==4||b.options.some(x=>typeof x!=='string'||x.length>160)||!Number.isInteger(b.answer)||b.answer<0||b.answer>3)return send(res,400,{error:'Data soal tidak valid.'});db.prepare('UPDATE questions SET prompt=?,options=?,answer=?,explanation=? WHERE id=?').run(b.prompt.trim(),JSON.stringify(b.options),b.answer,String(b.explanation||'').slice(0,500),id);return send(res,200,{ok:true});}
   if(path==='/api/schedule'&&method==='POST'){const b=await body(req),start=Date.parse(b.starts),end=Date.parse(b.ends),ids=Array.isArray(b.ids)?b.ids.map(Number):[];if(!b.title||b.title.length>100||!Number.isFinite(start)||!Number.isFinite(end)||end<=start||ids.length<1||ids.length>100)return send(res,400,{error:'Jadwal atau paket soal tidak valid.'});const tx=db.prepare('SELECT * FROM questions WHERE id=?');const pack=ids.map(id=>tx.get(id));if(pack.some(x=>!x))return send(res,400,{error:'Soal tidak ditemukan.'});db.exec('BEGIN');try{const ex=db.prepare('INSERT INTO exams(title,starts,ends) VALUES(?,?,?)').run(b.title,start,end),ins=db.prepare('INSERT INTO exam_questions VALUES(?,?,?,?,?,?)');pack.forEach((q,i)=>ins.run(ex.lastInsertRowid,i+1,q.prompt,q.options,q.answer,q.explanation));db.exec('COMMIT');}catch(e){db.exec('ROLLBACK');throw e;}return send(res,200,{ok:true});}
   if(path==='/api/monitor'&&method==='GET'){const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get();if(!e)return send(res,200,{exam:null,students:[]});const rows=db.prepare('SELECT u.name,u.class_name,a.submitted,a.submitted_at,(SELECT count(*) FROM answers WHERE attempt_id=a.id) saved FROM users u LEFT JOIN attempts a ON a.user_id=u.id AND a.exam_id=? WHERE u.role=? ORDER BY u.id').all(e.id,'student');return send(res,200,{exam:{title:e.title,starts:e.starts,ends:e.ends,released:!!e.released},students:rows});}
   if(path==='/api/release'&&method==='POST'){const e=db.prepare('SELECT id FROM exams ORDER BY id DESC LIMIT 1').get();if(e)db.prepare('UPDATE exams SET released=1 WHERE id=?').run(e.id);return send(res,200,{ok:true});}
   if(path==='/api/export'&&method==='GET'){const e=db.prepare('SELECT * FROM exams ORDER BY id DESC LIMIT 1').get();if(!e||!e.released)return send(res,403,{error:'Rilis hasil terlebih dahulu.'});const rows=db.prepare('SELECT u.name,u.class_name,a.id,a.submitted FROM users u JOIN attempts a ON a.user_id=u.id WHERE a.exam_id=?').all(e.id);const csv=['Nama,Kelas,Skor,Total'];for(const r of rows){const score=db.prepare('SELECT count(*) n FROM answers a JOIN exam_questions q ON q.exam_id=? AND q.position=a.position WHERE a.attempt_id=? AND a.choice=q.answer').get(e.id,r.id).n;csv.push([r.name,r.class_name,score,db.prepare('SELECT count(*) n FROM exam_questions WHERE exam_id=?').get(e.id).n].map(x=>'"'+String(x).replaceAll('"','""')+'"').join(','));}return send(res,200,{csv:csv.join('\r\n')});}
  }
  return send(res,403,{error:'Akses tidak diizinkan.'});
 }catch(e){return send(res,e instanceof SyntaxError?400:500,{error:e instanceof SyntaxError?'Format data tidak valid.':'Terjadi kesalahan server.'});}
}
const server=createServer(handler);
const port=Number(process.env.PORT||3000);
server.listen(port,'127.0.0.1',()=>console.log('Portal demo berjalan di http://127.0.0.1:'+port));
