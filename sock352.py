
import binascii
import socket as syssock
import struct
import sys

import random

# these functions are global to the class and
# define the UDP ports all messages are sent
# and received from

SOCK352_SYN = 0x01
SOCK352_ACK = 0x04
SOCK352_FIN = 0x02
SOCK352_RESET = 0x08
SOCK352_HAS_OPT = 0xA0

sock352PktHdrData = "!BBBBHHLLQQLL"
udpPkt_hdr_data = struct.Struct(sock352PktHdrData)

header_len = struct.calcsize(sock352PktHdrData)

def init(UDPportTx,UDPportRx):

    global receiving
    global transmitter

    receiving = int(UDPportRx)
    transmitter = int(UDPportTx)

    pass 
    
class socket:
    
    def __init__(self):
    
        self.sock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
        
        self.sock.bind(('',receiving))
        
        self.sock.settimeout(0.2)

        self.connected = False
        return
    
    def bind(self,address):
        return 

    def connect(self,address): 
        global header
        
        seqNum = random.randint(1,100)

        header = self.create_header(SOCK352_SYN, seqNum, 0, 0, 0)

        acknowledge = False
        while not acknowledge:
            try:
                self.sock.sendto(header,(address[0],transmitter))
                print("Data sent")
                data = self.sock.recvfrom(header_len)[0]
                acknowledge = True
            except syssock.timeout:
                print("Timed out, resending")
                pass

        self.newHeader = struct.unpack(sock352PktHdrData, data)
        flag = self.newHeader[1]

        if(flag == SOCK352_SYN | SOCK352_ACK):
            print("Connection Recieved")
            pass
        elif (flag == SOCK352_RESET):
            print("Connection rejected")
            pass
        else:
            print("error")

        return 
    
    def listen(self,backlog):
        return

    def accept(self):

        global connect_response
        
        self.sock.settimeout(None)

        (header, self.address) = self.sock.recvfrom(int(header_len))

        self.newHeader = struct.unpack(sock352PktHdrData, header)

        if self.connected:
            flag = SOCK352_RESET
            seqNum = self.newHeader[8]
            ackNum = self.newHeader[8]+1
        else:
            flag = SOCK352_ACK | SOCK352_SYN
            seqNum = random.randint(1,100)
            ackNum = self.newHeader[8]+1
            self.connected = True

        connect_response = self.create_header(flag, seqNum, ackNum, 64000, 0)

        self.sock.sendto(connect_response,('localhost', self.address[1]))

        print("Response sent")

        return self,self.address
    
    def close(self):   # fill in your code here 
        return 

    def send(self,buffer):
        bytessent = 0     # fill in your code here 
        return bytesent 

    def recv(self,nbytes):
        bytesreceived = 0     # fill in your code here
        return bytesreceived 

    def create_header (self, flags, seqNum, ackNum, window, payLoad):

        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0

        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, seqNum, ackNum, window, payLoad)
        


    


