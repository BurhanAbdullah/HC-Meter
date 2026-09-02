#!/usr/bin/env python3
import json, os, shutil, subprocess, time, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'web'
AGENT = ROOT / 'syswatch' / 'agent'
sys.path.insert(0, str(AGENT))
try:
    from causal_engine import summary as agent_summary
except Exception:
    agent_summary = lambda: {'score': 0, 'confidence': 0, 'level': 'UNKNOWN', 'chains': [], 'events': []}

HOST = os.environ.get('SYSWATCH_HOST', '127.0.0.1')
PORT = int(os.environ.get('SYSWATCH_PORT', '8080'))
LOOPBACK_HOSTS = {'127.0.0.1', 'localhost', '[::1]'}


def host_is_local(value):
    if not value:
        return False
    value = value.strip().lower()
    host = value.split(']')[0] + ']' if value.startswith('[') else value.split(':', 1)[0]
    return host in LOOPBACK_HOSTS


def origin_is_local(value):
    if not value:
        return True
    try:
        u = urlparse(value)
        return u.scheme in ('http', 'https') and (u.hostname or '').lower() in ('127.0.0.1', 'localhost', '::1')
    except Exception:
        return False


def cmd(args, timeout=2):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip()
    except Exception:
        return ''


def cpu_percent():
    def read():
        with open('/proc/stat') as f:
            v = list(map(int, f.readline().split()[1:8]))
            return sum(v), v[3]
    a = read()
    time.sleep(0.08)
    b = read()
    total = b[0] - a[0]
    idle = b[1] - a[1]
    return round((1 - idle / total) * 100, 1) if total else 0


def memory_percent():
    total = available = 0
    with open('/proc/meminfo') as f:
        for line in f:
            k, v, *_ = line.split()
            if k == 'MemTotal:':
                total = int(v)
            elif k == 'MemAvailable:':
                available = int(v)
    return round((1 - available / total) * 100, 1) if total else 0


def ports():
    try:
        return subprocess.check_output(['ss', '-H', '-lntup'], text=True, stderr=subprocess.DEVNULL, timeout=2).splitlines()[:100]
    except Exception:
        return []


def network_interfaces():
    result = []
    base = Path('/sys/class/net')
    for p in sorted(base.iterdir() if base.exists() else []):
        name = p.name
        state = (p / 'operstate').read_text().strip() if (p / 'operstate').exists() else 'unknown'
        mac = (p / 'address').read_text().strip() if (p / 'address').exists() else ''
        rx = tx = 0
        try:
            rx = int((p / 'statistics/rx_bytes').read_text())
            tx = int((p / 'statistics/tx_bytes').read_text())
        except Exception:
            pass
        result.append({'name': name, 'state': state, 'mac': mac, 'rx_bytes': rx, 'tx_bytes': tx, 'wireless': (p / 'wireless').exists()})
    return result


def wifi_security():
    wireless = [x for x in network_interfaces() if x['wireless']]
    if not wireless:
        return {'available': False, 'status': 'NOT_PRESENT'}
    iface = wireless[0]['name']
    link = cmd(['iw', 'dev', iface, 'link'])
    ssid = signal = security = ''
    for line in link.splitlines():
        s = line.strip()
        if s.startswith('SSID:'):
            ssid = s.split(':', 1)[1].strip()
        elif 'signal:' in s:
            signal = s.split('signal:', 1)[1].strip().split()[0]
    nm = cmd(['nmcli', '-t', '-f', 'IN-USE,SSID,SECURITY,SIGNAL', 'dev', 'wifi'])
    for row in nm.splitlines():
        if row.startswith('*:'):
            parts = row.split(':')
            if len(parts) >= 4:
                ssid = ssid or parts[1]
                security = parts[2]
                signal = signal or parts[3]
                break
    if not security:
        security = 'UNKNOWN'
    status = 'GOOD' if security not in ('', '--', 'NONE', 'OPEN', 'UNKNOWN') else ('OPEN' if security in ('NONE', 'OPEN') else 'UNKNOWN')
    return {'available': True, 'interface': iface, 'ssid': ssid or 'unknown', 'signal': signal, 'security': security, 'status': status}


def firewall_health():
    ufw = cmd(['ufw', 'status'])
    if ufw:
        active = 'Status: active' in ufw
        return {'backend': 'ufw', 'status': 'ACTIVE' if active else 'INACTIVE', 'detail': ufw.splitlines()[0] if ufw.splitlines() else ''}
    fw = cmd(['firewall-cmd', '--state'])
    if fw:
        return {'backend': 'firewalld', 'status': 'ACTIVE' if fw == 'running' else 'INACTIVE', 'detail': fw}
    nft = cmd(['nft', 'list', 'ruleset'])
    if nft:
        return {'backend': 'nftables', 'status': 'CONFIGURED', 'detail': 'ruleset present'}
    return {'backend': 'unknown', 'status': 'NOT_DETECTED', 'detail': 'No supported firewall command reported an active ruleset'}


def ssh_health():
    path = Path('/etc/ssh/sshd_config')
    if not path.exists():
        return {'available': False, 'status': 'NOT_PRESENT'}
    values = {}
    try:
        for line in path.read_text(errors='ignore').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    values[parts[0].lower()] = parts[1]
    except OSError:
        return {'available': True, 'status': 'UNKNOWN'}
    root = values.get('permitrootlogin', 'default')
    password = values.get('passwordauthentication', 'default')
    risk = root.lower() in ('yes', 'without-password', 'prohibit-password') and password.lower() == 'yes'
    return {'available': True, 'status': 'REVIEW' if risk else 'OK', 'permit_root_login': root, 'password_authentication': password}


