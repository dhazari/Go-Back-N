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

SOCK352_SYN = 0x01
SOCK352_FIN = 0x02
SOCK352_ACK = 0x04
SOCK352_RESET = 0x08
SOCK352_HAS_OPT = 0xA0
SOCK352_DATA = 0x23

PACKET_SIZE = 32000
isClient = False

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
      
        recAddress = ""
        receivedData = ""
        closeAddress = ""
        prevAck = -1
        allAck = False
        retransmit = False
        bufferLen = ""
        return

    def bind(self,address):
        return

    def connect(self,address):
    
        global sock, seqNum, header_len, isClient, transmitter
        
        #Is currently client
        print("Attempting Connection")
        isClient = True
        
        #generate random number
        seqNum = int(random.randint(1, 100))
        
        #create header
        data = self.create_header(SOCK352_SYN, header_len, seqNum, 0, 0,0)
        
        #set temp seq and ack variables
        tempAck = -1;
        tempSeq = 0;
        
        #send old info and recieve updted info from client to server and vice versa till info is recieved
        while True:
            print("Connection request sent from client to server")
            
            sock.sendto(data,(address[0],transmitter))
            serverData = self.getData()
            
            #test flags for rejection/acceptance
            tempAck = serverData[9]
            if tempAck == seqNum + 1:
                tempSeq = serverData[8] + 1
                print("Connection Recieved")
                break
            else:
                print("Connection Rejected")
        
        #send acknowledgement to server
        ackData = self.create_header(SOCK352_ACK, header_len, seqNum, tempSeq, 0,0)
        sock.sendto(ackData, (address[0], transmitter))
        print("Acknowledgement sent to server")

        sock.connect((address[0], transmitter))
        seqNum += 1
        print("Connected")
        return

    def listen(self,backlog):
        return

    def accept(self):
        
        global sock, reciever, seqNum, header_len, recAddress, isClient
        
        print("Attempting to connect to server ")

        
        #is currently the server
        isClient = False
        updatedStruct = ""
        
        #recieve info from client
        while(True):
            updatedStruct = self.getData()
            flag = updatedStruct[1]
            
            if(flag == SOCK352_SYN):
                print("SYN received")
                seqNum = updatedStruct[8]
                break
        
        #set new sequence number and increment ackNumber by 1 of og seqNum       
        newSeqNum = int(random.randint(1, 100))
        struct = self.create_header(SOCK352_SYN | SOCK352_ACK, header_len, newSeqNum, seqNum+1, 8, 0)
        sock.sendto(struct, recAddress)
        print("Connection response sent from server to client")

        #recieve acknowledgement flag from client
        while(True):
            updatedStruct = self.getData()
            if(updatedStruct[1] == SOCK352_ACK):
                print("Acknowledgement recieved")
                seqNum = updatedStruct[8]
                break
            else:
                print("Acknowledgement flag not set")

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
        if(head[1] == SOCK352_SYN or SOCK352_ACK or (SOCK352_SYN | SOCK352_ACK) or SOCK352_FIN or (SOCK352_FIN | SOCK352_ACK)):
            closeAddress = sendAddress
            recAddress = sendAddress
            receivedData = body;
            
        return newStruct

    def close(self):
        global isClient, sock, header_len, transmitter, recAddress, closeAddress
        
        if(isClient):
            print("Disconnect from Server")
            
            #generate random temp seqNum
            closeNum = random.randint(1,100)
            headerFile = self.create_header(SOCK352_FIN, header_len, closeNum, 0, 0, 0)
            
            #temp ack and seq num
            tempAck = -1
            closeNumServ = 0;
            
            while True:
                #send FIN flag
                sock.sendto(headerFile, recAddress)
                print("FIN flag to close sent to server")
                
                serverData = self.getData()
                tempAck = serverData[9]
                if tempAck == closeNum + 1:
                    closeNumServ = serverData[8] + 1
                    print("FIN-ACK flag recieved")
                    break
                else:
                    print("FIN-ACK flag not sent")
            
            #send acknowledgement to close
            ackData = self.create_header(SOCK352_ACK, header_len, closeNum, closeNumServ, 0, 0)
            sock.sendto(ackData, closeAddress)
            print("Acknowledgement to close sent to server")
            sock.close()
            print("Closed connection")
            return
            
        else:
            print("Disconnect from Client")
            
            #temp seqNum
            updatedStruct = ""
            updatedSeqNum = 0
            
            while(True):
                updatedStruct = self.getData()
                flag = updatedStruct[1]
                if(flag == SOCK352_FIN):
                    print("FIN flag to close sent to client")
                    updatedSeqNum = updatedStruct[8]
                    break
            
            #temp seq Num to recieve fin|Ack flag        
            closeNum = int(random.randint(1, 100))
            temp_header = self.create_header(SOCK352_FIN | SOCK352_ACK, header_len, closeNum, updatedSeqNum + 1, 8, 0)
            sock.sendto(temp_header, closeAddress)
            print("FIN-ACK flag rsent")
            
            #recieve acknowledgement
            while True:
                header = self.getData()
                if(header[1] == SOCK352_ACK):
                    print("Acknowledgement to close revieved")
                    break
            sock.close()
            print("Closed")
            
        return

    def send(self,buffer):
    
        global seqNum, sock, prevAck
        prevAck = -1
        seqNum = 0

	    #create two threads for sending the actual packets, and for sending back the actual acks, as suggested
        lock = threading.Lock()
        sendDataThread = threading.Thread(target = self.sendData, args=(lock, buffer))
        ackDataThread = threading.Thread(target = self.ackData, args=(lock, buffer))

	    #start thread to send data, and then start thread to ack data
        sendDataThread.start()
        ackDataThread.start()
	
	    #block until both return -- if packet lost, retransmit 
        sendDataThread.join()
	    #do not continue until all packets retransmitted, all subsequent ACKs return
        ackDataThread.join()

	    #return total bytes correctly sent
        bytessent = len(buffer)
        return bytessent

    def sendData(self, lock, buffer):

        #get current index + packet size until all data from 0-packet size has been accounted for
        finalData = [buffer[i:i+PACKET_SIZE] for i in range(0, len(buffer), PACKET_SIZE)]        

        global sock, seqNum, prevAck, allAck, retransmit

        #set retransmit to false initially, update if resent necessary	
        retransmit = False

        #default all packets have not been sent initially        
        allAck = False
        
        while(allAck == False):
        #if not all of the data has been sent, we stop and retransmit
        #else, we keep going to get all data
        #we stop once either seqnum is changed or until all of the packets have been ackd
            if(seqNum == len(finalData)):
                continue

            currPayLoad = finalData[seqNum]
            currPayLoadLen = len(currPayLoad)

            newStruct = self.create_header(SOCK352_DATA, header_len, seqNum, 0, currPayLoadLen, 0)
            lock.acquire()
            #block until retransmit completes
            if(retransmit == True):
                #ack not received, must retransmit
                print("Resending dropped packet")

                #no longer need to retransmit dropped frame, udpate and stop blocking
                retransmit = False 
                lock.release()
                continue
            else:
                sock.send(newStruct+currPayLoad)
                seqNum += 1
                lock.release()
        pass

    def ackData(self, lock, buffer):
        global seqNum, prevAck, allAck, retransmit

        finalData = [buffer[i:i+PACKET_SIZE] for i in range(0, len(buffer), PACKET_SIZE)]
        #set initial time        
        t0 = time.time()

        while True:
            newStruct = self.getData()
            #if(newStruct[10]<=0):
                #print("Hi!", newStruct[10])
                #continue;
            #retrive data from packet being sent
            if(newStruct[0] == 0 and time.time() >= t0+0.2):
                lock.acquire()
                #lock data while thread runs, do not finish until all data has been sent

                retransmit = True
                #send packet from last ACK, set timer
                seqNum = prevAck+1
                
                t0 = time.time()
                lock.release()

            elif(newStruct[0] != 0):
                prevAck = newStruct[9]
                if(prevAck == len(finalData)-1):
                    #break at end
                    break
        allAck = True
        pass

    def recv(self,nbytes):
        global seqNum, sock, receivedData, recAddress, bufferLen
        
	    #get sequence number from incoming packet, update accordingly
        seqNum = 0
        receivedData = ""
        finalData = ""
        counter = 0
        bufferLen = ""
	
        while(counter != nbytes):
	    #initialize sequence number received as -1 (no data yet)
            recvSeqNum = -1
            while(recvSeqNum != seqNum): 
                newStruct = self.getData()
                #buffer
		        #received sequence number acquired, contains actual data from packet
                #update received seq num to reflect packet num sent in
                recvSeqNum = newStruct[8]
                
            #bufferLen += receivedData
            #total_len = len(bufferLen)
            

            #create ACK 
            #window_size = 262000-total_len  
            window_size = 0                   
            newStruct = self.create_header(SOCK352_ACK, header_len, 0, seqNum,0, window_size)
            sock.sendto(newStruct, recAddress)
                
	        #send ACK, update how much data has been received
            counter += len(receivedData)
            finalData += receivedData
            
            #if total_len>=262000:
                #return bufferLen

	        #increase sequence number for next packet
            seqNum += 1
            
        return finalData
        
    def create_header(self, newFlags, newHeader_len, newSeqNo, newAckNo, newPayloadLen, windowLen):
        global sock
        
        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0
        
        window = windowLen
        flags = newFlags
        header_len = newHeader_len
        sequence_no = newSeqNo
        ack_no = newAckNo
        payload_len = newPayloadLen
        
        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, sequence_no, ack_no, window, payload_len)
