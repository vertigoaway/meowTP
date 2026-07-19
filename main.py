import random
import threading
import time
import base64
import netlib
import cli
import srv
import logging

netlib.ENCODING = "utf8"

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    logging.basicConfig(filename="myapp.log", level=logging.INFO)
    HOST, PORT = "127.0.0.1", 0
    ENCODING = "utf8"
    server = srv.ThreadedTCPServer((HOST, PORT), srv.ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address  # pyright: ignore[reportAssignmentType]

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)

        server_thread.daemon = True
        server_thread.start()
        #logging.info("Server loop running in thread:", str(server_thread.name))

        while True:
            c1 = cli.client((ip, port))  # pyright: ignore[reportArgumentType]
            x = c1.post('abcdefghijklmnopqrstuvwxyzlhf;isfsdferfneiufhrufwnrwefjwpfjdklvdkgjaspfjasdklfaljksrfkljas','asfiofvjklwremvpasjbviafvmwiefpasdojfiasdjfaskl;dfjoiwejqlk;fnsdlmvndfoibuhreiouydsflkgjnlkjbhsifrutsi')
            print(f"{c1.ping()*1000}ms")
            c1.close()
            c1 = None
