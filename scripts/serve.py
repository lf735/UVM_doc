"""Dual-stack (IPv4 + IPv6) local HTTP server for UVM 1.2 Documentation."""

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


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with DualStackHTTPServer(("::", port), handler) as httpd:
            print(f"Serving HTTP on :: (IPv4 + IPv6) port {port} ...", flush=True)
            httpd.serve_forever()
    except OSError:
        # Fallback to IPv4-only if IPv6 is disabled on the host
        with http.server.ThreadingHTTPServer(("0.0.0.0", port), handler) as httpd:
            print(f"Serving HTTP on 0.0.0.0 port {port} ...", flush=True)
            httpd.serve_forever()


if __name__ == "__main__":
    main()
