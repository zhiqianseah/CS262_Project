import socket
import thread 		#for spawning new threads to handle clients
import json			#for serializing data
import sock_helper
import time
import threading 	#for locks
import random

class StockExchangeServer:

	#initialize the Stock Exchange Server with a host/port
	def __init__(self, host = "127.0.0.1", port = 40000, Num_Companies = 5, StartingPrice = 30., UpdateFrequency = 5):

		#Set up Server socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind((host, port))
		print "Server Socket initialized."

		self.updatelock = threading.Lock()
		self.account = {}
		self.companies = {}
		self.pending_orders = {}
		self.demandsupply = {}  #used for updating company prices

		#populate the companies with initial values
		for x in range(Num_Companies):
			self.companies['Company'+str(x)] = StartingPrice

		#populate the demand supply as 0
		for x in range(Num_Companies):
			self.demandsupply['Company'+str(x)] = 0

		#Start a new therad for updating prices
		thread.start_new_thread( self.Price_Update_Thread, (UpdateFrequency,)  )

		#Listen for connections from clients. 
		#For each connection, spawn a new thread to handle  that client
		try:
			while True:
				sock.listen(1)
				client, addr = sock.accept()     # Establish connection with client.
				print 'Got connection from', addr	
				thread.start_new_thread( self.Client_Handling_Thread, (client, addr ) )

		except KeyboardInterrupt:
			print "Server Ended."
    		sock.close()


    #This thread will update company prices
    #python dictionaries are thread safe, so we don't have to worry about reader writer locks
	def Price_Update_Thread(self, frequency):
		start = time.time()

		while True:
			for company in self.companies:
				current_demandsupply = self.demandsupply[company]/50.
				newprice = self.companies[company] + round(random.normalvariate(0+current_demandsupply, 1), 2)

				#make sure that the price doesn't go below 0
				self.companies[company] = max (newprice, 0.01) 

				#Demand and supply degrade exponentially
				self.demandsupply[company] = self.demandsupply[company]/2


			#sleep the remaining time of an interval away
			time.sleep(frequency - ((time.time() - start) % frequency))

 	#thread to handle an incoming client
 	def Client_Handling_Thread(self, client, addr):

 		#the first message received by the user is his username to identify himself
		username = sock_helper.recv_msg(client)
		print addr, ' >> ', username

		#if the stock exchange sees a new user, create a new account for him and give him 1000 dollars
		#Reply the client with a welcome message
		if username not in self.account:
			self.account[username] = {}
			self.account[username]['bank'] = 1000
			self.account[username]['position'] = {}
			self.pending_orders[username] = []

			sock_helper.send_msg("Welcome, new user!. We have created a new account for you.", client)
	 	else:
			sock_helper.send_msg("Welcome Back, "+str(username)+".", client)


 		#listen to the client messages and respond accordingly
 		while True:
 			try:

 				#receive the data from the client
				msg_raw = sock_helper.recv_msg(client)

				#deserialize the data into a dictionary
				msg_dict = json.loads(msg_raw) 
				print addr, ' >> ', msg_dict

				#process the message
				return_msg = self.Process_Message(msg_dict, username)

				data_string = json.dumps(return_msg)
				#send an acknowledgement back to the server
				sock_helper.send_msg(data_string, client)

	 		except Exception as e:
	 			print "Exception: ", e
	 			print "Connection Broken from:", addr
	 			break


	#This function process an incoming command dictionary from the client, and process it accordingly
	#It will reply with a response dictionary that will be sent back to the user
	def Process_Message(self, msg_dict, username):

		reply_dict = {}

		if msg_dict['request_type'] == "queryBalance":
			reply_dict['response_type'] = "queryBalanceResponse"
			reply_dict['data'] = {}
			reply_dict['data']['balance'] = self.account[username]['bank']			
			return reply_dict

		elif msg_dict['request_type'] == "queryPrice":
			reply_dict['response_type'] = "queryPriceResponse"
			reply_dict['data'] = {}		
			for company in self.companies:
				reply_dict['data'][company] = self.companies[company]
			return reply_dict
		elif msg_dict['request_type'] == 'queryPendingOrder':
			#TODO
			reply_dict['response_type'] = 'queryPendingOrderResponse'
			reply_dict['data'] = self.pending_orders[username]

			return reply_dict
		elif msg_dict['request_type'] == "buy":
				# Response to the buy request
				reply_dict['response_type'] = "buyResponse"
				# Parse request message
				msg_data = msg_dict['data']
				ticketNumber = msg_data['ticketNumber']
				tick = msg_data['tick']
				volume = int(msg_data['volume'])
				price = float(msg_data['price'])
				# Enough money in bank for the order
				if self.companies[tick] * volume <= self.account[username]['bank']:
					# Order can be executed
						if price >= self.companies[tick]:
								self.account[username]['bank'] -= self.companies[tick] * volume
								if tick in self.account[username]['position']:
										self.account[username]['position'][tick] += volume
								else:
										self.account[username]['position'][tick] = volume
								#increase demand for this company
								self.demandsupply[tick] += float(volume)
								reply_dict['status'] = "Transaction succeeded"
						else:
								# Put the order on a queue
								self.pending_orders[username].append(msg_dict)
								reply_dict['status'] = "Pending Order"
				# Don't have enough money to execute the order
				else:
						reply_dict['status'] = "Not enough account balance"
				return reply_dict
		elif msg_dict['request_type'] == "sell":
				# Response to the buy request
				reply_dict['response_type'] = "sellResponse"
				# Parse request message
				msg_data = msg_dict['data']
				ticketNumber = msg_data['ticketNumber']
				tick = msg_data['tick']
				volume = int(msg_data['volume'])
				price = float(msg_data['price'])
				# Enough money in bank for the order
				if volume <= self.account[username]['position'][tick]:
					# Order can be executed
						if price <= self.companies[tick]:
								self.account[username]['position'][tick] -= volume
								self.account[username]['bank'] += self.companies[tick] * volume
								#decrease demand for this company
								self.demandsupply[tick] -= float(volume)
								reply_dict['status'] = "Transaction succeeded"
						else:
								# Put the order on a queue
								self.pending_orders[username].append(msg_dict)
								reply_dict['status'] = "Pending Order"
				# Don't have enough money to execute the order
				else:
						reply_dict['status'] = "Not enough shares to sell"
				return reply_dict

		elif msg_dict['request_type'] == "cancel":
				# Response to the buy request
				reply_dict['response_type'] = "cancelResponse"
				reply_dict['status'] = "Order not found"
				# Parse request message
				msg_data = msg_dict['data']
				ticketNumber = msg_data['ticketNumber']
				# Cancel pending order
				for i in range(len(self.pending_orders[username])):
						if self.pending_orders[username][i]['data']['ticketNumber'] == ticketNumber:
								del self.pending_orders[username][i]
								print 'Order cancelled'
								reply_dict['status'] = 'Order cancelled'
				return reply_dict

		#opcode not recognized. return invalid command
		reply_dict['response_type']= "invalidCommand"
		reply_dict['data'] = {}
		return reply_dict

if __name__ == "__main__":
    StockExchangeServer()
