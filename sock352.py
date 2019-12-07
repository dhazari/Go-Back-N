import binascii
import socket as syssock
import struct
import sys
import random
import threading
import time

sock352PktHdrData = '!BBBBHHLLQQLL'
udpPortTx = -1   #this is the UDPportTX we get as input from client/server to the global init() function
udpPortRx = -1   #this is the UDPportTX we get as input from client/server to the global init() function
version = 0x1
opt_ptr = 0x0
protocol = 0x0
checksum = 0x0
source_port = 0x0
dest_port = 0x0
window = 0x0
header_len = 40
seqNum = 0
recAddress = ""
receivedData = ""
closeAddress = ""

DROP_PACKET_NO = 2
#MAX_PAYLOAD_SIZE = 64000 #delete this
SOCK352_SYN = 0x01
SOCK352_FIN = 0x02
SOCK352_ACK = 0x04
SOCK352_RESET = 0x08
SOCK352_SENTDATA = 0x23
#PACKET_SIZE = (MAX_PAYLOAD_SIZE + header_len) #delete this
type = ""
client = 1
server = 2
lastAck = -1
allAcknowledged = False
resend = False

def init(UDPportTx,UDPportRx):   # initialize your UDP socket here
    global udpSock, udpPortRx, udpPortTx
    udpSock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
    udpPortRx = int(UDPportRx)
    if(UDPportTx == ''):
        udpPortTx = int(UDPportRx)
    else:
        udpPortTx = int(UDPportTx)

    udpSock.bind(('', udpPortRx))
    udpSock.settimeout(0.2);
    pass

