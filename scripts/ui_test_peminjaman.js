const $=id=>document.getElementById(id), sleep=ms=>new Promise(r=>setTimeout(r,ms));
var out=[]; const ok=(n,c,d='')=>out.push((c?'PASS ':'FAIL ')+n+(d!==''?' | '+d:''));
const errs=[]; addEventListener('error',e=>errs.push(e.message)); addEventListener('unhandledrejection',e=>errs.push(String(e.reason)));
const __AUTH=arguments[0]; const of=window.fetch.bind(window); let useAuth=true;
window.fetch=async(u,o={})=>{
  if(String(u).includes('/api/sql/loans')){
    if(!useAuth) return new Response(JSON.stringify({error:'Halaman peminjaman khusus petugas. Masuk dengan nama pengguna dan kata sandi petugas.'}),{status:401,headers:{'Content-Type':'application/json'}});
    o={...o, headers:{...(o.headers||{}), Authorization:__AUTH}};
  }
  return of(u,o);
};
const hdr={'Content-Type':'application/json','X-Requested-With':'libraryku'};
const jpost=(p,b)=>of(p,{method:'POST',headers:hdr,body:JSON.stringify(b)}).then(r=>r.json());
const jput=(p,b)=>of(p,{method:'PUT',headers:hdr,body:JSON.stringify(b)}).then(r=>r.json());
const jdel=(p)=>of(p,{method:'DELETE',headers:hdr}).then(r=>r.json());
const set=(id,v)=>{const e=$(id); e.value=v; e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}))};
const rows=()=>[...document.querySelectorAll('#loanTable tr[data-loan-id]')];
const go=async r=>{ location.hash='#'+r; await sleep(1800) };
const iso=d=>{const t=new Date(Date.now()+d*864e5); return new Date(t.getTime()-t.getTimezoneOffset()*6e4).toISOString().slice(0,10)};
const opt=id=>[...$('loanBook').options].find(o=>o.value===String(id));
const visible=el=>!!el && el.getClientRects().length>0;

ok('mode awal SQL: menu Peminjaman terlihat', visible(document.querySelector('.nav a[data-route="peminjaman"]')));
const bk=(await jpost('/api/sql/books',{title:'[UJI-UI] Buku Pinjam',author:'Penulis Uji',category:'Umum',year:2024,stock:2})).data;
await go('peminjaman');
ok('halaman peminjaman tampil, formulir terbuka', !$('view-peminjaman').hidden && !$('loanBody').hidden && $('loanGate').hidden);
ok('pilihan buku memuat buku uji dengan stok 2', !!opt(bk.id) && /\(stok 2\)/.test(opt(bk.id).textContent), opt(bk.id)&&opt(bk.id).textContent);
ok('tanggal pinjam bawaan hari ini dan batas minimal mengikuti', $('loanDate').value===iso(0) && $('loanDue').min===iso(0), $('loanDate').value+' / '+$('loanDue').min);

const n0=rows().length;
$('loanSubmit').click(); await sleep(300);
ok('kirim kosong: galat tampil di kolom wajib, tidak ada pinjaman baru', !$('loanBook-error').hidden && !$('loanName-error').hidden && !$('loanNim-error').hidden && !$('loanDue-error').hidden && rows().length===n0);
set('loanBook',String(bk.id)); set('loanName','Siti Fiktif'); set('loanClass','S1TT-UJI-01'); set('loanNim','12ab'); set('loanDue',iso(7));
$('loanSubmit').click(); await sleep(300);
ok('NIM berisi huruf ditolak di formulir', !$('loanNim-error').hidden, $('loanNim-error').textContent);
set('loanNim','0099887766'); set('loanDue',iso(-1));
$('loanSubmit').click(); await sleep(300);
ok('batas sebelum tanggal pinjam ditolak di formulir', !$('loanDue-error').hidden, $('loanDue-error').textContent);

set('loanDue',iso(7)); set('loanNote','data fiktif');
$('loanSubmit').click(); await sleep(2500);
const r0=rows()[0];
ok('pinjaman baru tampil di tabel dengan status Dipinjam', !!r0 && /Siti Fiktif/.test(r0.textContent) && /Dipinjam/.test(r0.textContent) && r0.querySelector('[data-return-id]'), r0&&r0.textContent.replace(/\s+/g,' ').slice(0,120));
ok('NIM tampil utuh dengan nol di depan', !!r0 && r0.querySelector('.col-nim').textContent==='0099887766');
ok('stok di pilihan buku berkurang menjadi 1', /\(stok 1\)/.test(opt(bk.id).textContent), opt(bk.id).textContent);
ok('formulir dikosongkan setelah berhasil (nama, NIM, batas)', $('loanName').value==='' && $('loanNim').value==='' && $('loanDue').value==='' && $('loanDate').value===iso(0));

document.querySelector('[data-return-id]').click(); await sleep(2500);
const r1=rows()[0];
ok('setelah Kembalikan: status Dikembalikan dan tanggal aktual terisi', /Dikembalikan/.test(r1.textContent) && !r1.querySelector('[data-return-id]') && r1.querySelectorAll('td')[6].textContent.trim()!=='', r1.querySelectorAll('td')[6].textContent);
ok('stok kembali menjadi 2', /\(stok 2\)/.test(opt(bk.id).textContent), opt(bk.id).textContent);

await jput('/api/sql/books/'+bk.id,{title:'[UJI-UI] Buku Pinjam',author:'Penulis Uji',category:'Umum',year:2024,stock:0});
$('loanRefresh').click(); await sleep(1500);
ok('buku bersetok 0 tidak bisa dipilih', opt(bk.id).disabled && /habis/.test(opt(bk.id).textContent), opt(bk.id).textContent);
await jdel('/api/sql/books/'+bk.id);
$('loanRefresh').click(); await sleep(1500);
ok('buku dihapus: judul tetap ada di riwayat', rows().some(r=>/\[UJI-UI\] Buku Pinjam/.test(r.textContent)));

await go('dashboard'); document.querySelector('input[name="dbmode-dash"][value="nosql"]').click(); await sleep(1500);
ok('mode NoSQL: menu Peminjaman disembunyikan', !visible(document.querySelector('.nav a[data-route="peminjaman"]')));
await go('peminjaman');
ok('mode NoSQL: halaman menolak dengan pesan dan tombol pindah ke SQL', !$('loanGate').hidden && $('loanBody').hidden && /mode SQL/.test($('loanGateText').textContent), $('loanGateText').textContent);
$('loanGateBtn').click(); await sleep(2500);
ok('tombol pindah ke SQL membuka formulir kembali', $('loanGate').hidden && !$('loanBody').hidden && visible(document.querySelector('.nav a[data-route="peminjaman"]')));

useAuth=false; await go('dashboard'); await go('peminjaman');
ok('tanpa login petugas (401): halaman terkunci dengan pesan khusus petugas', !$('loanGate').hidden && $('loanBody').hidden && /khusus petugas/.test($('loanGateText').textContent), $('loanGateText').textContent.slice(0,60));
ok('tidak ada data peminjam tampil saat terkunci', rows().length===0 || $('loanBody').hidden);
useAuth=true; $('loanGateBtn').click(); await sleep(2500);
ok('setelah login (tombol Masuk): riwayat tampil', $('loanGate').hidden && !$('loanBody').hidden);
ok('tanpa galat JavaScript', errs.length===0, errs.join(' | '));
return out.join('\n');
