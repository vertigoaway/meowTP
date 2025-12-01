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
        try:
            data = data.decode("utf-8").strip()
        except:
            pass


        
        param = lib.getParams(data)
        req = lib.getReq(data)
        msgs = []
        match req:
            ### key exchange ###
            case "reqKey":
                print(param)
                keychain[self.client_address[0]] = {
                        "clientPK":lib.recvPubkey(param),
                        "encrypt":False}
                
                clientPK = keychain[self.client_address[0]]["clientPK"]
                msgs.append("meowtp reqKey "+pem.decode("utf-8"))
            case "finKey":
                keychain[self.client_address[0]]["encrypt"] = True
                clientPK = keychain[self.client_address[0]]["clientPK"]
                msgs.append("meowtp ready ?")
            ######
            case "sizeOf":
                size = lib.fileSize(param[-1])
                msgs.append("meowtp size "+str(size))

            case "up": #sector sector fi contents


                pass

            case "down": #down fi
                file = param[0].replace("/","")
                sectorDict = lib.disassembleFile(file)
                msgs.append("meowtp size "+lib.fileSize(file))
                for i in sectorDict.keys():
                    msgs.append("meowtp part "+str(i)+" "+str(sectorDict[i],"utf-8"))
                


            case _:
                msgs.append("meowtp ready ?")

        
        lib.sendMessages(msgs, clientPK,
                   keychain[self.client_address[0]]["encrypt"], 
                   sock, self.client_address)


        



if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = lib.createKeyPair()
        keychain = {}
        server.serve_forever()