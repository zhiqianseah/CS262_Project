import socket
import json			#for serializing data

class PlayerClient:

	#initialize the Player client with a host/port
	def __init__(self, username = 'user1', host = "127.0.0.1", port = 40000):

		#Set up Server socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((host, port))
		self.user = username

		#run a loop to get user commands
		self.CommandLoop()

	def CommandLoop(self):

		#the first message to the server is the username to identify the user
		self.sock.send(self.user)

		#get reply from the server regarding the login
		msg = self.sock.recv(1024)
		print msg

		#while loop to get user input and set to the server
		while True:

			#get user command-line input
			msg = raw_input('Enter Command: ')

			#if the input command is to quit the client, break the while loop
			if msg == 'quit':
				break

			try:

				command_dict = self.Parse_Input(msg)

				#Serialize the data
				data_string = json.dumps(command_dict)
				#print data_string

				#send the msg to the socket
				self.sock.send(data_string)

				#get reply from the server and print it
				reply_raw = self.sock.recv(1024)
				msg = json.loads(reply_raw) 
				self.Parse_Print_Reply(msg)

			except Exception as e:
				print "Exception:", e
				print "Connection Broken. Quitting program"
				self.sock.close()
				break

	#this function parse the command line input string from the user and populates a command dictionary accordingly
	def Parse_Input(self, msg):
		command_dict = {}

		#split the message based on spaces
		msg_split = msg.split(" ")

		#store it in the relevant sections of the command dictionary
		command_dict["request_type"] = msg_split[0]


		return command_dict

	#This function parse the reply dictionary from the server, and print the relevant information
	def Parse_Print_Reply(self, msg):

		#parse the different type of response from the server
		if msg['response_type'] == "invalidCommand":
			print "Server received an invalid command."

		if msg['response_type'] == "queryBalanceResponse":
			print "Your Bank Balance is:", msg['data']['balance']

		if msg['response_type'] == 'queryPriceResponse':
			print "Prices of Companies:"
			for company in msg['data']:
				print company + ":", msg['data'][company] 
		#print "Received:", msg

if __name__ == "__main__":
    client = PlayerClient(username = 'user1')
    