class socket:
    def updateStruct(self, newFlags, newHeader_len, newSeqNo, newAckNo, newPayloadLen):
        global version, opt_ptr, protocol, checksum, source_port, dest_port, window, udpSock
        flags = newFlags
        header_len = newHeader_len
        sequence_no = newSeqNo
        ack_no = newAckNo
        payload_len = newPayloadLen
        udpPkt_hdr_data = struct.Struct(sock352PktHdrData)
        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, sequence_no, ack_no, window, payload_len)

    def __init__(self):  # fill in your code here
        return

    def bind(self,address):
        return

    def connect(self,address):  # fill in your code here
        #Send SYN
        #Receive ACK
        #Receive SYN
        #Send ACK
        print("Attempting Connection")
        global udpSock, seqNum, header_len, type, udpPortTx
        type = client
        seqNum = int(random.randint(10, 500))
        data = self.updateStruct(SOCK352_SYN, header_len, seqNum, 0, 0)
        ackServer = -1;
        seqNumServer = 0;
        while True:
            print("Sent SYN to server")
            udpSock.sendto(data,(address[0],udpPortTx))
            serverData = self.getData()
            ackServer = serverData[9]
            if ackServer == seqNum + 1:
                seqNumServer = serverData[8] + 1
                print("Received SYN-ACK from server")
                break
            else:
                print("Failed to receive SYN-ACK")

        ackData = self.updateStruct(SOCK352_ACK, header_len, seqNum, seqNumServer, 0)
        udpSock.sendto(ackData, (address[0], udpPortTx))
        print("Sent ACK to server")

        udpSock.connect((address[0], udpPortTx))
        seqNum = seqNum + 1
        print("Connection Established")
        return

    def listen(self,backlog):
        return

    def accept(self):
        #Receive SYN
        #Send ACK
        #Send SYN
        #Receive ACK
        print("Attempting Connection")
        global udpSock, udpPortRx, seqNum, header_len, recAddress, type
        type = server
        updatedStruct = ""
        while(True):
            updatedStruct = self.getData()
            flag = updatedStruct[1]
            if(flag == SOCK352_SYN):
                print("Received SYN from client")
                seqNum = updatedStruct[8]
                break
        newSeqNum = int(random.randint(10, 500))
        struct = self.updateStruct(SOCK352_SYN + SOCK352_ACK, header_len, newSeqNum, seqNum+1, 8)
        udpSock.sendto(struct + "Accepted", recAddress)
        print("Sending SYN-ACK to client")

        while(True):
            updatedStruct = self.getData()
            if(updatedStruct[1] == SOCK352_ACK):
                print("Received ACK from client")
                seqNum = updatedStruct[8]
                break

        seqNum = seqNum+1
        print("Connection Established")
        (clientsocket, address) = (socket(), recAddress)  # change this to your code
        return (clientsocket,address)

    def getData(self):
        global udpSock, sock352PktHdrData, recAddress, receivedData, closeAddress
        try:
            (message, sendAddress) = udpSock.recvfrom(32500)
        except syssock.timeout:
            return[0,0,0,0,0,0,0,0,0,0,0,0]
        (head, body) = (message[:40], message[40:])
        newStruct = struct.unpack(sock352PktHdrData, head)
        if(head[1] == SOCK352_SYN or  SOCK352_ACK or SOCK352_SYN + SOCK352_ACK or SOCK352_FIN or SOCK352_FIN + SOCK352_ACK):
            closeAddress = sendAddress
            recAddress = sendAddress
            receivedData = body;
            return newStruct
        return newStruct

    def close(self):   # fill in your code here
        global type
        if(type == client):
            print("\nAttempting to disconnect from Server")
            self.closeClient()
        elif(type == server):
            print("\nAttemping to disconnect from Client")
            self.closeServer()
        return

    def closeClient(self):
        global udpSock, header_len, udpPortTx, recAddress, closeAddress
        #Send FIN
        #Receive ACK
        #Receive FIN
        #Send ACK
        closeNum = random.randint(10,500)
        FINstruct = self.updateStruct(SOCK352_FIN, header_len, closeNum, 0, 0)
        ackServer = -1
        closeNumServ = 0;
        while True:
            print("Sent FIN to server")
            udpSock.sendto(FINstruct, recAddress)
            serverData = self.getData()
            ackServer = serverData[9]
            if ackServer == closeNum + 1:
                closeNumServ = serverData[8] + 1
                print("Recieved FIN-ACK from server")
                break
            else:
                print("Failed to receive FIN-ACK")

        ackData = self.updateStruct(SOCK352_ACK, header_len, closeNum, closeNumServ, 0)
        udpSock.sendto(ackData, closeAddress)
        print("Sent ACK to server")
        udpSock.close()
        print("Disconnected Successfully")
        return


    def closeServer(self):
        #Receive FIN
        #Send ACK
        #Send FIN
        #Receive ACK
        global udpSock, udpPortRx, header_len, closeAddress
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
        FIN_ACKstruct = self.updateStruct(SOCK352_FIN + SOCK352_ACK, header_len, closeNum, updatedSeqNum + 1, 8)
        udpSock.sendto(FIN_ACKstruct + "Accepted", closeAddress)
        print("Sending FIN-ACK to client")

        while True:
            updateStruct = self.getData()
            if(updateStruct[1] == SOCK352_ACK):
                print("Received ACK from client")
                break
        udpSock.close()
        print("Disconnected Successfully")

        return

    def send(self,buffer):
        global seqNum, udpSock, lastAck
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
        global udpSock, seqNum, lastAck, allAcknowledged, resend
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
            newStruct = self.updateStruct(SOCK352_SENTDATA, header_len, seqNum, 0, currPayLoadLen)
            lock.acquire()
            if(resend == True):
                print("RESENT DROPPED PACKET seqNum: " + str(seqNum))
                resend = False
                lock.release()
                continue
            else:
                udpSock.send(newStruct+currPayLoad)
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
        global seqNum, udpSock, receivedData, recAddress
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
                ###print("now going in infinite loop: seqNum = " + str(seqNum) + " recvSeqNum = " + str(recvSeqNum))
            #at this point, we received the correct seqNum, so we must send and ack for it
            #also increment the counter
            dropped = random.randint(1,100)
            # if(dropped < 30):                                  #UTILIZE THIS TO TESST DROPS
            #     continue                                       #APPROX 30% DROPPED
            newStruct = self.updateStruct(SOCK352_ACK, header_len, 0, seqNum,0)
            udpSock.sendto(newStruct, recAddress)
            counter += len(receivedData)
            finalData += receivedData
            seqNum += 1
        return finalData
