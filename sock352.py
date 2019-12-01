import binascii
import socket as syssock
import struct
import sys
import thread
import random
import time

receiver = -1
transmitter = -1
sock352PktHdrData = "!BBBBHHLLQQLL"
udpPkt_hdr_data = struct.Struct(sock352PktHdrData)
header_len = struct.calcsize(sock352PktHdrData)
ackNum = None
seqNum = None
fin_received = False
error = False
other_address = None
last_acked = 0
data_to_return = ''
finished = False
FRAGMENT_SIZE = 63960

SYN = 0x01
DATA = 0x03
FIN = 0x02
ACK = 0x04
RESET = 0x08
HAS_OPT = 0xA0


# these functions are global to the class and
# define the UDP ports all messages are sent
# and received from

def init(UDPportTx, UDPportRx):  # initialize your UDP socket here
    global receiver, transmitter
    receiver = int(UDPportRx)
    transmitter = int(UDPportTx)


class socket:
    sock = None

    def __init__(self):
        global sock
        sock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
        sock.bind(('', receiver))
        print('Socket initialized')
        
        self.connected = False
        return

    def bind(self, address):
        return

    def connect(self, address):
        global seqNum, ackNum, other_address
        
        #other_address is the server_address
        other_address = (address[0], transmitter)
        
        #generate random number
        seqNum = random.randint(1,100)
        
        #create header
        s_header = self.create_header(SYN, seqNum, 0, 0)
        sock.sendto(s_header, other_address)
        print("Connection request sent from client to server")
        
        #Recieve Connection
        packet = sock.recv(header_len)
        r_header = struct.unpack(sock352PktHdrData, packet)
        if SYN == r_header[1] and seqNum == r_header[9]:
            ackNum = r_header[8]
            print("Connection Recieved")
        else:
            print("Connection Rejected")
            
        #send acknowledgement to server
        try:
            header = self.create_header(ACK, seqNum, ackNum, 0)
            sock.sendto(header,other_address)
            print("Acknowledgement sent to server")
        except syssock.timeout:
            print("Timed out, resending")
            pass
        return

    def listen(self, backlog):
        return

    def accept(self):
        global seqNum, ackNum, other_address
        
        #recieve info from client
        (r_packet, address) = sock.recvfrom(header_len)
        other_address = (address[0], transmitter)
        
        #unpack info so you can maipulate sequence nuber and acknowledgement number
        r_header = struct.unpack(sock352PktHdrData, r_packet)
        
        if (SYN == r_header[1]):
            print("SYN recieved")
            if self.connected:
                flag = RESET
                seqNum = r_header[8]+1
                ackNum = sr_header[8]
            else:
                flag = ACK | SYN
                ackNum = r_header[8]
                seqNum = random.randint(1,100)
                self.connected = True
                
            s_header = self.create_header(SYN, seqNum, ackNum, 0)
            sock.sendto(s_header, other_address)
            print("Connection response sent from server to client")  
        else:
            sys.exit('SYN flag missing')
            
        #recieve acknowledgement fro client
        data = sock.recvfrom(header_len)[0]
        r_header = struct.unpack(sock352PktHdrData, data)
        
        if(r_header[1] == ACK):
            print("Acknowledgement recieved")
        else:
            print("Acknowledgement flag not set")
            
        print('Successfully accepted connection')
        return self, other_address

    def close(self):
        global sock
        print("Closing . . .")
        sock.close()

    def send(self, buffer):
        print("Starting send . . .")
        global last_acked, finished
        
        last_acked = 0
        packets = list()
        
        fragments = 0
        remainder = 0
        size = len(buffer)
        finished = False      
        bytes_sent = 0
        go_back_n = False
        fragment = 0
        i = 0
        start = 0
     
        #Calculate how many fragements to sent
        if size > FRAGMENT_SIZE:
            fragments = len(buffer) / FRAGMENT_SIZE
            remainder = len(buffer) % FRAGMENT_SIZE
            size = FRAGMENT_SIZE

        while i <= fragments or go_back_n:
            total_sent = 0

            if go_back_n:
                i = last_acked + 1
                print("Go back n")
                size = len(packets[i])
                go_back_n = False

            elif fragments > 0:

                if i == fragments and remainder > 0:
                    size = remainder
                    fragment = buffer[bytes_sent:]

                elif i == fragments and remainder == 0:
                    break

                else:
                    fragment = buffer[bytes_sent:(bytes_sent + FRAGMENT_SIZE)]
            else:
                fragment = buffer[:]

            if i == len(packets):
                header = self.create_header(DATA, i, 0, size)
                packets.append(header+fragment)

            while total_sent < len(packets[i]):
                sent = sock.sendto((packets[i])[total_sent:], other_address)
                if sent == 0:
                    raise RuntimeError("socket broken")
                else:
                    print('Sent ' + str(sent) + 'bytes')
                    total_sent += sent

            if i >= last_acked:
                bytes_sent += total_sent - header_len

            if start:

                if last_acked == i - 1 or last_acked == i:
                    start = time.time()
                elif last_acked > i:
                    i = last_acked
                elif last_acked < i - 1 and time.time() - start >= 0.2:
                    go_back_n = True

            else:
                start = time.time()
                thread.start_new_thread(self.__receive, ())

            i += 1

        finished = True
        return bytes_sent

    def __receive(self):
        print("Started receiving ack packets for send . . .")
        global last_acked
        while not finished:
            r_header = sock.recv(header_len)
            header = struct.unpack(sock352PktHdrData, r_header)
            last_acked = header[9]
        return

    def recv(self, nbytes):
    
        print('Receiving' + str(nbytes) + 'bytes')
        
        i = 0
        fragments = 0
        remainder = 0
        finalMsg = ""
        
        if nbytes > FRAGMENT_SIZE:
            fragments = nbytes / FRAGMENT_SIZE
            remainder = nbytes % FRAGMENT_SIZE
            
        if fragments == 0:
            fragement = sock.recv(nbytes+header_len)
            msg = fragement[header_len:]
            finalMsg = msg
            
        while i < fragments:
        
            fragment = ''
            size = FRAGMENT_SIZE + header_len

            while size > 0:
                
                if size >= FRAGMENT_SIZE+header_len:
                    fragment = sock.recv(FRAGMENT_SIZE+header_len)
                else:
                    fragment = sock.recv(size)
                    
                size -= len(fragment)
                
            packet = fragment[:header_len]
            packet = struct.unpack(sock352PktHdrData, packet)
            
            if i == packet[8]:
                finalMsg += fragment[header_len:]
                
                ack_packet = self.create_header(ACK, 0, i, 0)
                sock.sendto(ack_packet, other_address)
                i += 1
            else:
                continue
                
        if remainder > 0:
        
            fragment = ''
            size = remainder + header_len

            while size > 0:
                
                if size >= remainder + header_len:
                    fragment = sock.recv(remainder+header_len)
                else:
                    fragment = sock.recv(size)
                    
                size -= len(fragment)
                
            packet = fragment[:header_len]
            packet = struct.unpack(sock352PktHdrData, packet)
            
            if i == packet[8]:
                finalMsg += fragment[header_len:]
                
                ack_packet = self.create_header(ACK, 0, i, 0)
                sock.sendto(ack_packet, other_address)
                i += 1
                
        return finalMsg
        
    def create_header (self, flags, seqNumbo, ackNum, payLoad):

        version = 0x1
        opt_ptr = 0x0
        protocol = 0x0
        checksum = 0x0
        source_port = 0x0
        dest_port = 0x0
        window = 0x0

        return udpPkt_hdr_data.pack(version, flags, opt_ptr, protocol, header_len, checksum, source_port, dest_port, seqNumbo, ackNum, window, payLoad)
  
