import socket
import thread

class StockExchangeServer:

	#initialize the Stock Exchange Server with a host/port
	def __init__(self, host = "127.0.0.1", port = 9999):

		#Set up Server socket
		sock = socket.socket()
		sock.bind((host, port))

		print "Server Socket initialized."

		#Listen for connections from clients. 
		#For each connection, spawn a new thread to handle  that client
		while True:
			sock.listen(1)
			client, addr = sock.accept()     # Establish connection with client.
			print 'Got connection from', addr	
			thread.start_new_thread( self.client_handling_thread, (client, addr ) )




 	#thread to handle an incoming client
 	def client_handling_thread(self, client, addr):

 		#listen to the client messages and respond accordingly
 		while True:
 			try:
				msg = client.recv(1024)
				print addr, ' >> ', msg
	 			client.send("Server Received: "+msg)
	 		except:
	 			print "Connection Broken from:", addr
	 			break


if __name__ == "__main__":
    StockExchangeServer()