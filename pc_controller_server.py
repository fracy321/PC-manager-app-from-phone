#!/usr/bin/env python3
"""
PC Remote Controller Server
Avvia sul PC - genera un codice di sessione per connettere il telefono via rete locale (WiFi/LAN)
"""

import http.server
import socketserver
import json
import os
import sys
import subprocess
import platform
import socket
import random
import string
import threading
import time
import urllib.parse
import glob
import shutil
import psutil
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PORT = 8765
SESSION_CODES = {}   # code -> {"created": timestamp, "active": True}
SYSTEM = platform.system()  # Windows / Darwin / Linux

# ─── UTILITY ──────────────────────────────────────────────────────────────────

def generate_code():
    """Genera codice 6 caratteri alfanumerico"""
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    SESSION_CODES[code] = {"created": time.time(), "active": True}
    return code

def validate_code(code):
    if code in SESSION_CODES:
        data = SESSION_CODES[code]
        # Codice valido per 24 ore
        if time.time() - data["created"] < 86400:
            return True
    return False

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=15)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Timeout: comando troppo lento"
    except Exception as e:
        return f"Errore: {e}"

# ─── OPERAZIONI PC ────────────────────────────────────────────────────────────

def get_pc_info():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
    return {
        "os": f"{platform.system()} {platform.release()}",
        "hostname": socket.gethostname(),
        "cpu_percent": cpu,
        "ram_total_gb": round(mem.total / 1e9, 1),
        "ram_used_gb": round(mem.used / 1e9, 1),
        "ram_percent": mem.percent,
        "disk_total_gb": round(disk.total / 1e9, 1),
        "disk_used_gb": round(disk.used / 1e9, 1),
        "disk_percent": disk.percent,
        "boot_time": boot,
        "python": platform.python_version(),
    }

def list_running_apps():
    apps = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            if info['name'] and info['status'] == 'running':
                mem_mb = round(info['memory_info'].rss / 1e6, 1) if info['memory_info'] else 0
                apps.append({"pid": info['pid'], "name": info['name'], "cpu": info['cpu_percent'], "mem_mb": mem_mb})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(apps, key=lambda x: x['mem_mb'], reverse=True)[:50]

def kill_app(pid_or_name):
    try:
        pid = int(pid_or_name)
        p = psutil.Process(pid)
        p.terminate()
        return f"Processo {pid} terminato"
    except ValueError:
        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if pid_or_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    killed.append(proc.info['name'])
            except:
                pass
        return f"Terminati: {', '.join(killed)}" if killed else "Nessun processo trovato"
    except Exception as e:
        return f"Errore: {e}"

def open_app(app_name):
    try:
        if SYSTEM == "Windows":
            os.startfile(app_name)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
        return f"Avviato: {app_name}"
    except Exception as e:
        return f"Errore apertura: {e}"

def open_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        import webbrowser
        webbrowser.open(url)
        return f"Aperto: {url}"
    except Exception as e:
        return f"Errore: {e}"

def web_search(query):
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

def list_files(path=None):
    if not path:
        path = str(Path.home())
    try:
        items = []
        for entry in os.scandir(path):
            try:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "path": entry.path
                })
            except:
                pass
        return {"path": path, "items": sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower()))}
    except Exception as e:
        return {"error": str(e)}

def create_file(path, content=""):
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File creato: {path}"
    except Exception as e:
        return f"Errore: {e}"

def delete_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"File eliminato: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Cartella eliminata: {path}"
        else:
            return "File/cartella non trovato"
    except Exception as e:
        return f"Errore: {e}"

def search_files(query, search_path=None):
    if not search_path:
        search_path = str(Path.home())
    results = []
    try:
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if query.lower() in f.lower():
                    full_path = os.path.join(root, f)
                    results.append(full_path)
                    if len(results) >= 50:
                        return results
    except:
        pass
    return results

def open_settings():
    if SYSTEM == "Windows":
        run_cmd("start ms-settings:")
        return "Impostazioni Windows aperte"
    elif SYSTEM == "Darwin":
        run_cmd("open /System/Applications/System\\ Preferences.app")
        return "Preferenze di Sistema aperte"
    else:
        run_cmd("gnome-control-center &")
        return "Impostazioni aperte"

def shutdown_pc():
    if SYSTEM == "Windows":
        run_cmd("shutdown /s /t 5")
    elif SYSTEM == "Darwin":
        run_cmd("sudo shutdown -h +1")
    else:
        run_cmd("shutdown -h +1")
    return "⚠️ PC si spegnerà tra 1 minuto"

