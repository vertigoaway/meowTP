MeowTP!!!

too early to write a proper readme

client and server can transfer files bidirectionally
only difference is one initiates the other waits
library is general functions for meowTP both will use

default port is 6969 cause im awesome

handshake steps:
1. client sends "reqKey"
2. server sends "reqKey" and attaches server public key
3. client sends "sndKey" and attaches client public key
4. server sends "finKey" encrypted as a confirmation

awful command names? yeah.