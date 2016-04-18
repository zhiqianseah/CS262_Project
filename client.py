import socket

class PlayerClient:

	#initialize the Player client with a host/port
	def __init__(self, host = "127.0.0.1", port = 9999):

		#Set up Server socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((host, port))

		#while loop to get user input and set to the server
		while True:

			#get user command-line input
			msg = raw_input('Enter Command: ')

			#if the input command is to quit the client, break the while loop
			if msg == 'quit':
				break

			try:
				#send the msg to the socket
				sock.send(msg)

				#get reply from the server and print it
				msg = sock.recv(1024)
				print "Received:", msg 
			except:
				print "Connection Broken. Quitting program"
				break

if __name__ == "__main__":
    PlayerClient()