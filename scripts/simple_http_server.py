#!/usr/bin/env python3
"""Small static HTTP server that ensures .mov files are served with the
video/quicktime MIME type. Run from the repository root to serve files
on port 8000 (or pass --port).

Usage Examples:
  # Start server on default port 8000 from current directory
  python scripts/simple_http_server.py

  # Start server on port 8000 from repository root (recommended)
  python scripts/simple_http_server.py --port 8000 --directory .

  # Start server on different port
  python scripts/simple_http_server.py --port 3000

  # Start server from specific directory
  python scripts/simple_http_server.py --directory "path/to/serve"

  # Common usage for concert videos (run from VSCoding root)
  python scripts/simple_http_server.py --port 8000 --directory .

  # Then open in browser:
  # http://localhost:8000/concert/webcode/homepage.html
  # http://localhost:8000/concert/webcode/myconcerts.html
  # http://localhost:8000/concert/webcode/10-24-25-Freddie-Gibbs-Chicago-at-Aragon-Ballroom.html
"""
import argparse
import http.server
import socketserver
import re
import os
import mimetypes
import sys
from functools import partial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=8000)
    parser.add_argument('--directory', '-d', default='.')
    args = parser.parse_args()

    # Add mapping for .mov if it's missing on this platform
    mimetypes.add_type('video/quicktime', '.mov')
    mimetypes.add_type('video/quicktime', '.MOV')

    # Custom handler that supports HTTP Range requests so browsers can seek
    class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
        def send_head(self):
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                return super().send_head()
            try:
                f = open(path, 'rb')
            except OSError:
                return super().send_head()

            fs = os.fstat(f.fileno())
            size = fs.st_size
            start = 0
            end = size - 1
            range_header = self.headers.get('Range')
            if range_header:
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    if m.group(2):
                        end = int(m.group(2))
                self.send_response(206)
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                content_length = end - start + 1
            else:
                self.send_response(200)
                content_length = size

            ctype = self.guess_type(path)
            self.send_header('Content-type', ctype)
            self.send_header('Content-Length', str(content_length))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            f.seek(start)
            # store range for copyfile to use
            self._range = (start, end)
            return f

        def copyfile(self, source, outputfile):
            # If a range was requested, copy only the requested bytes
            r = getattr(self, '_range', None)
            if r is None:
                return super().copyfile(source, outputfile)
            start, end = r
            remaining = end - start + 1
            bufsize = 64*1024
            while remaining > 0:
                read = source.read(min(bufsize, remaining))
                if not read:
                    break
                outputfile.write(read)
                remaining -= len(read)

    # Use the handler with the requested directory so files are served from
    # the directory passed on the command line (like `python -m http.server`).
    Handler = partial(RangeRequestHandler, directory=args.directory)

    # Threading server is nicer for concurrent requests (video range requests)
    try:
        with socketserver.ThreadingTCPServer(('0.0.0.0', args.port), Handler) as httpd:
            httpd.allow_reuse_address = True
            print(f"Serving HTTP on 0.0.0.0 port {args.port} (http://0.0.0.0:{args.port}/) ...")
            print(f"Serving directory: {args.directory}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped by user')
        sys.exit(0)


if __name__ == '__main__':
    main()
