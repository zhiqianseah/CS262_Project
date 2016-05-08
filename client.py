import socket
import json			#for serializing data
import time
import sock_helper
import sys

class PlayerClient:
	"""
	@author Thomas Seah, Victor Lei, Chenchen Zhang, Yaoguang Jia
	@version May 8,2016
	This class realize the function of player as a client in 
	the distributed system. It can receive and send messages to server
	The player can be either artificial of PC
	
	Member Function:
		_init_: Initialize the player client
		CommandLoop: It can be accessed remotely. In the method, the client login and 
					 keeps sending message to server and receiving response messages from server
		Parse_Input: Called by CommandLoop to transform the original input string to the data 
					 dictionary that can be sent to server side
		Parse_Print_Reply: Also called by 
	"""
	
	
	def __init__(self, username = 'user1', password = 'password', host = "127.0.0.1", port = 40000):
		
		"""__init__ method is to initialize the player client with a host/port
		The initialization includes set up the server socket, the password of this 
		account and the elements of information in an standard order.
		
		Args:
			username(string): specify the user name
			password(string):specify the password to log in
			host(string)
			port(const)
		"""
		#Set up Server socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#connect to server
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
		
		
	
	def CommandLoop(self):
		"""method CommandLoop is to read the input from command line, process the 
		string into dictionaries and send the messages to server. It also keeps receiving
		message from server side, parsing the input and print the information.
		
		The messaging protocol in the system is hand crafted and 
		the sending and receiving are through the json serialization and deserialization
		
		This member function can also handle pc players by determine the value of pc_player
		and run the client in different while loops
		"""
		
		#the first message to the server is the username to identify the user
                credential = self.user + ' ' + self.password
                print credential
		sock_helper.send_msg(credential, self.sock) #send credential message to server 

		#get reply from the server regarding the login
		msg = sock_helper.recv_msg(self.sock)
				# if unathorized then print login failed
                if msg == 'Unauthorized':
                        print "Login failed."
                        sys.exit(1)
                pc_player = self.user.startswith('pc_')

		#while loop to get user input and set to the server when it is not pc_player
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
			#When error exists, an exception will be thrown and the error message will be printed
			except Exception as e:
				print "Exception:", e
				print "Connection Broken. Quitting program"
				self.sock.close()
				break
			#When it is pc_player 
	        while pc_player and msg != 'Unauthorized':
                            reply_raw = sock_helper.recv_msg(self.sock) #receive message from server
		
			    msg = json.loads(reply_raw) # deserialize the message
			    self.Parse_Print_Reply(msg) # parse and print the message
                            time.sleep(10)  # sleep 10 seconds
	
	
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
				# Set request values in the order 
				for order, value in zip(self.OrderInfo[1:], msg_split[1:]):
					command_dict['data'][order]=value
				command_dict['data']['ticketNumber']=self.ticketNumber
				print "ticket Number:",self.ticketNumber
				# Add the ticket number by 1
				self.ticketNumber+=1
			
			#print self.ticketNumber
		#store the data of request type cancel		
		elif command_dict['request_type']=="cancel":
			# determine whether the command is correct
			if len(msg_split) != 2:
				print "Too less or more information"
			else:
				command_dict['data']={}
				#specify the ticket number 
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
			#print the pending order information in a table
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

# specify the username and password by system input, used only pc_player
input_username = sys.argv[1]
input_password = sys.argv[2]

if __name__ == "__main__":
    client = PlayerClient(username = input_username, password = input_password)
    

