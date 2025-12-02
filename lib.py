import socket, math, os, crypto

#in this house we use reverse camel case
udpPort = 6969
keySize = 4096
maxSectorSize = int((446)-32) #cool ass magic numbers ik
#TODO: probably actually use these??

def parseRawPkts(rawPkts, encrypted=False, privKey=None):
    pkts = [[]*len(rawPkts)]
    i=0
    if encrypted:
        for rawPkt in rawPkts:
            rawPkt = crypto.privKeyDecrypt(privKey)
            id = i #packet id not implemented yet
            req = getReq(rawPkt)
            params = getParams(rawPkt)
            pkts[id] = [req,params]
            i+=1
    else: #no encryption!
        for rawPkt in rawPkts: 
            id = i #packet id not implemented yet
            req = getReq(rawPkt).decode('utf-8')
            params = getParams(rawPkt).decode('utf-8')
            pkts[id] = [req,params]
            i+=1
    return pkts



getId = lambda msg: msg[0:5]

getParams = lambda msg: msg[14:]

getReq = lambda msg: msg[7:13]


def sendMessages(sock, client_address, msgs, encrypt=False, publicKey=None):
    if encrypt:
        for i,msg in enumerate(msgs):
            msgs[i] = crypto.pubKeyEncrypt(msg,publicKey)
    
    else: #TODO: could be further optimized
        for i,msg in enumerate(msgs):
            msgs[i] = msg
    
    
    for msg in msgs:
        sock.sendto(msg, client_address)
    return

def fileSectSize(fileName):
    size = math.ceil(os.path.getsize("./serving/"+fileName)/maxSectorSize)
    return size


def readSector(fileName, sector):
    size = fileSectSize(fileName)
    file = open("./serving/"+fileName,"rb")
    file.seek(0,int(maxSectorSize*sector))
    contents = file.read(maxSectorSize)
    file.close()
    return contents


#sectors is a dictionary
# {sectNo:"sectContents"}
#TODO: allow & correct missing sectors

def disassembleFile(fileName):
    sectors = {}
    fileSectorSize = fileSectSize(fileName)
    file = open("serving/"+fileName, "rb")
    for i in range(0,fileSectorSize):
        sectors[i] = file.read(maxSectorSize)
    return sectors



def assembleFile(sectors, fileName):
    fileContents = b""
    file = open("downloaded/"+fileName, "wb")
    for i in sectors.keys():
        file.write(sectors[i])
    file.write(fileContents)
    file.close()
    return
