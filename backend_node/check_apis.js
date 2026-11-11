const http = require('http');
function post(url, body) {
  return new Promise((r,j)=>{
    const u=new URL(url);
    const req=http.request({hostname:u.hostname,port:u.port,path:u.pathname,method:'POST',headers:{'Content-Type':'application/json'}},(res)=>{
      let d='';res.on('data',c=>d+=c);res.on('end',()=>r({s:res.statusCode,b:d}));
    });
    req.on('error',j);req.write(JSON.stringify(body));req.end();
  });
}
function get(u) { return new Promise((r,j)=>{ http.get(u,res=>{let d='';res.on('data',c=>d+=c);res.on('end',()=>r({s:res.statusCode,b:d}))}).on('error',j)}); }
async function run() {
  console.log('-- Testing leave decision --');
  const r1 = await post('http://localhost:3000/api/warden/leaves/lv-1/status', { status: 'Approved' });
  console.log('Leave approve status:', r1.s, r1.b.substring(0,200));
  
  console.log('-- Testing complaints --');
  const r2 = await get('http://localhost:3000/api/complaints');
  console.log('GET /api/complaints:', r2.s, r2.b.substring(0,300));
}
run().catch(e=>console.error('ERR:',e.message));
