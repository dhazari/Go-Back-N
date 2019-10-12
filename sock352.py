
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

seqNum = 0

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

        #TrueorFalse
        self.connected = False
        self.server = False
        return
    
    def bind(self,address):
        return 

    def connect(self,address): 
        self.server = False
        global header
        
        #generate random number
        seqNum = random.randint(1,100)

        #Create header
        header = self.create_header(SOCK352_SYN, seqNum, 0, 0, 0)

        #send old info and recieve updted info from client to server and vice versa till info is recieved
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

        #unpack recieved data to test flags for rejection/acceptance
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
        self.server= True
        global connect_response
        
        #remove timeout so there is time to nter info on client side
        self.sock.settimeout(None)

        #recieve info from client
        (header, self.address) = self.sock.recvfrom(int(header_len))

        #unpack info so you can maipulate sequence nuber and acknowledgement number
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

        #create new header and send it to client with updated information
        connect_response = self.create_header(flag, seqNum, ackNum, 0, 0)
        self.sock.sendto(connect_response,('localhost', self.address[1]))
        print("Response sent")

        return self,self.address
    
    def close(self):
        
        #Set data to have Fin
        header = create_header(SOCK352_FIN,seqNum+1,0,0,0)
        
        #Send data with cancelation flag
        acknowledge = False
        while not acknowledge:
            try:
                if (self.server):
                    self.sock.sendto(header,(self.address[0],transmitter))
                else:
                    self.sock.sendto(header,('localhost', self.address[1]))
                print("Data sent")
                data = self.sock.recvfrom(header_len)[0]
                acknowledge = True
            except syssock.timeout:
                print("Timed out, resending")
                pass
        
        #Chack if flags recieved are FIN and ACK 
        self.newHeader = struct.unpack(sock352PktHdrData, data)
        flag = self.newHeader[1]  
            
        if(flag==SOCK352_FIN):
            header = create_header(SOCK352_ACK,seqNum+1,0,0,0)
            self.sock.close()
        else:
            pass
            
        return 

    def send(self,buffer):
    
        #get length of bytes to be sent
        #bytessent = 0
        #length = len(buffer)
        
       # msgHeader = create_header(0, seqNum, 0, 0, length)
        
        #acknowledge = False
        #while not acknowledge:
         #   try: 
          #      bytessent = self.sock.sendto((msgHeader+buffer),(address[0],transmitter))
           #     print("Data sent")
           #     data = self.sock.recvfrom(header_len)[0]
            #    acknowledge = True
          #  except syssock.timeout:
           #     print("Timed out, resending")
            #    pass
                
        #self.newHeader = struct.unpack(sock352PktHdrData, data)
        #if((newHeader[1] = SOCK352_ACK) and (seqNum = newHeader[8]))
        
        #inform reciever of how many bytes were sent
        return 100

    def recv(self,nbytes):
    
       # bytesreceived = 0  
        
       # while(nbytes>0):
       #     (header, self.address) = self.sock.recvfrom(int(header_len))
            
            
        
        
        return 100

    def create_header (self, flags, seqNumbo, ackNum, window, payLoad):

        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0

        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, seqNumbo, ackNum, window, payLoad)
        


    


