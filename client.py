import socket
import json			#for serializing data
import time
import sock_helper
import sys

class PlayerClient:
	"""This class realize the function of player as a client in 
	the distributed system. The member function 'CommandLoop' can be 
	accessed remotely. The member function 'Parse_Input' and 'Parse_Print_Reply'
	are called by 'CommandLoop' to generate the data structure to be sent 
	and process the message received from server.
	"""
	
	#initialize the Player client with a host/port
	def __init__(self, username = 'user1', password = 'password', host = "127.0.0.1", port = 40000):
		
		"""__init__ method is to initialize the player client with a host/port
		The initialization includes set up the server socket, the password of this 
		account and the elements of information in an standard order.
		
		Args:
			username(string): specify the user name
			password(string):specify the password to log in
			host(string)
			host(const)
		"""
		#Set up Server socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((host, port))
		# initialize the username and password of the user
		self.user = username
                self.password = password
		#Initialize the keys in the order information dictionary
		self.OrderInfo=[]
		self.OrderInfo=['ticketNumber','tick','volume','price','expirationTime']
		#Initialize the first ticketNumber to be 1
		self.ticketNumber=1
		#run a loop to get user commands
		self.CommandLoop()
		
		
		#specify the information in a standard order
		
	
	def CommandLoop(self):
		"""method CommandLoop is to read the input from command line, process the 
		string into dictionaries and send the messages to server. It also keeps receiving
		message from server side, parsing the input and print the information.
		
		The messaging protocol in the system is hand crafted and 
		the sending and receiving are through the json serialization and deserialization
		
		This member function handle pc players:
		"""
		
		#the first message to the server is the username to identify the user
                credential = self.user + ' ' + self.password
                print credential
		sock_helper.send_msg(credential, self.sock)

		#get reply from the server regarding the login
		msg = sock_helper.recv_msg(self.sock)

                if msg == 'Unauthorized':
                        print "Login failed."
                        sys.exit(1)
                pc_player = self.user.startswith('pc_')

		#while loop to get user input and set to the server
		while not pc_player and msg != 'Unauthorized':

			#get user command-line input
			msg = raw_input('Enter Command: ')

			#if the input command is to quit the client, break the while loop
			if msg == 'quit':
				break

			try:
				#parse the input from command line into dictionary to be sent
				command_dict = self.Parse_Input(msg)
				# continue if the command is empty
				if command_dict is None:
					continue

				#Serialize the data
				data_string = json.dumps(command_dict)
				#print data_string

				#send the msg to the socket
				sock_helper.send_msg(data_string, self.sock)

				#get reply from the server and print it
				reply_raw = sock_helper.recv_msg(self.sock)
				#deserialize the data
				msg = json.loads(reply_raw) 
				#parse and print the reply
				self.Parse_Print_Reply(msg)
			#When error exists, an exception will be thrown and the error message will be print
			except Exception as e:
				print "Exception:", e
				print "Connection Broken. Quitting program"
				self.sock.close()
				break
			#When the pc_player is un
	        while pc_player and msg != 'Unauthorized':
                            reply_raw = sock_helper.recv_msg(self.sock)
		
			    msg = json.loads(reply_raw) 
			    self.Parse_Print_Reply(msg)
                            time.sleep(10)
	
	
	#this function parse the command line input string from the user and populates a command dictionary accordingly
	def Parse_Input(self, msg):
		"""Parse_Input is to parse the message got from command line into the dictionary that
		can be sent to the server side. The  dictionary is the command_dict where:
		key='request_type' and value=the data structure which is also a dictionary.
		
		Args:
			msg(string):
		Return:
			command_dict(dictionary)
		"""
		command_dict = {}

		#split the message based on ,
		msg_split = msg.split(",")

		#store it in the relevant sections of the command dictionary
		command_dict['request_type'] = msg_split[0]

		#store the data of buy and sell
		if command_dict['request_type']=="buy" or command_dict['request_type']=="sell":
			#print len(msg_split),len(self.OrderInfo)
			
			if len(msg_split) != len(self.OrderInfo):
				print "Too less or more information"
				return None
			else:
			#store the information of buy and sell order
				command_dict['data']={}				
				# Set expiration datetime
				msg_split[-1] = float(msg_split[-1])+time.time()
				# Set request values
				for order, value in zip(self.OrderInfo[1:], msg_split[1:]):
					command_dict['data'][order]=value
				command_dict['data']['ticketNumber']=self.ticketNumber
				print "ticket Number:",self.ticketNumber
				self.ticketNumber+=1
			
			#print self.ticketNumber
		#store the data of request type cancel		
		elif command_dict['request_type']=="cancel":
			if len(msg_split) != 2:
				print "Too less or more information"
			else:
				command_dict['data']={}
				#print int(msg_split[1])
				command_dict['data']['ticketNumber']=int(msg_split[1])
		# elif command_dict['request_type'] == 'pending':
		# 	# A request to get the pending orders for the current user
		# 	command_dict['data'] = {'username': }

		return command_dict

	#This function parse the reply dictionary from the server, and print the relevant information
	def Parse_Print_Reply(self, msg):
		"""Parse_Print_Reply method is called by Command_Loop. It parse the message 
		received from the server side print the corresponding information.
		
		Args:
			msg(dictionary): received dictionary from server
								key=response_type and value= corresponding data structure
		Print the corresponding information
		
		"""
		#parse the different type of response from the server
		
		#if the response type is invalide ,print the error message
		if msg['response_type'] == "invalidCommand":
			print "Server received an invalid command."
		# parse response of query balance
		if msg['response_type'] == "queryBalanceResponse":
			#print the current balance and current stocks
			print "Your Bank Balance is:", msg['data']['balance']
			print "Your current stocks are:"
			for tick in msg['data']['ticks']:
				print tick,":",msg['data']['ticks'][tick]
		#parse the response of query price
		if msg['response_type'] == "queryPriceResponse":
		#print the price of each company
			print "Prices of Companies:"
			for company in msg['data']:
				print company + ":", msg['data'][company]
		#parse the response of query pending orders
		if msg['response_type'] == "queryPendingOrderResponse":
			#print the pending order information
			print '''Number	|	Type	|	Company	|	Volume	|	Price	|	Expiration	|'''
			print '-------------------------------------------------------------------------------------------------'

			for order_dict in msg['data']:
				print '%s\t|\t%s\t|\t%s|\t%s\t|\t%s\t|\t%s'%(order_dict['data']['ticketNumber'],
				 order_dict['request_type'],
				 order_dict['data']['tick'],
				 order_dict['data']['volume'],
				 order_dict['data']['price'],
				 float(order_dict['data']['expirationTime']) - time.time())

		#print "Received:", msg
		#print buy status
		if msg['response_type']=="buyResponse":
			print "Buy Status", msg['status']
		# print sell status
		if msg['response_type']=="sellResponse":
			print "Sell Status",msg['status']
		#print cancel status
		if msg['response_type']=="cancelResponse":
			print "Cancel Status", msg['status']

input_username = sys.argv[1]
input_password = sys.argv[2]

if __name__ == "__main__":
    client = PlayerClient(username = input_username, password = input_password)
    