def restart_pc():
    if SYSTEM == "Windows":
        run_cmd("shutdown /r /t 5")
    elif SYSTEM == "Darwin":
        run_cmd("sudo shutdown -r +1")
    else:
        run_cmd("shutdown -r +1")
    return "⚠️ PC si riavvierà tra 1 minuto"

def write_text(text):
    """Simula scrittura testo - apre blocco note con contenuto"""
    try:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        tmp.write(text)
        tmp.close()
        if SYSTEM == "Windows":
            os.startfile(tmp.name)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", tmp.name])
        else:
            subprocess.Popen(["xdg-open", tmp.name])
        return f"Testo aperto in editor: {tmp.name}"
    except Exception as e:
        return f"Errore: {e}"

# ─── HTTP HANDLER ─────────────────────────────────────────────────────────────

class PCControlHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Silenzia log HTTP

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Session-Code')
        self.end_headers()

    def get_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        return {}

    def check_auth(self):
        code = self.headers.get('X-Session-Code', '')
        return validate_code(code)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/' or path == '/mobile':
            self.send_html(MOBILE_HTML)
            return

        if path == '/ping':
            self.send_json({"status": "ok", "host": socket.gethostname()})
            return

        if not self.check_auth():
            self.send_json({"error": "Codice sessione non valido"}, 401)
            return

        if path == '/info':
            self.send_json(get_pc_info())
        elif path == '/apps':
            self.send_json(list_running_apps())
        elif path.startswith('/files'):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            p = params.get('path', [None])[0]
            self.send_json(list_files(p))
        elif path == '/search_files':
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            q = params.get('q', [''])[0]
            sp = params.get('path', [None])[0]
            self.send_json({"results": search_files(q, sp)})
        else:
            self.send_json({"error": "Endpoint non trovato"}, 404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        # Generazione codice (senza auth)
        if path == '/generate_code':
            code = generate_code()
            ip = get_local_ip()
            print(f"\n{'═'*50}")
            print(f"  NUOVO CODICE SESSIONE: {code}")
            print(f"  IP Server: {ip}:{PORT}")
            print(f"{'═'*50}\n")
            self.send_json({"code": code, "server_ip": ip, "port": PORT})
            return

        if path == '/validate_code':
            body = self.get_body()
            code = body.get('code', '')
            if validate_code(code):
                self.send_json({"valid": True, "host": socket.gethostname()})
            else:
                self.send_json({"valid": False}, 401)
            return

        if not self.check_auth():
            self.send_json({"error": "Codice sessione non valido"}, 401)
            return

        body = self.get_body()

        if path == '/open_app':
            self.send_json({"result": open_app(body.get('app', ''))})
        elif path == '/kill_app':
            self.send_json({"result": kill_app(body.get('target', ''))})
        elif path == '/open_url':
            self.send_json({"result": open_url(body.get('url', ''))})
        elif path == '/search_web':
            self.send_json({"result": web_search(body.get('query', ''))})
        elif path == '/create_file':
            self.send_json({"result": create_file(body.get('path', ''), body.get('content', ''))})
        elif path == '/delete_file':
            self.send_json({"result": delete_file(body.get('path', ''))})
        elif path == '/write_text':
            self.send_json({"result": write_text(body.get('text', ''))})
        elif path == '/settings':
            self.send_json({"result": open_settings()})
        elif path == '/shutdown':
            self.send_json({"result": shutdown_pc()})
        elif path == '/restart':
            self.send_json({"result": restart_pc()})
        elif path == '/shell':
            cmd = body.get('cmd', '')
            if cmd:
                self.send_json({"result": run_cmd(cmd)})
            else:
                self.send_json({"error": "Nessun comando"})
        else:
            self.send_json({"error": "Endpoint non trovato"}, 404)

# ─── MOBILE HTML (servito dal server stesso) ──────────────────────────────────

MOBILE_HTML = ''

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    global MOBILE_HTML
    # Ricarica html dal file se esiste
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pc_controller_mobile.html')
    if os.path.exists(html_path):
        with open(html_path, encoding='utf-8') as f:
            MOBILE_HTML = f.read()

    # Genera il primo codice all'avvio
    code = generate_code()
    ip = get_local_ip()

    print("╔══════════════════════════════════════════════════════╗")
    print("║         PC REMOTE CONTROLLER - SERVER                ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  IP Server  : {ip:<39}║")
    print(f"║  Porta      : {PORT:<39}║")
    print(f"║  Codice     : {code:<39}║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Mobile URL : http://{ip}:{PORT}/{'':>30}║")
    print("║                                                      ║")
    print("║  Apri l'URL sul telefono e inserisci il codice       ║")
    print("║  Premi Ctrl+C per fermare il server                  ║")
    print("╚══════════════════════════════════════════════════════╝")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), PCControlHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer fermato.")

if __name__ == '__main__':
    main()
