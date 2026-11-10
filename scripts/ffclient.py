"""Klien Marionette minimal (pustaka standar) untuk mengendalikan Firefox headless pada pengujian UI.
Firefox harus terpasang. Tidak memasang paket tambahan."""
import json, socket, base64, subprocess, time, tempfile, os

class FF:
    def __init__(self, port=2829):
        self.prof = tempfile.mkdtemp(prefix="ffprof.")
        with open(os.path.join(self.prof, "user.js"), "w") as f:
            f.write('user_pref("marionette.port", %d);\n' % port)
        self.proc = subprocess.Popen(
            ["firefox", "--headless", "--no-remote", "--marionette", "--remote-allow-system-access", "--profile", self.prof],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.id = 0
        for _ in range(60):
            try:
                self.s = socket.create_connection(("127.0.0.1", port), timeout=240)
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("marionette tidak tersedia")
        self._recv()
        self.cmd("WebDriver:NewSession", {"capabilities": {}})

    def _recv(self):
        buf = b""
        while b":" not in buf:
            buf += self.s.recv(1)
        n = int(buf.split(b":")[0])
        data = b""
        while len(data) < n:
            data += self.s.recv(n - len(data))
        return json.loads(data)

    def cmd(self, name, params=None):
        self.id += 1
        msg = json.dumps([0, self.id, name, params or {}]).encode()
        self.s.sendall(str(len(msg)).encode() + b":" + msg)
        while True:
            r = self._recv()
            if r[0] == 1 and r[1] == self.id:
                if r[2]:
                    raise RuntimeError(json.dumps(r[2])[:400])
                return r[3]

    def go(self, url): return self.cmd("WebDriver:Navigate", {"url": url})
    def js(self, script, args=None, timeout=60000):
        self.cmd("WebDriver:SetTimeouts", {"script": timeout})
        return self.cmd("WebDriver:ExecuteAsyncScript", {"script": script, "args": args or []})["value"]
    def rect(self, w, h): return self.cmd("WebDriver:SetWindowRect", {"width": w, "height": h})
    def shot(self, path, full=False):
        v = self.cmd("WebDriver:TakeScreenshot", {"full": full, "hash": False})["value"]
        open(path, "wb").write(base64.b64decode(v))
    def keys(self, *keys):
        acts = []
        for k in keys:
            acts += [{"type": "keyDown", "value": k}, {"type": "keyUp", "value": k}]
        self.cmd("WebDriver:PerformActions", {"actions": [{"type": "key", "id": "kbd", "actions": acts}]})
    def zoom(self, factor):
        self.cmd("Marionette:SetContext", {"value": "chrome"})
        try:
            self.js("let [f,cb]=[arguments[0],arguments[arguments.length-1]]; gBrowser.selectedBrowser.fullZoom=f; cb(gBrowser.selectedBrowser.fullZoom);", [factor])
        finally:
            self.cmd("Marionette:SetContext", {"value": "content"})
    def close(self):
        try: self.cmd("Marionette:Quit")
        except Exception: pass
        try: self.proc.terminate()
        except Exception: pass

TAB, ENTER, ESC, SPACE, RIGHT, LEFT = "", "", "", "", "", ""
