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

#global seqNum to tell which the correct seqNum is
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
    
        #setting up current socket
        self.sock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
        
        #Binding to client
        self.sock.bind(('',receiving))
        
        #Setting timeout for future calls
        self.sock.settimeout(0.2)

        #TrueorFalse
        self.connected = False
        self.server = False
        
        self.servAddr = None
        self.clientAddr = None
        return
    
    def bind(self,address):
        return 

    def connect(self,address): 
        global seqNum
        self.servAddr = (address[0],transmitter)
        
        #Currently is the client
        self.server = False
        
        #generate random number
        seqNum = random.randint(1,100)

        #Create header
        header = self.create_header(SOCK352_SYN, seqNum, 0, 0, 0)

        #send old info and recieve updted info from client to server and vice versa till info is recieved
        flag = 0
        while (flag != SOCK352_SYN | SOCK352_ACK):
            try:
                self.sock.sendto(header,(address[0],transmitter))
                print("Connection request sent from client to server")
                data = self.sock.recvfrom(header_len)[0]
                
                #unpack recieved data to test flags for rejection/acceptance
                self.newHeader = struct.unpack(sock352PktHdrData, data)
                flag = self.newHeader[1]
                
            except syssock.timeout:
                print("Timed out, resending")
                pass

        if(flag == SOCK352_SYN | SOCK352_ACK):
            print("Connection Recieved")
            print("Connect sequence number: ", seqNum)
            pass
        elif (flag == SOCK352_RESET):
            print("Connection Rejected")
            print("Connect sequence number: ", seqNum)
            pass
        else:
            print("error")
        
        #send acknowledgement to server
        ackNum = seqNum+1
        
        try:
            header = self.create_header(SOCK352_ACK, 0, ackNum, 0, 0)
            self.sock.sendto(header,(address[0],transmitter))
            print("Acknowledgement sent to server")
        except syssock.timeout:
                print("Timed out, resending")
                pass

        return 
    
    def listen(self,backlog):
        return

    def accept(self):
        global connect_response, seqNum
    
        #Currntly on server because accept call
        self.server= True
        
        #remove timeout so there is time to enter info on client side
        self.sock.settimeout(None)

        #recieve info from client
        (header, self.clientAddress) = self.sock.recvfrom(int(header_len))
        self.clientAddr = ('localhost', self.clientAddress[1])

        #unpack info so you can maipulate sequence nuber and acknowledgement number
        self.newHeader = struct.unpack(sock352PktHdrData, header)

        if(self.newHeader[1] == SOCK352_SYN):
            print("SYN recieved")
            if self.connected:
                flag = SOCK352_RESET
                seqNum +=1
                ackNum = self.newHeader[8]+1
            else:
                flag = SOCK352_ACK | SOCK352_SYN
                ackNum = seqNum+1
                seqNum = random.randint(1,100)
                self.connected = True
            
        print("Accept sequence number: ", seqNum, self.connected, ackNum)

        #create new header and send it to client with updated information
        connect_response = self.create_header(flag, seqNum, ackNum, 0, 0)
        self.sock.sendto(connect_response,('localhost', self.clientAddress[1]))
        print("Connection response sent from server to client")        
        
        #recieve acknowledgement fro client
        data = self.sock.recvfrom(header_len)[0]
        self.newHeader = struct.unpack(sock352PktHdrData, data)
        
        if(self.newHeader[1] == SOCK352_ACK):
            print("Acknowledgement recieved")
        else:
            print("Acknowledgement flag not set")

        return self,self.clientAddress
    
    def close(self):
    
        global seqNum
    
        #increment sequence number
        seqNum+=1
        
        #Set data to have Fin
        header = self.create_header(SOCK352_FIN,seqNum,0,0,0)
        
        #Send data with cancelation flag
        data = None
        acknowledge = False
        while not acknowledge:
            try:
                if (self.server):
                    self.sock.sendto(header,self.clientAddr)
                    print("Acknowledgement to close sent to client")
                else:
                    self.sock.sendto(header,self.servAddr)
                    print("Acknowledgement to close sent to server")
                data = self.sock.recvfrom(header_len)[0]
                acknowledge = True
            except syssock.timeout:
                print("Timed out, resending")
                pass
        
        #Chack if flags recieved are FIN and ACK 
        self.newHeader = struct.unpack(sock352PktHdrData, data)
        flag = self.newHeader[1]  
        
        #Flag is set to ACK flag if it responds with ACK (data!=None) and FIN (flag)
        if(flag==SOCK352_FIN):
            header = self.create_header(SOCK352_ACK,seqNum,0,0,0)
            print("Closing packet")
            self.sock.close()
        else:
            print("Wrong flags recieved")
            pass
            
        return 

    def send(self,buffer):
    
        global seqNum
    
        #get length of bytes to be sent
        bytessent = 0
        length = len(buffer)
        
        #Start to send the message
        while(length>0):
        
            package = buffer[:64000]
        
            #Create message header for this package
            pckgHeader = self.create_header(0, seqNum, 0, 0, length)
            
            #Declare temp variables
            tempBytes = 0
            tempAckFlag = -2
            
            print(seqNum)
            
            #Start the loop of sending the correct packet
            while(tempAckFlag != seqNum):
                
                #try sending and recieving the data
                try:
                    tempBytes = self.sock.sendto((pckgHeader+package),self.servAddr)
                    print("Data has been sent from client to server")
                    (data,address) = self.sock.recvfrom(header_len)
                except syssock.timeout:
                    print("Timed out")
                    pass
                
                #get the new header
                self.newHeader = struct.unpack(sock352PktHdrData, data)
                tempAckFlag = self.newHeader[9]
                
            length -= 64000
            buffer = buffer[6400:]
            bytessent+= tempBytes
            seqNum+=1
 
        return bytes(bytessent)

    def recv(self,nbytes):
    
        global seqNum

        message = "" 
            
        while(nbytes>0):

            tempSeqNum = -1

            while(tempSeqNum != seqNum):
                
                data = self.sock.recvfrom(header_len)[0]
                self.newHeader = struct.unpack(sock352PktHdrData, data)
                tempSeqNum = self.newHeader[8]
                
                print("recv Temp Sequence Number: ",tempSeqNum)
                print("recv Sequence Number: ",seqNum)
                
                if(tempSeqNum != seqNum):
                    print("Incorrect sequence order, get next packet")
                    
                header = self.create_header(SOCK352_ACK, 0, tempSeqNum, 0, 0)
                tempBytes = self.sock.sendto(header,self.clientAddr)
              
            message += self.newHeader[header_len:]
            nbytes-= len(newHeader[header_len:]) 
            seqNum+=1
            
        print(message)   
        
        return bytes(message)

    def create_header (self, flags, seqNumbo, ackNum, window, payLoad):

        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0

        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, seqNumbo, ackNum, window, payLoad)
        


    


