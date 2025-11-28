import lib, socketserver


class UDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print(f"{self.client_address[0]} wrote:")
        print(data)
        

if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!\nPort:"+str(lib.udpPort))
        server.serve_forever()