def load_metrics():
    try:
        one, five, fifteen = os.getloadavg()
        return {'1m': round(one, 2), '5m': round(five, 2), '15m': round(fifteen, 2)}
    except OSError:
        return {'1m': 0, '5m': 0, '15m': 0}


def _proc_status(pid):
    values = {}
    try:
        for line in (Path('/proc') / str(pid) / 'status').read_text(errors='ignore').splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                values[k] = v.strip()
    except OSError:
        return values
    return values


def process_lineage(limit=250):
    """Return a bounded, read-only process tree without exposing command lines."""
    result = []
    proc = Path('/proc')
    for p in proc.iterdir() if proc.exists() else []:
        if not p.name.isdigit():
            continue
        pid = int(p.name)
        status = _proc_status(pid)
        if not status:
            continue
        try:
            stat = (p / 'stat').read_text(errors='ignore')
            close = stat.rfind(')')
            fields = stat[close + 2:].split() if close >= 0 else []
            ppid = int(fields[1]) if len(fields) > 1 else 0
            state = fields[0] if fields else '?'
        except (OSError, ValueError):
            continue
        try:
            exe = os.readlink(p / 'exe')
        except OSError:
            exe = status.get('Name', 'unknown')
        uid = status.get('Uid', '0').split()[0]
        try:
            user = cmd(['getent', 'passwd', uid], timeout=0.5).split(':', 1)[0] or uid
        except Exception:
            user = uid
        try:
            start_ticks = int(fields[19]) if len(fields) > 19 else 0
            hz = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            boot = float(Path('/proc/stat').read_text().split('btime ', 1)[1].splitlines()[0]) if 'btime ' in Path('/proc/stat').read_text() else time.time()
            start_time = round(boot + start_ticks / hz, 3)
        except Exception:
            start_time = 0
        result.append({'pid': pid, 'ppid': ppid, 'state': state, 'name': status.get('Name', 'unknown'), 'exe': exe, 'user': user, 'start_time': start_time})
        if len(result) >= limit:
            break
    result.sort(key=lambda x: (x['ppid'], x['pid']))
    return result


def metrics():
    d = shutil.disk_usage('/')
    interfaces = network_interfaces()
    return {
        'cpu': cpu_percent(),
        'memory': memory_percent(),
        'disk': round(d.used / d.total * 100, 1),
        'disk_free_gb': round(d.free / 1024**3, 2),
        'processes': sum(1 for p in Path('/proc').iterdir() if p.name.isdigit()),
        'ports': ports(),
        'hostname': os.uname().nodename,
        'platform': os.uname().sysname + ' ' + os.uname().release,
        'kernel': os.uname().release,
        'uptime_seconds': round(float(Path('/proc/uptime').read_text().split()[0])) if Path('/proc/uptime').exists() else 0,
        'load': load_metrics(),
        'interfaces': interfaces,
        'wifi': wifi_security(),
        'firewall': firewall_health(),
        'ssh': ssh_health(),
        'timestamp': int(time.time()),
    }


def run_scan():
    engine = ROOT / 'core' / 'engine.sh'
    if not engine.exists():
        return {'ok': False, 'error': 'Security engine not found; dashboard telemetry still available'}
    try:
        p = subprocess.run(['bash', str(engine)], cwd=str(ROOT), text=True, capture_output=True, timeout=60)
        return {'ok': p.returncode == 0, 'exit_code': p.returncode, 'output': (p.stdout + p.stderr)[-12000:]}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'Scan timed out after 60 seconds'}


class Handler(BaseHTTPRequestHandler):
    def security_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

    def trusted(self):
        return host_is_local(self.headers.get('Host')) and origin_is_local(self.headers.get('Origin'))

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.security_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve(self, path, ctype):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            return self.send_error(404)
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.security_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.trusted():
            return self.send_json({'ok': False, 'error': 'untrusted host or origin'}, 403)
        path = urlparse(self.path).path
        if path == '/api/health':
            return self.send_json({'ok': True, 'service': 'syswatch', 'agent': 'online'})
        if path == '/api/metrics':
            return self.send_json(metrics())
        if path == '/api/processes':
            return self.send_json({'timestamp': int(time.time()), 'processes': process_lineage()})
        if path == '/api/agent':
            return self.send_json(agent_summary())
        if path == '/api/scan':
            self.send_response(405)
            self.send_header('Allow', 'POST')
            self.security_headers()
            self.end_headers()
            return
        if path in ('/', '/index.html'):
            return self.serve(WEB / 'index.html', 'text/html; charset=utf-8')
        if path == '/manifest.webmanifest':
            return self.serve(WEB / 'manifest.webmanifest', 'application/manifest+json')
        self.send_error(404)

    def do_POST(self):
        if not self.trusted():
            return self.send_json({'ok': False, 'error': 'untrusted host or origin'}, 403)
        if urlparse(self.path).path == '/api/scan':
            return self.send_json(run_scan())
        self.send_error(404)

    def log_message(self, fmt, *args):
        print('[SYSWATCH] ' + fmt % args)


if __name__ == '__main__':
    print(f'SYSWATCH PRO dashboard: http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
