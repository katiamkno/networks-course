import socket
import threading
import requests
import sys
from datetime import datetime
import logging
import os
from urllib.parse import urlparse

PROXY_HOST = "localhost"
PROXY_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
LOG_FILE = "proxy.log"
TIMEOUT = 10
CACHE_DIR = "cache"
BLACKLIST_FILE = "blacklist.txt"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)s] %(message)s',
    handlers=[
        logging.FileHandler("proxy.log"),
        logging.StreamHandler()
    ]
)

def log(msg, level=logging.INFO):
    logging.log(level, msg)

def log_request(client_ip, url, status_code, method, from_cache = False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"{timestamp} [{client_ip}] {method} {url} - Status: {status_code} - from_cache: {from_cache}"
    log(log_msg)


def send_response(client, status_code, status_text):
    response = f'HTTP/1.1 {status_code} {status_text}\r\n'
    response += 'Content-Type: text/html; charset=utf-8\r\n'
    response += 'Content-Length: 0\r\n\r\n'
    client.send(response.encode())


def extract_base_url(target):
    if target.startswith('http://') or target.startswith('https://'):
        return target
    if target.startswith('//'):
        return f"https:{target}"
    if target.startswith('/'):
        target = target[1:]
    return f"https://{target}"

def get_resp_headers(status_code, response, message = "OK"):
    resp_headers = f"HTTP/1.1 {status_code} {message}\r\n"
    for header in ['Content-Type', 'Server', 'Cache-Control']:
        if hasattr(response, 'headers'):
            if header in response.headers:
                resp_headers += f"{header}: {response.headers[header]}\r\n"
        else:
            if header in response:
                resp_headers += f"{header}: {response[header]}\r\n"
    resp_headers += f"Content-Length: {len(response.content)}\r\n"
    resp_headers += "Connection: close\r\n\r\n"
    return resp_headers


cache = {}

class CacheResponse:
    def __init__(self, content, headers):
        self.content = content
        self.headers = headers
        self.status_code = 200

def get_cache_filename(url):
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()


def save_to_cache(url, response):
    filename = get_cache_filename(url)
    cache_path = os.path.join(CACHE_DIR, filename)

    with open(cache_path, 'wb') as f:
        f.write(response.content)
    cache[filename] = {
        "url": url,
        "Last-Modified": response.headers.get("Last-Modified", ""),
        "ETag": response.headers.get("ETag", ""),
    }

    with open(os.path.join(CACHE_DIR, "cache_meta.pkl"), 'wb') as f:
        import pickle
        pickle.dump(cache, f)

    log(f"Cached: {url}")


def get_from_cache(url):
    filename = get_cache_filename(url)
    cache_path = os.path.join(CACHE_DIR, filename)

    if os.path.exists(cache_path) and filename in cache:
        with open(cache_path, 'rb') as f:
            content = f.read()
        return content, cache[filename]

    return None, None


def load_cache():
    global cache
    meta_path = os.path.join(CACHE_DIR, "cache_meta.pkl")
    if os.path.exists(meta_path):
        import pickle
        with open(meta_path, 'rb') as f:
            cache = pickle.load(f)




def load_blacklist():
    blacklist = set()
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    blacklist.add(line.lower())
    return blacklist


def is_blocked(url, host, blacklist):
    host_lower = host.lower()
    for blocked in blacklist:
        if blocked in host_lower:
            return True
    url_lower = url.lower()
    for blocked in blacklist:
        if blocked in url_lower:
            return True
    return False


def send_blocked_response(client, url):
    body = f"""<html>
        <body>
        <h1>403 Forbidden</h1>
        <p>Access to <b>{url}</b> is blocked.</p>
        </body>
        </html>"""

    response = f'HTTP/1.1 403 Forbidden\r\n'
    response += 'Content-Type: text/html; charset=utf-8\r\n'
    response += f'Content-Length: {len(body)}\r\n'
    response += 'Connection: close\r\n\r\n'
    client.send(response.encode() + body.encode())

def handle_client(client, addr, blacklist):
    client_ip = addr[0]
    url = "unknown"
    global cache

    try:
        client.settimeout(TIMEOUT)
        data = b''
        while b'\r\n\r\n' not in data:
            chunk = client.recv(4096)
            if not chunk:
                return
            data += chunk
        try:
            req = data.decode('utf-8', errors='replace')
            first_line = req.split('\r\n')[0]
            method, target, _ = first_line.split()
        except Exception:
            send_response(client, 400, "Bad Request")
            log_request(client_ip, "parse_error", 400, "UNKNOWN")
            return

        method = method.upper()
        if method not in ("GET", "POST"):
            send_response(client, 405, "Method Not Allowed")
            log_request(client_ip, target, 405, method)
            return

        url = extract_base_url(target)
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if is_blocked(url, host, blacklist):
            log(f"[BLOCKED] {client_ip} tried to access {url}")
            log_request(client_ip, url, 403, method)
            send_blocked_response(client, url)
            return

        body = None
        if method == "POST":
            try:
                parts = data.split(b'\r\n\r\n', 1)
                if len(parts) > 1:
                    body = parts[1].decode('utf-8', errors='replace')
            except:
                body = None

        print(f"[{client_ip}] {method} {url}")

        try:
            if method == "GET":
                cached_content, cached_meta = get_from_cache(url)

                if cached_content:
                    headers = {}
                    if cached_meta.get("Last-Modified"):
                        headers["If-Modified-Since"] = cached_meta["Last-Modified"]
                    if cached_meta.get("ETag"):
                        headers["If-None-Match"] = cached_meta["ETag"]

                    if headers:
                        response = requests.get(url, headers=headers, verify=False, timeout=TIMEOUT)
                        if response.status_code == 304:
                            cache_resp = CacheResponse(cached_content, cached_meta)
                            resp_headers = get_resp_headers(200, cache_resp)
                            client.send(resp_headers.encode() + cache_resp.content)
                            log_request(client_ip, url, 200, method, from_cache=True)
                            return
                response = requests.get(url, verify=False, timeout=TIMEOUT)
                if response.status_code == 200:
                    save_to_cache(url, response)
            else:
                response = requests.post(url, data=body, verify=False, timeout=TIMEOUT)

            status_code = response.status_code
            log_request(client_ip, url, status_code, method)

            if status_code == 404:
                send_response(client, 404, "Not Found")
            else:
                resp_headers = get_resp_headers(status_code, response)
                client.send(resp_headers.encode() + response.content)


        except requests.exceptions.ConnectionError:
            if method == "POST":
                status_code = 504
                log_request(client_ip, url, status_code, method)
                send_response(client, 504, "Gateway Timeout")
            else:
                log(f"ConnectionError for {url}, retrying with google.com")
                try:
                    if target.startswith('/'):
                        new_url = f"https://www.google.com{target}"
                    else:
                        new_url = f"https://www.google.com/{target}"
                    log(f"Retry with: {new_url}")
                    response = requests.get(new_url, verify=False, timeout=TIMEOUT)
                    status_code = response.status_code
                    log_request(client_ip, url, status_code, method)

                    if status_code == 404:
                        send_response(client, 404, "Not Found")
                    else:
                        resp_headers = get_resp_headers(status_code, response)
                        client.send(resp_headers.encode() + response.content)
                except Exception as e2:
                    log(f"Google retry failed: {e2}")
                    send_response(client, 502, "Bad Gateway")
        except requests.exceptions.Timeout:
            status_code = 504
            log_request(client_ip, url, status_code, method)
            send_response(client, 504, "Gateway Timeout")
        except Exception as e:
            status_code = 500
            log_request(client_ip, url, status_code, method)
            send_response(client, 500, "Internal Server Error")
            print(f"Error: {e}")

    except socket.timeout:
        log_request(client_ip, url, 504, "TIMEOUT")
        send_response(client, 504,  "Gateway Timeout")
    except Exception as e:
        print(f"Unexpected error: {e}")
        try:
            log_request(client_ip, url, 500, "ERROR")
            send_response(client, 500, "Internal Server Error")
        except:
            pass
    finally:
        print(f"Cache size: {len(cache)}")
        client.close()


def start_proxy():
    load_cache()
    blacklist = load_blacklist()
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Port must be a number")
            return
    else:
        port = PROXY_PORT

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((PROXY_HOST, port))
    except Exception as e:
        print(f"Cannot bind to port {port}: {e}")
        return

    server.listen(10)

    print(f"Proxy server is running on http://{PROXY_HOST}:{port}")
    print(f"Logs: {LOG_FILE}")

    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr, blacklist))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.close()


if __name__ == "__main__":
    start_proxy()