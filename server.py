import lib, socketserver, cryptography # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!


def sendPubkey(param):
    msg = "meowtp pk "+pem.decode("utf-8")

    return msg

class UDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print(f"{self.client_address[0]} connected!")
        tmp, req, param = data.decode("utf-8").split(" ", 2)
        if tmp!="meowtp":
            print("not a meowtp client, throwing connection out")
            exit()
        tmp=None
        print("matching: "+req)
        match req:
            case "?":
                msg = sendPubkey(param)
                socket.sendto(msg.encode("utf-8"), self.client_address)
        print("valid request and sent!")
        
        
    



if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey = rsa.generate_private_key( #everytime program is started, a new key is used :3
            public_exponent = 65537,
            key_size=2048
        )
        pubKey = privKey.public_key()
        pem = pubKey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        server.serve_forever()