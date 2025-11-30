import lib, socketserver, cryptography # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]


class UDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        print(f"{self.client_address[0]} connected!")


        try: 
            if keychain[self.client_address[0]]["encrypt"]:
                clientPK = keychain[self.client_address[0]]["clientPK"]#key was exchanged, assume all messages are encrypted
                data = lib.privKeyDecrypt(data,privKey)
        except:
            keychain[self.client_address[0]] = {"encrypt":False} #new ip! disable encryption
        encrypt = keychain[self.client_address[0]]["encrypt"]
        try:
            data = data.decode("utf-8").strip()
        except:
            pass


        
        param = lib.getParams(data)
        req = lib.getReq(data)
        print("matching: "+req)
        
        match req:
            case "hand?":
                msg = "meowtp hand "+pem.decode("utf-8")
            case "shake?":
                keychain[self.client_address[0]] = {
                        "clientPK":lib.recvPubkey(param),
                        "encrypt":True}
                encrypt = True
                clientPK = keychain[self.client_address[0]]["clientPK"]
                msg = "meowtp shake "+self.client_address[0]
            case "up":
                fileName = str(param.split("/")[-1::][0])

            case "down":
                lib.getParams()
            case _:
                msg = "meowtp await ?"

        if keychain[self.client_address[0]]["encrypt"]:
            msg = lib.pubKeyEncrypt(msg.encode("utf-8"),clientPK)
        else:
            msg = msg.encode("utf-8")
        sock.sendto(msg, self.client_address)



if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = lib.createKeyPair()
        keychain = {}
        server.serve_forever()