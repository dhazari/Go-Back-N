import binascii
import socket as syssock
import struct
import sys
import random
import threading
import time

sock352PktHdrData = '!BBBBHHLLQQLL'
udpPkt_hdr_data = struct.Struct(sock352PktHdrData)  
header_len = 40
seqNum = 0
recAddress = ""
receivedData = ""
closeAddress = ""

SOCK352_SYN = 0x01
SOCK352_FIN = 0x02
SOCK352_ACK = 0x04
SOCK352_RESET = 0x08
SOCK352_HAS_OPT = 0xA0
SOCK352_DATA = 0x23

PACKET_SIZE = 32000
type = ""
client = 1
server = 2

lastAck = -1
allAcknowledged = False
resend = False

def init(UDPportTx,UDPportRx):

    global sock, reciever, transmitter
    sock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
    reciever = int(UDPportRx)
    
    if(UDPportTx == ''):
        transmitter = int(UDPportRx)
    else:
        transmitter = int(UDPportTx)

    sock.bind(('', reciever))
    sock.settimeout(0.2);
    
    pass

class socket:

    def __init__(self):
        return

    def bind(self,address):
        return

    def connect(self,address):
    
        global sock, seqNum, header_len, type, transmitter
        
        print("Attempting Connection")
        type = client
        seqNum = int(random.randint(1, 100))
        
        data = self.create_header(SOCK352_SYN, header_len, seqNum, 0, 0)
        
        ackServer = -1;
        seqNumServer = 0;
        
        while True:
            print("Sent SYN to server")
            
            sock.sendto(data,(address[0],transmitter))
            serverData = self.getData()
            
            ackServer = serverData[9]
            if ackServer == seqNum + 1:
                seqNumServer = serverData[8] + 1
                print("Received SYN-ACK from server")
                break
            else:
                print("Failed to receive SYN-ACK")

        ackData = self.create_header(SOCK352_ACK, header_len, seqNum, seqNumServer, 0)
        sock.sendto(ackData, (address[0], transmitter))
        print("Sent ACK to server")

        sock.connect((address[0], transmitter))
        seqNum = seqNum + 1
        print("Connection Established")
        return

    def listen(self,backlog):
        return

    def accept(self):
    
        print("Attempting to connect to server ")
        
        global sock, reciever, seqNum, header_len, recAddress, type
        type = server
        updatedStruct = ""
        
        while(True):
            updatedStruct = self.getData()
            flag = updatedStruct[1]
            if(flag == SOCK352_SYN):
                print("Received SYN from client")
                seqNum = updatedStruct[8]
                break
                
        newSeqNum = int(random.randint(1, 100))
        struct = self.create_header(SOCK352_SYN | SOCK352_ACK, header_len, newSeqNum, seqNum+1, 8)
        sock.sendto(struct + "Accepted", recAddress)
        print("Sending SYN-ACK to client")

        while(True):
            updatedStruct = self.getData()
            if(updatedStruct[1] == SOCK352_ACK):
                print("Receive ACK from client")
                seqNum = updatedStruct[8]
                break

        seqNum = seqNum+1
        print("Connection Established")
        
        (clientsocket, address) = (socket(), recAddress)
        return (clientsocket, address)

    def getData(self):
        global sock, sock352PktHdrData, recAddress, receivedData, closeAddress
        
        try:
            (message, sendAddress) = sock.recvfrom(32500)
        except syssock.timeout:
            return[0,0,0,0,0,0,0,0,0,0,0,0]
            
        (head, body) = (message[:40], message[40:])
        
        newStruct = struct.unpack(sock352PktHdrData, head)
        if(head[1] == SOCK352_SYN or  SOCK352_ACK or SOCK352_SYN + SOCK352_ACK or SOCK352_FIN or SOCK352_FIN | SOCK352_ACK):
            closeAddress = sendAddress
            recAddress = sendAddress
            receivedData = body;
            return newStruct
            
        return newStruct

    def close(self):
        global type
        if(type == client):
            print("\nAttempting to disconnect from Server")
            self.closeClient()
        elif(type == server):
            print("\nAttemping to disconnect from Client")
            self.closeServer()
        return

    def closeClient(self):
        global sock, header_len, transmitter, recAddress, closeAddress
        
        closeNum = random.randint(1,100)
        FINstruct = self.create_header(SOCK352_FIN, header_len, closeNum, 0, 0)
        ackServer = -1
        closeNumServ = 0;
        
        while True:
            print("Sent FIN to server")
            sock.sendto(FINstruct, recAddress)
            serverData = self.getData()
            ackServer = serverData[9]
            if ackServer == closeNum + 1:
                closeNumServ = serverData[8] + 1
                print("Recieved FIN-ACK from server")
                break
            else:
                print("Failed to receive FIN-ACK")

        ackData = self.create_header(SOCK352_ACK, header_len, closeNum, closeNumServ, 0)
        sock.sendto(ackData, closeAddress)
        print("Sent ACK to server")
        sock.close()
        print("Disconnected Successfully")
        return


    def closeServer(self):
        global sock, reciever, header_len, closeAddress
        updatedStruct = ""
        updatedSeqNum = 0
        while(True):
            updatedStruct = self.getData()
            flag = updatedStruct[1]
            if(flag == SOCK352_FIN):
                print("Recieved FIN from client")
                updatedSeqNum = updatedStruct[8]
                break
        closeNum = int(random.randint(10, 500))
        FIN_ACKstruct = self.create_header(SOCK352_FIN + SOCK352_ACK, header_len, closeNum, updatedSeqNum + 1, 8)
        sock.sendto(FIN_ACKstruct + "Accepted", closeAddress)
        print("Sending FIN-ACK to client")

        while True:
            create_header = self.getData()
            if(create_header[1] == SOCK352_ACK):
                print("Received ACK from client")
                break
        sock.close()
        print("Disconnected Successfully")

        return

    def send(self,buffer):
        global seqNum, sock, lastAck
        lastAck = -1
        seqNum = 0

        lock = threading.Lock()
        sendDataThread = threading.Thread(target = self.sendData, args=(lock, buffer))
        ackDataThread = threading.Thread(target = self.ackData, args=(lock, buffer))

        sendDataThread.start()
        ackDataThread.start()

        sendDataThread.join()
        ackDataThread.join()

        bytessent = len(buffer)     # fill in your code here
        return bytessent

    def sendData(self, lock, buffer):
        global sock, seqNum, lastAck, allAcknowledged, resend
        allAcknowledged = False
        resend = False
        finalData = [buffer[i:i+PACKET_SIZE] for i in range(0, len(buffer), PACKET_SIZE)]
        while(allAcknowledged == False):
            if(seqNum == len(finalData)):
                #the idea here is that incase seqNum == len(finalData) meaning,
                #all data is sent as of now, then we will keep iterating through
                #the while loop untill allAcknowledged is true or until seqNum is changed (when some packet is dropped)
                continue
            currPayLoad = finalData[seqNum]
            currPayLoadLen = len(currPayLoad)
            newStruct = self.create_header(SOCK352_DATA, header_len, seqNum, 0, currPayLoadLen)
            lock.acquire()
            if(resend == True):
                print("RESENT DROPPED PACKET seqNum: " + str(seqNum))
                resend = False
                lock.release()
                continue
            else:
                sock.send(newStruct+currPayLoad)
                seqNum += 1
                lock.release()
        pass

    def ackData(self, lock, buffer):
        global seqNum, lastAck, allAcknowledged, resend
        finalData = [buffer[i:i+PACKET_SIZE] for i in range(0, len(buffer), PACKET_SIZE)]
        t0 = time.time()
        while True:
            newStruct = self.getData()
            if(newStruct[0] == 0 and time.time() >= t0+0.2):
                lock.acquire()
                resend = True
                seqNum = lastAck+1
                t0 = time.time()
                lock.release()
            elif(newStruct[0] != 0):
                lastAck = newStruct[9]
                if(lastAck == len(finalData)-1):
                    break
        allAcknowledged = True
        pass

    def recv(self,nbytes):
        global seqNum, sock, receivedData, recAddress
        seqNum = 0
        receivedData = ""
        finalData = ""
        counter = 0
        sent5 = False
        while(counter != nbytes):
	    
            recvSeqNum = -1
            while(recvSeqNum != seqNum):
                newStruct = self.getData()
                #at this point, receivedData is loaded with the actual data
                recvSeqNum = newStruct[8]
                
            dropped = random.randint(1,100)
                                             
            newStruct = self.create_header(SOCK352_ACK, header_len, 0, seqNum,0)
            sock.sendto(newStruct, recAddress)
            counter += len(receivedData)
            finalData += receivedData
            seqNum += 1
        return finalData
        
    def create_header(self, newFlags, newHeader_len, newSeqNo, newAckNo, newPayloadLen):
        global sock
        
        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0
        window = 0x0
        
        flags = newFlags
        header_len = newHeader_len
        sequence_no = newSeqNo
        ack_no = newAckNo
        payload_len = newPayloadLen
        
        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, sequence_no, ack_no, window, payload_len)
