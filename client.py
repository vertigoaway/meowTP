import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


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


    return msgs




privKey, pubKey, pem = lib.createKeyPair()
quit = False
encrypt = False
skimp = False
srvPubKey = None


sock.sendto(bytes("meowtp reqKey ", "utf-8")+pem, ("127.0.0.1", lib.udpPort))
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
            msgs = interface(msgs)

        case "size": #size of a file previously requested is sent to us
            size = int(param[-1])

        case "part": #download a "sector" of file
            param
        case _:
            print("invalid request recieved D:")
    



    lib.sendMessages(msgs,srvPubKey, encrypt, sock, ("127.0.0.1",lib.udpPort))

    if skimp: #lazy? yeah lol
        encrypt = True
        skimp = False

