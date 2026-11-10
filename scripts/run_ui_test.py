"""Menjalankan uji UI LibraryKu Unified di Firefox (Marionette) terhadap aplikasi nyata.
Kredensial dashboard dibaca dari ~/.libraryku_dashboard_credentials dan hanya disuntikkan ke fetch halaman
oleh harness uji (browser headless tidak bisa menjawab dialog Basic Auth). Tidak dicetak."""
import base64, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from ffclient import FF
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "bukti/publik", "ui_firefox_fungsional_setelah_auth.txt")
kv = dict(l.strip().split("=", 1) for l in open(os.path.expanduser("~/.libraryku_dashboard_credentials")) if "=" in l)
AUTH = "Basic " + base64.b64encode(f"{kv['username']}:{kv['password']}".encode()).decode()
body = open(os.path.join(HERE, "scripts/ui_test.js")).read()
ff = FF()
try:
    ff.rect(1366, 900); ff.go("http://127.0.0.1:8081/?x=0#beranda"); time.sleep(3)
    ff.js("sessionStorage.clear(); arguments[arguments.length-1](1)"); ff.go("http://127.0.0.1:8081/?x=1#beranda"); time.sleep(3)
    res = ff.js("const cb=arguments[arguments.length-1]; const __ARG0=arguments[0]; (async(arguments)=>{ try { %s } catch(e) { return (typeof out!=='undefined'?out.join('\\n'):'')+'\\nERROR '+e; } })([__ARG0]).then(cb,e=>cb('ERROR '+e));" % body, args=[AUTH], timeout=300000)
    open(OUT, "w").write("Uji UI Firefox setelah login untuk tulis (kredensial disuntikkan harness)\n" + str(res) + "\n")
    print(res)
finally:
    ff.close()
