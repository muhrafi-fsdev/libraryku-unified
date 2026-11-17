"""Uji tampilan halaman Peminjaman di Firefox (Marionette) pada stack uji.
Pemakaian: LIBRARYKU_BASE=http://127.0.0.1:55081 UJI_USER=... UJI_PASS=... python3 scripts/run_ui_peminjaman.py [berkas_hasil]
Kredensial uji fiktif hanya disuntikkan ke fetch halaman (browser headless tidak bisa menjawab dialog Basic Auth)."""
import base64, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from ffclient import FF
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ["LIBRARYKU_BASE"].rstrip("/")
AUTH = "Basic " + base64.b64encode(f"{os.environ['UJI_USER']}:{os.environ['UJI_PASS']}".encode()).decode()
body = open(os.path.join(HERE, "ui_test_peminjaman.js")).read()
ff = FF(port=2841)
try:
    ff.rect(1366, 900); ff.go(f"{BASE}/?x=0#beranda"); time.sleep(3)
    ff.js("sessionStorage.clear(); arguments[arguments.length-1](1)"); ff.go(f"{BASE}/?x=1#beranda"); time.sleep(3)
    res = ff.js("const cb=arguments[arguments.length-1]; const __ARG0=arguments[0]; (async(arguments)=>{ try { %s } catch(e) { return (typeof out!=='undefined'?out.join('\\n'):'')+'\\nERROR '+e; } })([__ARG0]).then(cb,e=>cb('ERROR '+e));" % body, args=[AUTH], timeout=300000)
    print(res)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(str(res) + "\n")
    n_fail = sum(1 for l in str(res).splitlines() if l.startswith("FAIL") or l.startswith("ERROR"))
    print(f"\nRINGKASAN UI peminjaman: {sum(1 for l in str(res).splitlines() if l.startswith('PASS'))} PASS, {n_fail} FAIL")
    sys.exit(1 if n_fail else 0)
finally:
    ff.close()
