import random
import threading
import time
import base64
import netlib
import cli
import srv

netlib.ENCODING = "utf8"


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "127.0.0.1", 0
    ENCODING = "utf8"
    server = srv.ThreadedTCPServer((HOST, PORT), srv.ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address  # pyright: ignore[reportAssignmentType]

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)
        dur = []
        while True:
            start = time.time()
            c1 = cli.client((ip, port))  # pyright: ignore[reportArgumentType]
            aa = base64.b64encode(random.randbytes(8)).decode(ENCODING)
            meow = base64.b64encode(random.randbytes(8)).decode(ENCODING)
            x = c1.post(aa, meow)
            c1.close()
            c1.open()
            y = c1.query("apple")
            c1.close()
            c1 = None
            end = time.time()
            dur.append(end-start)
            print(f"pps{len(dur)/sum(dur)}")