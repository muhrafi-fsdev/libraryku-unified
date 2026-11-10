const $=id=>document.getElementById(id), sleep=ms=>new Promise(r=>setTimeout(r,ms));
var out=[]; const ok=(n,c,d='')=>out.push((c?'PASS ':'FAIL ')+n+(d!==''?' | '+d:''));
const errs=[], csp=[]; addEventListener('error',e=>errs.push(e.message)); addEventListener('unhandledrejection',e=>errs.push(String(e.reason))); addEventListener('securitypolicyviolation',e=>csp.push(e.violatedDirective+' '+e.blockedURI));
const net=[]; const __AUTH=arguments[0]; const of=window.fetch.bind(window); let delaySql=0;
window.fetch=async(u,o={})=>{ if(delaySql && String(u).includes('/api/sql/books') && (o.method||'GET')==='GET'){ await sleep(delaySql);} if(__AUTH && (o.method||'GET')!=='GET'){ o={...o, headers:{...(o.headers||{}), Authorization:__AUTH}}; } const r=await of(u,o); net.push([o.method||'GET',String(u),r.status]); return r; };
const set=(el,v)=>{el.value=v; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}))};
const radio=(grp,v)=>document.querySelector(`input[name="${grp}"][value="${v}"]`);
const rows=()=>[...document.querySelectorAll('#bookTable tr[data-id]')];
const api=async(p)=>(await of(p)).json();
const go=async(r)=>{location.hash='#'+r; await sleep(350)};
const stats=()=>[...document.querySelectorAll('#view-dashboard [data-stat]')].map(n=>n.textContent).join('/');
const sqlN0=(await api('/api/sql/books')).total, noN0=(await api('/api/nosql/books')).total;
ok('awal: SQL punya data asli, NoSQL terpisah', sqlN0>=3, `sql=${sqlN0} nosql=${noN0}`);
// 1 default & navigasi
ok('mode awal SQL (radio, banner, status)', radio('dbmode-dash','sql').checked && /PostgreSQL/.test($('modeBanner').textContent) && /PostgreSQL terhubung/.test($('statusText').textContent) && document.body.dataset.mode==='sql', $('statusText').textContent);
const navs=[...document.querySelectorAll('.nav a')].map(a=>a.textContent);
ok('navigasi 5 menu', navs.join()==='Beranda,Katalog,Dashboard,Perbandingan,Tentang', navs.join());
for(const r of ['katalog','dashboard','perbandingan','tentang','beranda']){ await go(r); const v=[...document.querySelectorAll('[data-view]')].filter(x=>!x.hidden).map(x=>x.dataset.view).join(); ok('rute '+r, v===r && document.querySelector('.nav [aria-current]').dataset.route===r && document.activeElement===document.querySelector(`[data-view="${r}"] h1`)); }
// 2 Perbandingan: data nyata
await go('perbandingan'); await sleep(1500);
ok('perbandingan: status kedua DB terhubung', $('cmpSqlStatus').textContent==='Terhubung' && $('cmpNosqlStatus').textContent==='Terhubung', $('cmpSqlStatus').textContent+' / '+$('cmpNosqlStatus').textContent);
ok('perbandingan: jumlah = API', $('cmpSqlTotal').textContent===new Intl.NumberFormat('id-ID').format(sqlN0) && $('cmpNosqlTotal').textContent===new Intl.NumberFormat('id-ID').format(noN0), $('cmpSqlTotal').textContent+' / '+$('cmpNosqlTotal').textContent);
ok('perbandingan: contoh JSON SQL dari API (id integer)', /"id": \d+/.test($('cmpSqlSample').textContent), $('cmpSqlSample').textContent.replace(/\s+/g,' ').slice(0,90));
$('cmpMeasure').click(); for(let i=0;i<40 && $('cmpMeasure').disabled;i++) await sleep(250);
const perf=[...document.querySelectorAll('#cmpPerfBody tr')].map(r=>r.textContent.replace(/\s+/g,' ').trim());
ok('perbandingan: ukur waktu menghasilkan 2 baris angka nyata', perf.length===2 && perf.every(t=>/\d+\.\d ms/.test(t)), perf.join(' || '));
// 3 NoSQL mode: dashboard
await go('dashboard'); radio('dbmode-dash','nosql').click(); await sleep(1200);
ok('ganti ke NoSQL: radio, banner, status, body', radio('dbmode-dash','nosql').checked && radio('dbmode-cat','nosql').checked && /MongoDB/.test($('modeBanner').textContent) && /MongoDB terhubung/.test($('statusText').textContent) && document.body.dataset.mode==='nosql', $('statusText').textContent);
ok('NoSQL: daftar = API NoSQL (terpisah dari SQL)', rows().length===noN0 && stats().startsWith(String(noN0)+'/'), `${rows().length} baris, stat ${stats()}`);
if(noN0===0) ok('NoSQL: empty state tampil', /Belum ada buku/.test($('bookTable').textContent));
ok('tombol tambah menyebut database aktif', /MongoDB/.test($('newBtn').textContent), $('newBtn').textContent.trim());
$('newBtn').click(); await sleep(250);
ok('form NoSQL: petunjuk menyebut MongoDB', /MongoDB/.test($('formHint').textContent), $('formHint').textContent);
set($('title'),'[UJI-UI-NOSQL] Buku Mongo'); set($('author'),'Penguji'); set($('category'),'Umum'); set($('year'),'2024'); set($('stock'),'6'); $('submitBtn').click(); await sleep(1800);
const nPost=net.filter(n=>n[0]==='POST').pop(); ok('NoSQL create: POST /api/nosql/books 201', nPost && nPost[1]==='/api/nosql/books' && nPost[2]===201, JSON.stringify(nPost));
const noId=rows()[0] && rows()[0].dataset.id; ok('NoSQL: baris baru dengan id ObjectId (24 heks)', /^[0-9a-f]{24}$/.test(noId||''), noId);
ok('toast menyebut MongoDB', /MongoDB/.test($('toast').textContent), $('toast').textContent.trim());
ok('SQL TIDAK ikut berubah', (await api('/api/sql/books')).total===sqlN0 && !(await api('/api/sql/books')).data.some(b=>b.title.includes('UJI-UI')));
// 4 filter aktif + edit
set($('dashSearch'),'mongo'); await sleep(250); ok('NoSQL: pencarian jalan', rows().length===1);
document.querySelector(`[data-edit-id="${noId}"]`).click(); await sleep(300);
ok('NoSQL edit: dialog terisi & petunjuk id', $('title').value.includes('Buku Mongo') && /dengan id/.test($('formHint').textContent), $('formHint').textContent);
set($('title'),'[UJI-UI-NOSQL] Buku Sesudah'); set($('stock'),'60'); $('submitBtn').click(); await sleep(2200);
const nPut=net.filter(n=>n[0]==='PUT').pop(); ok('NoSQL update: PUT /api/nosql/books/{id} 200', nPut && nPut[1]===`/api/nosql/books/${noId}` && nPut[2]===200, JSON.stringify(nPut));
const g=await api('/api/nosql/books/'+noId); ok('NoSQL update: GET id sesuai', g.data.title.endsWith('Sesudah') && g.data.stock===60);
ok('filter dibersihkan otomatis dan baris terlihat', $('dashSearch').value==='' && !!document.querySelector(`#bookTable tr[data-id="${noId}"]`));
// 5 Katalog NoSQL vs SQL (tanpa tercampur)
await go('katalog'); ok('Katalog (mode NoSQL): hanya buku Mongo', document.querySelectorAll('#catGrid .card').length===noN0+1 && $('catGrid').textContent.includes('Buku Sesudah') && !$('catGrid').textContent.includes('TEKNIK SIPIL'), $('catCount').textContent);
radio('dbmode-cat','sql').click(); await sleep(1200);
ok('Katalog ganti ke SQL: buku Mongo hilang, buku SQL muncul', !$('catGrid').textContent.includes('UJI-UI-NOSQL') && document.querySelectorAll('#catGrid .card').length===sqlN0 && /PostgreSQL/.test($('statusText').textContent), $('catCount').textContent);
ok('mode tersimpan di sesi (refresh akan memakai SQL)', sessionStorage.getItem('libraryku-mode')==='sql');
// 6 CRUD SQL
await go('dashboard'); $('newBtn').click(); await sleep(250);
set($('title'),'[UJI-UI-SQL] Buku Postgres'); set($('author'),'Penguji'); set($('category'),'Umum'); set($('year'),'2024'); set($('stock'),'7'); $('submitBtn').click(); await sleep(1800);
const sPost=net.filter(n=>n[0]==='POST').pop(); ok('SQL create: POST /api/sql/books 201', sPost[1]==='/api/sql/books' && sPost[2]===201, JSON.stringify(sPost));
const sqlId=rows()[0].dataset.id; ok('SQL: id angka', /^\d+$/.test(sqlId), sqlId);
document.querySelector(`[data-edit-id="${sqlId}"]`).click(); await sleep(300); set($('stock'),'70'); $('submitBtn').click(); await sleep(2000);
const sPut=net.filter(n=>n[0]==='PUT').pop(); ok('SQL update: PUT /api/sql/books/{id} 200', sPut[1]===`/api/sql/books/${sqlId}` && sPut[2]===200 && (await api('/api/sql/books/'+sqlId)).data.stock===70, JSON.stringify(sPut));
ok('NoSQL tidak ikut berubah oleh aksi SQL', (await api('/api/nosql/books')).total===noN0+1 && !(await api('/api/nosql/books')).data.some(b=>b.title.includes('UJI-UI-SQL')));
document.querySelector(`[data-delete-id="${sqlId}"]`).click(); await sleep(300);
ok('hapus SQL: dialog menyebut judul dan PostgreSQL', /Buku Postgres/.test($('confirmBook').textContent) && /PostgreSQL/.test($('confirmDb').textContent), $('confirmDb').textContent);
$('confirmDelete').click(); await sleep(1800); const sDel=net.filter(n=>n[0]==='DELETE').pop();
ok('SQL delete: DELETE /api/sql/books/{id} 200, data kembali', sDel[1]===`/api/sql/books/${sqlId}` && sDel[2]===200 && (await api('/api/sql/books')).total===sqlN0, JSON.stringify(sDel));
// 7 balapan: ganti mode saat request SQL tertunda
delaySql=1500; $('refreshBtn').click(); await sleep(150); radio('dbmode-dash','nosql').click(); await sleep(2600); delaySql=0;
ok('balapan: respons SQL yang terlambat tidak menimpa tampilan NoSQL', /MongoDB/.test($('modeBanner').textContent) && rows().length===noN0+1 && !$('bookTable').textContent.includes('TEKNIK SIPIL') && /MongoDB terhubung/.test($('statusText').textContent), `${rows().length} baris; ${$('statusText').textContent}`);
// 8 hapus buku uji NoSQL lewat UI
document.querySelector(`[data-delete-id="${noId}"]`).click(); await sleep(300);
ok('hapus NoSQL: dialog menyebut MongoDB', /MongoDB/.test($('confirmDb').textContent));
$('confirmDelete').click(); await sleep(1800); const nDel=net.filter(n=>n[0]==='DELETE').pop();
ok('NoSQL delete: DELETE /api/nosql/books/{id} 200 dan koleksi kembali', nDel[1]===`/api/nosql/books/${noId}` && nDel[2]===200 && (await api('/api/nosql/books')).total===noN0, JSON.stringify(nDel));
// 9 keyboard pada radio
radio('dbmode-dash','nosql').focus(); await sleep(100);
ok('galat JS', errs.length===0, errs.join(';'));
ok('tanpa pelanggaran CSP', csp.length===0, csp.join(';'));
sessionStorage.setItem('libraryku-mode','nosql');
return out.join('\n');
