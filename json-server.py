#
# Simple HTTP server to get JSON messages from Wx7xx devices
#
# Requirements: Python 3.8 ( www.python.org )
#               Wx7xx device with firmware version 10-0-0-6 or higher
#               Allowed port in firewall
#               Cloud connection set to "User server" mode with enabled feature "Memory disabled"
#               HTTPS connection is not supported by this example
#
#  Purpose of this example is demonstration of communication with Wx7xx device(s).
#  It is not intended to be used in production environment without further changes.
#

# TCP port for http server
PORT = 8080

from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class HTTPServer_RequestHandler(BaseHTTPRequestHandler):

    # POST request handler
    def do_POST(self):
        # read POST data
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length).decode()
        #print('POST-path:', self.path, ', POST-data-len:', length)
        #print(data)

        # decode JSON
        j = json.loads(data)
        for ch in j["Channels"]:
            print(str(ch["Nr"])+" ("+ch["Quant"]+"): "+ch["ValStr"]+" "+ch["Unit"])

        # prepare response message data
        respData = '{\"Result\":true,\"Message\":\"This is a response message text.\"}'

        # send back response do device
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200)
        self.send_header("Content-length", str(len(respData)))
        self.end_headers()
        self.wfile.write(bytes(respData,"utf-8"))
        return

    # disable server log messages
    def log_message(self, format, *args):
        return

# run HTTP server
def run():
    print('Starting HTTP server...')
    httpd = HTTPServer(("", PORT), HTTPServer_RequestHandler)
    httpd.serve_forever()

run()
