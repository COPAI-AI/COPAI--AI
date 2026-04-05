"""
Docling API shim: rewrites /v1alpha/ -> /v1/ for Open WebUI 0.6.5 compatibility.
Listens on 5001, proxies to Docling on 5002.
"""
import re
import http.server
import urllib.request
import urllib.error

DOCLING = "http://127.0.0.1:5002"


class Shim(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {self.path.replace('/v1alpha/', '/v1/', 1)}")

    def _proxy(self):
        path = re.sub(r"^/v1alpha/", "/v1/", self.path)
        url = DOCLING + path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(url, data=body, method=self.command)
        for k, v in self.headers.items():
            if k.lower() not in ("host", "content-length"):
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                self.send_response(r.status)
                for k, v in r.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(r.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()


if __name__ == "__main__":
    print("Docling shim listening on :5001 -> :5002")
    http.server.HTTPServer(("0.0.0.0", 5001), Shim).serve_forever()
