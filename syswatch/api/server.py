#!/usr/bin/env python3
import json,os,shutil,subprocess,time,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[2]; WEB=ROOT/'web'; AGENT=ROOT/'syswatch'/'agent'; sys.path.insert(0,str(AGENT))
try:
 from causal_engine import summary as agent_summary
except Exception:
 agent_summary=lambda:{'score':0,'confidence':0,'level':'UNKNOWN','chains':[],'events':[]}
HOST=os.environ.get('SYSWATCH_HOST','127.0.0.1'); PORT=int(os.environ.get('SYSWATCH_PORT','8080'))
def cpu_percent():
 def read():
  with open('/proc/stat') as f: v=list(map(int,f.readline().split()[1:8])); return sum(v),v[3]
 a=read(); time.sleep(.08); b=read(); total=b[0]-a[0]; idle=b[1]-a[1]; return round((1-idle/total)*100,1) if total else 0
def memory_percent():
 t=a=0
 with open('/proc/meminfo') as f:
  for l in f:
   k,v,*_=l.split(); t=int(v) if k=='MemTotal:' else t; a=int(v) if k=='MemAvailable:' else a
 return round((1-a/t)*100,1) if t else 0
def ports():
 try:return subprocess.check_output(['ss','-H','-lntup'],text=True,stderr=subprocess.DEVNULL,timeout=2).splitlines()[:100]
 except Exception:return []
def metrics():
 d=shutil.disk_usage('/'); return {'cpu':cpu_percent(),'memory':memory_percent(),'disk':round(d.used/d.total*100,1),'disk_free_gb':round(d.free/1024**3,2),'processes':sum(1 for p in Path('/proc').iterdir() if p.name.isdigit()),'ports':ports(),'hostname':os.uname().nodename,'platform':os.uname().sysname+' '+os.uname().release,'timestamp':int(time.time())}
def run_scan():
 engine=ROOT/'core'/'engine.sh'
 if not engine.exists(): return {'ok':False,'error':'Security engine not found; dashboard telemetry still available'}
 try:
  p=subprocess.run(['bash',str(engine)],cwd=str(ROOT),text=True,capture_output=True,timeout=60); return {'ok':p.returncode==0,'exit_code':p.returncode,'output':(p.stdout+p.stderr)[-12000:]}
 except subprocess.TimeoutExpired:return {'ok':False,'error':'Scan timed out after 60 seconds'}
class Handler(BaseHTTPRequestHandler):
 def send_json(self,payload,status=200):
  b=json.dumps(payload).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def serve(self,path,ctype):
  try:b=path.read_bytes()
  except FileNotFoundError:return self.send_error(404)
  self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/health':return self.send_json({'ok':True,'service':'syswatch','agent':'online'})
  if p=='/api/metrics':return self.send_json(metrics())
  if p=='/api/agent':return self.send_json(agent_summary())
  if p=='/api/scan':return self.send_json(run_scan())
  if p in ('/','/index.html'):return self.serve(WEB/'index.html','text/html; charset=utf-8')
  if p=='/manifest.webmanifest':return self.serve(WEB/'manifest.webmanifest','application/manifest+json')
  self.send_error(404)
 def log_message(self,fmt,*args): print('[SYSWATCH] '+fmt%args)
if __name__=='__main__': print(f'SYSWATCH PRO dashboard: http://{HOST}:{PORT}'); ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
