import math
import crypto
import os
import threading
import time
import math as m
#in this house we use reverse camel case
udpPort = 6969 #meowtp port!
# keysize - sha256 - OAEP - overhead
maxSectorSize = m.floor(crypto.keySize/8) - 2*m.ceil(256/8) - 20


getNonce = lambda msg: int.from_bytes(msg[0:4], 'big')

getParams = lambda msg: msg[10:]

getReq = lambda msg: msg[4:10]
def parseRawPkts(rawPkts, encrypted=False, privKey=None):
    pkts = [[]*len(rawPkts)] #allocate pkt array
    i=0
    if encrypted:#decrypt all packets
        rawPkts = crypto.bulkDecrypt(rawPkts, privKey) 

    for rawPkt in rawPkts:  #extract information
        nonce = getNonce(rawPkt)
        req = getReq(rawPkt)
        params = getParams(rawPkt)
        pkts[i] = [nonce,req,params]
        i+=1
    return pkts
    
    

def sendMessages(sock, client_address, msgs, encrypt=False, publicKey=None,nonce=0):
    startTime = time.time()
    #its noncing time
    for i,msg in enumerate(msgs):
        msgs[i]=nonce.to_bytes(4,'big')+msg
        nonce+=1
    if encrypt:
        msgs = crypto.bulkEncrypt(msgs,publicKey)
    for msg in msgs:
        sock.transport.sendto(msg, client_address)
    duration = time.time()-startTime
    print(str((maxSectorSize*len(msgs)/duration)/1000/1000)+'MB/s')#speed
    return nonce

def fileSectSize(fileName):
    size = math.ceil(os.path.getsize("./serving/"+fileName.strip())/maxSectorSize)
    return size


def readSector(fileName, sector):
    size = fileSectSize(fileName)
    file = open("./serving/"+fileName,"rb")
    file.seek(int(maxSectorSize*sector),0)
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



def assembleFile(sectors, fileName, size=None):
    file = open("downloaded/"+fileName, "wb")
    if size!=None:#smart assembler
        file.write(b'\x00'*size*maxSectorSize) #preall file

        for i in sectors.keys():
            file.seek(i*maxSectorSize,0)
            file.write(sectors[i])
    
    else:#old dumb assemble
        fileContents = b""

        for i in sectors.keys():
            fileContents+=sectors[i]
        file.write(fileContents)
        
    file.close()
    return
