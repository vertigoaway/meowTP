import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#init
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
    print('meowtp:')

    cmd = "meowtp "+input("")
    req = lib.getReq(cmd)
    param = lib.getParams(cmd)
    match req:
        case "down":
            cmd = cmd.replace("/","")
            msgs.append(cmd)
            file = {"expectingFile":True,"name":param[0],"sectors":{}}

    return msgs,file





#begin connection
sock.sendto(bytes("meowtp reqKey ", "utf-8")+pem, ("192.168.2.66", lib.udpPort))
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

        case _:
            print("invalid request recieved D:")
    


    if len(msgs) != 0:
        lib.sendMessages(msgs,srvPubKey, encrypt, sock, ("192.168.2.66",lib.udpPort))

    if skimp: #lazy? yeah lol
        encrypt = True
        skimp = False

