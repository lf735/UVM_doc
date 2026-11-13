"""Dual-stack (IPv4 + IPv6) local HTTP server for UVM 1.2 Documentation."""

import errno
import http.server
import socket
import socketserver
import sys


class DualStackHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


class IPv4HTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    address_family = socket.AF_INET
    daemon_threads = True
    allow_reuse_address = False


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with DualStackHTTPServer(("::", port), handler) as httpd:
            print(f"Serving HTTP on :: (IPv4 + IPv6) port {port} ...", flush=True)
            httpd.serve_forever()
    except OSError as exc:
        if exc.errno in (errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT):
            # Fallback to IPv4-only if IPv6 is disabled on the host
            with IPv4HTTPServer(("0.0.0.0", port), handler) as httpd:
                print(f"Serving HTTP on 0.0.0.0 port {port} ...", flush=True)
                httpd.serve_forever()
        else:
            print(f"[ERROR] Cannot start server on port {port}: {exc}", file=sys.stderr, flush=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
