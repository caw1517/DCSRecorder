"""Loopback-only companion UI. Launch with --settings <local JSON file>."""
import argparse, json, secrets, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from library import Library


def serve(settings, port=0, open_browser=True):
    library = Library(settings)
    # One process owns this library's activation operations at a time.
    import msvcrt
    instance = (library.home / 'companion.lock').open('a+b')
    instance.seek(0); instance.write(b'0'); instance.flush(); instance.seek(0)
    try:
        msvcrt.locking(instance.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        instance.close()
        existing = library.home / 'companion-url.txt'
        if open_browser and existing.exists():
            from urllib.parse import urlparse
            url = existing.read_text(encoding='utf-8').strip()
            parsed = urlparse(url)
            if parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and parsed.path == '/':
                webbrowser.open(url)
        print('Companion is already running for this library.', flush=True)
        return
    token = secrets.token_urlsafe(32)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, value, content_type='application/json'):
            data = value.encode('utf-8') if isinstance(value, str) else json.dumps(value).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'nonce-" + token + "'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, {'error': 'Invalid local host.'})
            if self.path == '/':
                page = Path(__file__).with_name('index.html').read_text(encoding='utf-8').replace('__TOKEN__', token)
                if library.build_trial:
                    page=page.replace('Record a flight. Fly alongside it.','DCS '+library.build+' trial · Record a flight, then check playback.')
                    page=page.replace('DCS 2.9.29.27468','DCS '+library.build)
                return self.reply(200, page, 'text/html')
            if self.path == '/api/library':
                try:
                    hook = library.saved / 'Scripts/Hooks/dcs-recorder-autosave.lua'
                    from library import digest
                    hook_ok = hook.exists() and digest(hook) == digest(Path(__file__).with_name('recording_sink.lua'))
                    status_file = library.home / 'save-status.txt'
                    save_status = status_file.read_text(encoding='utf-8', errors='replace')[:1000] if status_file.exists() else ''
                    return self.reply(200, {'recordings': library.entries(), 'partial_count': len(list(library.recordings.glob('*.partial'))),
                                           'hook_installed': hook_ok, 'save_status': save_status, 'directory': str(library.recordings),
                                           'legacy_setup': library.legacy})
                except Exception as exc:
                    return self.reply(400, {'error': str(exc)})
            return self.reply(404, {'error': 'Not found.'})

        def do_POST(self):
            if not self.valid_host() or self.headers.get('X-Recorder-Token') != token:
                return self.reply(403, {'error': 'Reload this local app before continuing.'})
            if not lock.acquire(blocking=False):
                return self.reply(409, {'error': 'Another preparation is running; wait for it to finish.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 4096:
                    raise ValueError('Invalid request size.')
                args = json.loads(self.rfile.read(size))
                if self.path == '/api/authored/inspect':
                    result = library.authored_inspect(args['path'])
                elif self.path == '/api/authored/review':
                    result = library.authored_review(args['path'], args['source_sha256'], args['lineage'])
                elif self.path == '/api/authored/revision':
                    result = library.authored_save_revision(args['path'], args['source_sha256'], args.get('lineage'),
                                                            args.get('name'), args.get('decisions'))
                elif self.path == '/api/authored/recording':
                    result = library.authored_recording(args['path'], args['unit_id'], args['source_sha256'])
                elif self.path == '/api/authored/playback-options':
                    result = library.authored_playback_options(args['id'])
                elif self.path == '/api/authored/playback':
                    result = library.authored_playback(args['id'], args['player_id'], args['source_sha256'])
                elif self.path == '/api/rename':
                    library.rename(args['id'], args['name'])
                    result = {'message': 'Recording renamed. Original flight data preserved.'}
                elif self.path == '/api/practice':
                    result = library.practice()
                elif self.path == '/api/playback':
                    result = library.playback(args['id'])
                else:
                    return self.reply(404, {'error': 'Not found.'})
                self.reply(200, result)
            except Exception as exc:
                self.reply(400, {'error': str(exc)})
            finally:
                lock.release()

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    url = f'http://127.0.0.1:{server.server_port}/'
    (library.home / 'companion-url.txt').write_text(url, encoding='utf-8')
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        instance.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', required=True)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    serve(json.loads(Path(args.settings).read_text(encoding='utf-8-sig')), args.port, not args.no_browser)
