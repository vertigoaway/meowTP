MeowTP!!!

too early to write a proper readme

client and server can transfer files bidirectionally
only difference is one initiates the other waits
library is general functions for meowTP both will use

default port is 6969 cause im awesome

handshake steps:
1. client sends "hand?"
2. server sends "hand" and attaches server public key
3. client sends "shake?" and attaches client public key
4. server sends "shake" encrypted as a confirmation

awful command names? yeah.