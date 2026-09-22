"""Local-only read-only artifact server; never serves dotfiles or credentials."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import unquote,urlsplit
from .config import ROOT

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        parts=unquote(urlsplit(self.path).path).split('/')
        if any(p.startswith('.') for p in parts if p):
            self.send_error(403);return
        return super().do_GET()
    def list_directory(self,path):
        self.send_error(403,'Directory listing disabled')

if __name__=='__main__':
    print('Open http://127.0.0.1:8765/reports/dashboard.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
