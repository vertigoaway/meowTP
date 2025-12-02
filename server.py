import lib, socketserver, os,crypto # pyright: ignore[reportMissingImports]






class UDPHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        print(f"C: {self.client_address[0]}")


        try: 
            if keyChain[self.client_address[0]]["encrypt"]:
                data = crypto.privKeyDecrypt(data,privKey)
            else:
                data = data.decode("utf-8").strip()
        except KeyError:
            keyChain[self.client_address[0]] = {"encrypt":False} #new ip! disable encryption
            print(data)
            data = data.decode("utf-8").strip()
    
        
        
        param = lib.getParams(data)
        req = lib.getReq(data)
        data = None
        msgs = []
        print(req)
        try:
            match req:
                ### key exchange ###
                case "reqKey":
                    keyChain[self.client_address[0]] = {
                            "clientPK":crypto.recvPubkey(param),
                            "encrypt":False}
                    
                    msgs.append(b"meowtp reqKey "+pem)
                case "finKey":
                    keyChain[self.client_address[0]]["encrypt"] = True
                    msgs.append(b"meowtp ready! ")
                ######
                case b"sizeOf":
                    size = lib.fileSectSize(param[-1])
                    msgs.append(b"meowtp sizeOf "+size.to_bytes(6,"big"))

                case b"upldFi": #fi contents


                    pass
                
                case b"downFi": #fi
                    file = param.decode().replace("/","")
                    sectorDict = lib.disassembleFile(file)
                    
                    for i in sectorDict.keys():
                        msgs.append(b"meowtp partFi "+i.to_bytes(6, "big")+b" "+sectorDict[i])
                    msgs.append(b"meowtp finish ") #TODO: send a hash?
                    print("served "+file+" to "+self.client_address[0])
                    msgs.append(b"meowtp ready! ")
                case b"stpNow":
                    print("client "+self.client_address[0]+" disconnected")
                    keyChain[self.client_address[0]]["encrypt"] = False
                    keyChain[self.client_address[0]]["clientPK"] = None

                case _:
                    msgs.append(b"meowtp ready! ")
        except FileNotFoundError:
            msgs.append(b"meowtp err400 ")
        
        lib.sendMessages(sock, self.client_address, msgs,
                   encrypt=keyChain[self.client_address[0]]["encrypt"],
                   publicKey=keyChain[self.client_address[0]]["clientPK"] )


        



if __name__ == "__main__":
    with socketserver.ThreadingUDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = crypto.createKeyPair()
        keyChain = {}
        server.serve_forever()