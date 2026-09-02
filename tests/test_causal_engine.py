import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'syswatch'/'agent'))
from causal_engine import Engine

def test_reverse_shell_chain(tmp_path):
 e=Engine(tmp_path/'state.json'); e.ingest('new_port','2222'); e.ingest('reverse_shell','bash'); s=e.summary(); assert s['chains']; assert s['level'] in ('HIGH','CRITICAL'); assert s['confidence'] >= .5

def test_no_false_chain(tmp_path):
 e=Engine(tmp_path/'state.json'); e.ingest('new_port','80'); s=e.summary(); assert not s['chains']
