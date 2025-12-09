import math
import crypto
import os
import threading
import time
import math as m
#in this house we use reverse camel case
udpPort = 6969 #meowtp port!
# keysize - sha256 - OAEP - meowtp overhead
maxSectorSize = m.floor(crypto.keySize/8) - 2*m.ceil(256/8) - 2 - 21


getId = lambda msg: msg[0:5]

getParams = lambda msg: msg[14:]

getReq = lambda msg: msg[7:13]
def parseRawPkts(rawPkts, encrypted=False, privKey=None):
    pkts = [[]*len(rawPkts)] #allocate pkt array
    i=0
    if encrypted:#decrypt all packets
        rawPkts = crypto.bulkDecrypt(rawPkts, privKey) 

    for rawPkt in rawPkts:  #extract information
        id = i #packet ids not implemented yet
        req = getReq(rawPkt)
        params = getParams(rawPkt)
        pkts[id] = [req,params]
        i+=1
    return pkts
    
    

def sendMessages(sock, client_address, msgs, encrypt=False, publicKey=None):
    startTime = time.time()
    if encrypt:
        msgs = crypto.bulkEncrypt(msgs,publicKey)
    for msg in msgs:
        sock.transport.sendto(msg, client_address)
    duration = time.time()-startTime
    print(str((maxSectorSize*len(msgs)/duration)/10^6)+'MB/s')#speed
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



def assembleFile(sectors, fileName, size=None):
    file = open("downloaded/"+fileName, "wb")
    if size!=None:#smart assembler
        file.write(b'\x00'*size*maxSectorSize) #preall file

        for i in sectors.keys():
            file.seek(0,i*maxSectorSize)
            file.write(sectors[i])
    
    else:#old dumb assemble
        fileContents = b""

        for i in sectors.keys():
            fileContents+=sectors[i]
        file.write(fileContents)
        
    file.close()
    return
