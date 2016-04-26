import socket
import json			#for serializing data
import time
import sock_helper

class PlayerClient:

	#initialize the Player client with a host/port
	def __init__(self, username = 'user1', host = "127.0.0.1", port = 40000):

		#Set up Server socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((host, port))
		self.user = username
		self.OrderInfo=[]
		self.OrderInfo=['ticketNumber','tick','volume','price','expirationTime']
		self.ticketNumber=1
		#run a loop to get user commands
		self.CommandLoop()
		
		
		#specify the information in a standard order
		
	
	def CommandLoop(self):

		#the first message to the server is the username to identify the user
		sock_helper.send_msg(self.user, self.sock)

		#get reply from the server regarding the login
		msg = sock_helper.recv_msg(self.sock)

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

				if command_dict is None:
					continue

				#Serialize the data
				data_string = json.dumps(command_dict)
				#print data_string

				#send the msg to the socket
				sock_helper.send_msg(data_string, self.sock)

				#get reply from the server and print it
				reply_raw = sock_helper.recv_msg(self.sock)

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

		#split the message based on ,
		msg_split = msg.split(",")

		#store it in the relevant sections of the command dictionary
		command_dict['request_type'] = msg_split[0]

		#store the data of buy and sell
		if command_dict['request_type']=="buy" or command_dict['request_type']=="sell":
			print len(msg_split),len(self.OrderInfo)
			
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

		#parse the different type of response from the server
		if msg['response_type'] == "invalidCommand":
			print "Server received an invalid command."

		if msg['response_type'] == "queryBalanceResponse":
			print "Your Bank Balance is:", msg['data']['balance']

		if msg['response_type'] == "queryPriceResponse":
			print "Prices of Companies:"
			for company in msg['data']:
				print company + ":", msg['data'][company]

		if msg['response_type'] == "queryPendingOrderResponse":
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
		
		if msg['response_type']=="sellResponse":
			print "Sell Status",msg['status']
		
		if msg['response_type']=="cancelResponse":
			print "Cancel Status", msg['status']
		
if __name__ == "__main__":
    client = PlayerClient(username = 'user1')
    

