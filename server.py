import lib, socketserver, cryptography, os # pyright: ignore[reportMissingImports]






class UDPHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        print(f"C: {self.client_address[0]}")


        try: 
            if keyChain[self.client_address[0]]["encrypt"]:
                data = lib.privKeyDecrypt(data,privKey)
            else:
                data = data.decode("utf-8").strip()
        except:
            keyChain[self.client_address[0]] = {"encrypt":False} #new ip! disable encryption
            data = data.decode("utf-8").strip()
    
        
        
        param = lib.getParams(data)
        req = lib.getReq(data)
        data = None
        msgs = []
        try:
            match req:
                ### key exchange ###
                case "reqKey":
                    keyChain[self.client_address[0]] = {
                            "clientPK":lib.recvPubkey(param),
                            "encrypt":False}
                    
                    msgs.append("meowtp reqKey "+pem.decode("utf-8"))
                case "finKey":
                    keyChain[self.client_address[0]]["encrypt"] = True
                    msgs.append("meowtp ready ")
                ######
                case "sizeOf":
                    size = lib.fileSectSize(param[-1])
                    msgs.append("meowtp size "+str(size))

                case "up": #fi contents


                    pass
                
                case "down": #fi
                    file = param[0].replace("/","")
                    sectorDict = lib.disassembleFile(file)
                    
                    for i in sectorDict.keys():
                        msgs.append("meowtp part "+str(i)+" "+str(sectorDict[i],"utf-8"))
                    msgs.append("meowtp fin ") #TODO: send a hash?
                    print("served "+file+" to "+self.client_address[0])
                    msgs.append("meowtp ready ")

                case _:
                    msgs.append("meowtp ready ")
        except FileNotFoundError:
            msgs.append("meowtp 400 ")
        
        lib.sendMessages(sock, self.client_address, msgs,
                   encrypt=keyChain[self.client_address[0]]["encrypt"],
                   publicKey=keyChain[self.client_address[0]]["clientPK"] )


        



if __name__ == "__main__":
    with socketserver.UDPServer(("192.168.2.66", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = lib.createKeyPair()
        keyChain = {}
        server.serve_forever()