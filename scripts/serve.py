#!/usr/bin/env python3
"""審片台本機伺服器（支援 Range）／ Local server for a review desk, with Range support.
python3 -m http.server 不支援 Range：在 Chrome 把時間軸拖到中間再按播放，影片會跳回 0 秒。
python3 -m http.server has no Range support, so in Chrome seeking and then pressing play restarts the film at 0.
用法 Usage: python3 serve.py <審片台資料夾 desk folder> [port, 預設 default 8787]
"""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class H(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        a = int(m.group(1)) if m.group(1) else max(size - int(m.group(2) or 0), 0)
        b = min(int(m.group(2)), size - 1) if m.group(1) and m.group(2) else size - 1
        if a > b or a >= size:
            self.send_error(416); return None
        f = open(path, "rb"); f.seek(a)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.send_header("Content-Length", str(b - a + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._left = b - a + 1
        return f

    def copyfile(self, src, dst):
        left = getattr(self, "_left", None)
        if left is None:
            return super().copyfile(src, dst)
        self._left = None
        while left > 0:
            buf = src.read(min(65536, left))
            if not buf: break
            dst.write(buf); left -= len(buf)

    def end_headers(self):
        if not getattr(self, "_left", None): self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

if __name__ == "__main__":
    os.chdir(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8787
    print(f"http://127.0.0.1:{port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
