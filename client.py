import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#init
srv = ("192.168.2.66",lib.udpPort)
privKey, pubKey, pem = lib.createKeyPair()
quit = False
encrypt = False
skimp = False
srvPubKey = None
file = {"expectingFile":False}



def interface(msgs):
    print("enter a request!")
    print("Download:")
    print('\t down <filename>')
    print("Upload:")
    print('\t up <filename>')
    cmd = "meowtp "+input("meowtp:")
    req = lib.getReq(cmd)
    param = lib.getParams(cmd)
    match req:
        case "down":
            cmd = cmd.replace("/","")
            msgs.append(cmd)
            file = {"expectingFile":True,"name":param[0],"sectors":{}}
        case _:
            print("err")
            raise NotImplemented
    return msgs,file





#begin connection
sock.sendto(bytes("meowtp reqKey ", "utf-8")+pem, srv)
print("requesting server public key")

while not quit:

    received = sock.recv(4096)

    if encrypt:
        received = lib.privKeyDecrypt(received, privKey)
    try:
        received = str(received, "utf-8")
    except:
        pass
    req = lib.getReq(received)
    param = lib.getParams(received)
    msgs = []
    match req:
        ### key exchange ###
        case "reqKey":# we recieve server key and get requested for client key
            skimp = True
            srvPubKey = lib.recvPubkey(param)
            msgs.append("meowtp finKey ")
        case "finKey":#ensure both can read messages
            print("key exchange completed")
            encrypt = True
            msgs.append("meowtp ready ?")
        case "ready": #idle
            msgs,file = interface(msgs)


        case "part": #download a "sector" of file
            if file["expectingFile"]:
                sectNo = param[0]
                contents = ''.join(x for x in param[1:])
                file["sectors"][sectNo] = bytes(contents,"utf-8")
        case "fin":
            if file["expectingFile"]:
                lib.assembleFile(file["sectors"],file["name"])
            file = {"expectingFile":False}
        case "400": #exception
            if file["expectingFile"]:
                print("400: doesn't exist or you are not authorized")
                file["expectingFile"] = {"expectingFile":False}
                interface(msgs)

        case _:
            print("invalid request recieved D:")
    


    if len(msgs) != 0:
        lib.sendMessages(sock,srv, msgs, encrypt=encrypt, publicKey=srvPubKey)
    else:
        lib.sendMessages(sock,srv, ["meowtp ready "], encrypt=encrypt,publicKey=srvPubKey)

    if skimp: #lazy? yeah lol
        encrypt = True
        skimp = False

