import http.server
import socketserver
import os
import subprocess
import json
import cgi
import sys

PORT = 8000

class CobolRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'visualizer.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/parse':
            try:
                # Parse the form data
                ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
                if ctype == 'multipart/form-data':
                    pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    
                    if 'file' in fields:
                        file_content = fields['file'][0]
                        # Save to temp file
                        with open("temp_upload.cbl", "wb") as f:
                            f.write(file_content)
                            
                        # Run parser
                        try:
                            # Capture output
                            subprocess.run([sys.executable, "cobolparser.py", "temp_upload.cbl"], check=True)
                            
                            if os.path.exists("output.json"):
                                with open("output.json", "r") as f:
                                    data = json.load(f)
                                
                                self.send_response(200)
                                self.send_header('Content-Type', 'application/json')
                                self.send_header('Access-Control-Allow-Origin', '*')
                                self.end_headers()
                                self.wfile.write(json.dumps(data).encode())
                            else:
                                raise Exception("Parser failed to generate output.json")
                                
                        except subprocess.CalledProcessError as e:
                            self.send_response(500)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(f"Parser execution failed: {str(e)}".encode())
                        except Exception as e:
                            self.send_response(500)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(str(e).encode())
                            
                    else:
                        self.send_error(400, "No file provided")
                else:
                    self.send_error(400, "Invalid Content-Type")
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"Server Error: {str(e)}".encode())
        else:
            self.send_error(404)

if __name__ == "__main__":
    Handler = CobolRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving COBOL Visualizer at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
