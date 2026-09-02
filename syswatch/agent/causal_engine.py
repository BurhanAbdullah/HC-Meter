#!/usr/bin/env python3
import json,time
from pathlib import Path
from collections import deque

RULES={
 'reverse_shell':['new_port','reverse_shell'],
 'persistence':['reverse_shell','file_write_tmp','cron_change'],
 'privilege_escalation':['reverse_shell','new_suid'],
 'credential_access':['honeypot_access','outbound_c2'],
 'ransomware':['mass_file_write','outbound_c2'],
 'cryptominer':['outbound_c2','high_cpu_alien'],
 'bruteforce':['ssh_failure','new_port'],
}
STAGE={'reverse_shell':'Command & Control','persistence':'Persistence','privilege_escalation':'Privilege Escalation','credential_access':'Credential Access','ransomware':'Impact','cryptominer':'Execution','bruteforce':'Initial Access'}
WEIGHT={'new_port':.30,'reverse_shell':.90,'file_write_tmp':.40,'cron_change':.60,'new_suid':.80,'honeypot_access':.99,'outbound_c2':.70,'mass_file_write':.85,'high_cpu_alien':.50,'ssh_failure':.30}
class Engine:
 def __init__(self,state=None,window=120):
  self.window=window; self.state=Path(state or Path(__file__).resolve().parents[2]/'runtime/agent_state.json'); self.state.parent.mkdir(parents=True,exist_ok=True); self.events=deque(maxlen=500); self.chains={}; self.load()
 def load(self):
  try:
   d=json.loads(self.state.read_text()); self.events.extend(d.get('events',[])); self.chains=d.get('chains',{})
  except Exception: pass
 def save(self): self.state.write_text(json.dumps({'events':list(self.events),'chains':self.chains},indent=2))
 def ingest(self,t,detail='',pid=0,port=0):
  e={'ts':time.time(),'type':t,'detail':detail,'pid':pid,'port':port,'severity':'CRITICAL' if t in ('reverse_shell','new_suid','honeypot_access','mass_file_write') else 'HIGH'}; self.events.append(e); self.evaluate(); self.save(); return e
 def evaluate(self):
  now=time.time(); recent=[e for e in self.events if e['ts']>=now-self.window]; present={e['type'] for e in recent}
  for name,req in RULES.items():
   if set(req)<=present:
    matched=[e for e in recent if e['type'] in req]; conf=min(.99, sum(WEIGHT.get(e['type'],.3) for e in matched)/len(matched)+.2)
    self.chains[name]={'name':name.replace('_',' ').title(),'stage':STAGE[name],'confidence':round(conf,3),'tactic':'MITRE ATT&CK mapped behavioral chain','signals':matched,'last_seen':now}
  for name,c in list(self.chains.items()):
   if c['last_seen']<now-self.window*2: del self.chains[name]
 def summary(self):
  active=list(self.chains.values()); conf=max([c['confidence'] for c in active],default=0); score=min(100,int(conf*100)); level='CRITICAL' if score>=85 else 'HIGH' if score>=65 else 'MEDIUM' if score>=30 else 'LOW'; return {'score':score,'confidence':conf,'level':level,'chains':active,'events':list(self.events)[-100:]}
engine=Engine()

def feed_signal(signal_type,detail='',pid=0,port=0): return engine.ingest(signal_type,detail,pid,port)
def summary(): return engine.summary()
if __name__=='__main__': print(json.dumps(engine.summary(),indent=2))