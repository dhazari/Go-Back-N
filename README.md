# Go-Back-N

Dhrishti hazari, netID: dah253
Diana Del Gaudio, netID: dmd424
Python version 2.7.5

The Connect/Accept works and implements a 3-way handshake.

The send/recieve works by sending packets of size 64000. Then, the rec method will send back the header of the packet containing the expected seqNum. there is also a global seqNum that has been incremented in recv, so if the global seqNum and the ackNum recieved in the header file send fro the recv method are the same, you can tell that the packet is in order because seqNum+1 = ackNum.

The close method uses a double handshake with a global variable to tell if the server is the one doing the close or if the client is the one doing the close. 
