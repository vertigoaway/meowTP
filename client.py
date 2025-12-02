import socket, sys, cryptography, lib, random, crypto # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#init
srv = ("127.0.0.1",lib.udpPort)
privKey, pubKey, pem = crypto.createKeyPair()
quit = False
encrypt = False
skimp = False
srvPubKey = None
file = {"expectingFile":False}



def interface(msgs):
    print("enter a request!")
    print("Download:")
    print('\t downFi <filename>')
    print("Upload:")
    print('\t upldFi <filename>')
    print("Quit:")
    print("\t quit")
    cmd = "meowtp "+input("meowtp:")
    req = lib.getReq(cmd)
    param = lib.getParams(cmd)
    match req:
        case "downFi":
            cmd = cmd.replace("/","")
            msgs.append(cmd.encode())
            file = {"expectingFile":True,"name":cmd[14:],"sectors":{}}
        case "upldFi":
            cmd = cmd.replace("/","")
            msgs.append(cmd.encode())
            file = {"sendingFile":True,"name":cmd[14:],"sectors":lib.disassembleFile(cmd[14:])} 
            #TODO: finish upload implementation
        case "quit":
            global quit
            quit = True
            msgs.append(b"meowtp stpNow")
            file = {"expectingFile":False}
        case _:
            print("err")
            raise Exception("invalid command")
        
    return msgs,file





#begin connection
sock.sendto(bytes("meowtp reqKey ", "utf-8")+pem, srv)
print("requesting server public key")

while not quit:

    received = sock.recv(4096)

    if encrypt:
        received = crypto.privKeyDecrypt(received, privKey)
    else:
        received = str(received, "utf-8")
    
    req = lib.getReq(received)
    param = lib.getParams(received)
    msgs = []
    match req:
        ### key exchange ###
        case "reqKey":# we recieve server key and get requested for client key
            skimp = True
            srvPubKey = crypto.recvPubkey(param)
            msgs.append(b"meowtp finKey ")
        case "finKey":#ensure both can read messages
            print("key exchange completed")
            msgs.append(b"meowtp ready! ?")
        case b"ready!": #idle
            msgs,file = interface(msgs)


        case b"partFi": #download a "sector" of file
            if file["expectingFile"]:
                sectNo = int.from_bytes(param[0:6],"big")
                contents = param[7:]
                print(sectNo)
                file["sectors"][sectNo] = contents
        case b"finish":
            if file["expectingFile"]:
                lib.assembleFile(file["sectors"],file["name"])
            file = {"expectingFile":False}
        case b"err400": #exception
            if file["expectingFile"]:
                print("400: doesn't exist or you are not authorized")
                file["expectingFile"] = {"expectingFile":False}
                interface(msgs)

        case _:
            print("invalid request recieved D:")
            print(req)
    


    if len(msgs) != 0:
        lib.sendMessages(sock,srv, msgs, encrypt=encrypt, publicKey=srvPubKey)
    else:
        if file["expectingFile"] == False:
            lib.sendMessages(sock,srv, [b"meowtp ready!"], encrypt=encrypt,publicKey=srvPubKey)
        else:
            pass
    if skimp: #lazy? yeah lol
        encrypt = True
        skimp = False

