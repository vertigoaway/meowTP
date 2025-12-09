from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import threading
keySize = 4096


def createKeyPair(): #you are never gonna believe what this does
    privKey = rsa.generate_private_key( 
        public_exponent = 65537,
        key_size=keySize
    )
    pubKey = privKey.public_key()

    pem = pubKey.public_bytes(
        encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return privKey, pubKey, pem

def pubKeyEncrypt(msg, key,result): #single threaded encrypt
    msg = key.encrypt(msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    result.append(msg)
    return msg, result

def privKeyDecrypt(msg, key, result):#single threaded decrypt
    msg = key.decrypt(
            msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    result.append(msg)
    return msg,result


def bulkEncrypt(msgs, key): #MT encryption
    threads = []
    result = []
    for i, msg in enumerate(msgs):
        thread = threading.Thread(target=pubKeyEncrypt, args=[msgs[i],key,result])
        threads.append(thread)
        threads[i].start()
    for i,t in enumerate(threads):
        t.join()
        msgs[i] = result[i]
    return msgs

def bulkDecrypt(msgs, key):#MT decryption
    threads = []
    result = []
    for i, msg in enumerate(msgs):
        thread = threading.Thread(target=privKeyDecrypt, args=[msgs[i],key,result])
        threads.append(thread)
        threads[i].start()
    for i,t in enumerate(threads):
        t.join()
        msgs[i] = result[i]
    return msgs


recvPubkey = lambda param: serialization.load_pem_public_key(param)