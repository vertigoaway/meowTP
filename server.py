import lib, socketserver, cryptography # pyright: ignore[reportMissingImports]






class UDPHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        print(f"{self.client_address[0]} connected!")


        try: 
            if keychain[self.client_address[0]]["encrypt"]:
                clientPK = keychain[self.client_address[0]]["clientPK"]#key was exchanged, all messages Should be encrypted
                data = lib.privKeyDecrypt(data,privKey)
        except:
            keychain[self.client_address[0]] = {"encrypt":False} #new ip! disable encryption
            clientPK = None
        encrypt = keychain[self.client_address[0]]["encrypt"]
        try:
            data = data.decode("utf-8").strip()
        except:
            pass


        
        param = lib.getParams(data)
        req = lib.getReq(data)
        print(req)
        msgs = []
        match req:
            case "reqKey":
                msgs.append("meowtp reqKey "+pem.decode("utf-8"))
            case "pKey":
                keychain[self.client_address[0]] = {
                        "clientPK":lib.recvPubkey(param),
                        "encrypt":True}
                encrypt = True
                clientPK = keychain[self.client_address[0]]["clientPK"]
                msgs.append("meowtp finKey "+self.client_address[0])
            
            case "sizeOf":
                size = lib.fileSize(param[-1])
                msgs.append("meowtp size "+str(size))

            case "up": #sector sector fi contents


                pass

            case "down": #down sector fi
                print("man idk")

            
            case _:
                msgs.append("meowtp ready ?")

        
        lib.msgHandler(msgs, clientPK,
                   keychain[self.client_address[0]]["encrypt"], 
                   sock, self.client_address)


        



if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = lib.createKeyPair()
        keychain = {}
        server.serve_forever()