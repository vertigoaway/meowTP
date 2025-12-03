import lib, asyncio,crypto # pyright: ignore[reportMissingImports]






class MyDatagramProtocol(asyncio.DatagramProtocol):


    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(f"Packet from {addr}")



        try: 
            if keyChain[addr[0]]["encrypt"]:
                print(keyChain[addr[0]['encrypt']])
        except KeyError:
            keyChain[addr[0]] = {"encrypt":False,"clientPK":None} #new ip! disable encryption
        lib.parseRawPkts([data],encrypted=keyChain[addr[0]]["encrypt"],privKey=privKey)
        
        
        param = lib.getParams(data)
        req = lib.getReq(data)
        data = None
        msgs = []
        try:
            match req:
                ### key exchange ###
                case "reqKey":
                    keyChain[addr[0]] = {
                            "clientPK":crypto.recvPubkey(param),
                            "encrypt":False}
                    
                    msgs.append(b"meowtp reqKey "+pem)
                case "finKey":
                    keyChain[addr[0]]["encrypt"] = True
                    msgs.append(b"meowtp ready! ")
                ######
                case b"sizeOf":
                    size = lib.fileSectSize(param[-1])
                    msgs.append(b"meowtp sizeOf "+{size.to_bytes(6,"big")})

                case b"upldFi": #fi contents


                    pass
                
                case b"downFi": #fi
                    file = param.decode().replace("/","")
                    sectorDict = lib.disassembleFile(file)
                    
                    for i in sectorDict.keys():
                        msgs.append(b"meowtp partFi "+i.to_bytes(6, "big")+b" "+sectorDict[i])
                    msgs.append(b"meowtp finish "+len(sectorDict.keys()).to_bytes(6, "big")) #TODO: send a hash?
                    print("served "+file+" to "+addr[0])
                    #msgs.append(b"meowtp ready! ")
                case b"stpNow":
                    print("client "+addr[0]+" disconnected")
                    keyChain[addr[0]]["encrypt"] = False
                    keyChain[addr[0]]["clientPK"] = None

                case _:
                    msgs.append(b"meowtp ready! ")
        except FileNotFoundError:
            msgs.append(b"meowtp err400 ")
        
        lib.sendMessages(self, addr, msgs,
                   encrypt=keyChain[addr[0]]["encrypt"],
                   publicKey=keyChain[addr[0]]["clientPK"] )


        

async def main():
    loop = asyncio.get_running_loop()
    print("Started UDP server")
    # Create a UDP server
    listen = loop.create_datagram_endpoint(lambda: MyDatagramProtocol(), local_addr=('127.0.0.1', lib.udpPort))
    transport, protocol = await listen
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    finally:
        transport.close()

if __name__ == "__main__":
    privKey, pubKey, pem = crypto.createKeyPair()
    keyChain = {}
    asyncio.run(main())
