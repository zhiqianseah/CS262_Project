import socket
import thread 		#for spawning new threads to handle clients
import json			#for serializing data
import sock_helper
import time
import random
import sys			#for command line inputs
import sqlite3		#for server failure
from datetime import datetime

class StockExchangeServer:
	"""
	@author Thomas Seah, Victor Lei, Chenchen Zhang, Yaoguang Jia
	@version May 8, 2016
	This the class realize the function of Stock Exchange Server
	The server has the functions:
		a. keep receive request message from aritificial or pc players
		and generate the response message. 
		b. update the bank account and stock information of the client when new trade happens
		c. has a thread to do the price update
		d. During the operation, server keep saving the data for the server recovary
	
	Member functure:
		__int__: Initialize the stock exchage server, it can handle server restart
		Price_Update_Thread: start a new thread to update price according to demand supply status
		Client_Handling_Thread: start a thread to handle new coming client; it can handle both artificial
		                        player and pc player
		Process_Message: Process the message from client, update the data structure of the corresponding client
						 and generate the response message
		SaveToDisk: save all information on disk for server recovary
		
	"""

	#initialize the Stock Exchange Server with a host/port
	def __init__(self, host = "127.0.0.1", port = 40000, Num_Companies = 5, StartingPrice = 30., UpdateFrequency = 5, DemandSupply_Const = 50., restart=False):
		"""
		The function __init__ is to initialize the stock exchange server with a host/port
		
		When server starts, it first determine whether it is starting normally or restarts from failure.
		If it starts normally, the function initialize the dictionary for the data including account,
		companies, pending_orders and demandsupply; if it restarts from failure, the function reload data from disk
		It keeps listen new coming clients and starts new threads to hand the new client.
		
		param:
			host(string):initialize the IP of the host
			port(const):initialize the port number
			Num_Companies(int): initialize the number of companies
			startPrice(float): initialize the start price
			UpdateFrequency(int): the frequency of price update
			DemandSupply_const(float): the const used in the demand supply relationship for price update
			restart(bool): determine whether the server is restarting from failure
		"""
		
		
		#Set up Server socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind((host, port))
		print "Server Socket initialized."

		#determin whether the server is restarting
		if restart:
			#if is restarting, connect to data base
			conn = sqlite3.connect('./data/server_backup.db')
			c = conn.cursor()	
			# load data from data base
			for row in c.execute('''SELECT * from backup ORDER BY time DESC LIMIT 1;'''):	
				self.account = json.loads(row[0])
				self.companies = json.loads(row[1])
				self.pending_orders = json.loads(row[2])
				self.demandsupply = json.loads(row[3])			
		else:
			# if is not restarting, just initialize the data structure
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
		thread.start_new_thread( self.Price_Update_Thread, (UpdateFrequency, DemandSupply_Const, restart)  )

		#Listen for connections from clients. 
		#For each connection, spawn a new thread to handle  that client
		try:
			while True:
				sock.listen(1)
				client, addr = sock.accept()     # Establish connection with client.
				print 'Got connection from', addr	
				# start new thread to handle new client
				thread.start_new_thread( self.Client_Handling_Thread, (client, addr ) )

		except KeyboardInterrupt:
			print "Server Ended."
    		sock.close()


    #This thread will update company prices
    #python dictionaries are thread safe, so we don't have to worry about reader writer locks
	def Price_Update_Thread(self, frequency, DemandSupply_Const, restart):
		"""
		the method Price_Update_Thread 
		"""
		start = time.time()

		self.conn = sqlite3.connect('./data/server_backup.db')
		self.c = self.conn.cursor()
		if not restart:
			self.c.execute('''DROP TABLE IF EXISTS backup''')
			self.c.execute('''CREATE TABLE backup
			             (account text, companies text, pending_orders text, demandsupply text, time timestamp)''')
		while True:
			for company in self.companies:
				current_demandsupply = self.demandsupply[company]/DemandSupply_Const
				newprice = self.companies[company] + round(random.normalvariate(0+current_demandsupply, 1), 2)

				#make sure that the price doesn't go below 0
				self.companies[company] = max (newprice, 0.01) 

				#Demand and supply degrade exponentially
				self.demandsupply[company] = self.demandsupply[company]/2

				self.SaveToDisk();
                        for account, account_pending_orders in self.pending_orders.iteritems():
                                for apending_order in account_pending_orders:
                                        apending_order_data = apending_order['data']
                                        price =  float(apending_order_data['price'])
                                        volume = int(apending_order_data['volume'])
                                        tick = apending_order_data['tick']
                                        if apending_order_data['expirationTime'] >= time.time():
                                                if apending_order['request_type'] == 'buy':
                                                            if  price > self.companies[tick] and self.companies[tick] * volume <= self.account[account]['bank']:
                                                                    self.account[account]['bank'] -= self.companies[tick] * volume
                                                                    if tick in self.account[account]['position']:
							                    self.account[account]['position'][tick] += volume
							            else:
								            self.account[account]['position'][tick] = volume
                                                                    apending_order_data['expirationTime'] = time.time()
                                                if apending_order['request_type'] == 'sell':
                                                            if price < self.companies[tick] and self.account[username]['position'][tick] >= volume:
                                                                    self.account[account]['bank'] += self.companies[tick] * volume
                                                                    if tick in self.account[account]['position']:
							                    self.account[username]['position'][tick] -= volume
                                                                    apending_order_data['expirationTime'] = time.time()
                
			#sleep the remaining time of an interval away
			time.sleep(frequency - ((time.time() - start) % frequency))


	def SaveToDisk(self):

		self.c.execute('''INSERT INTO backup VALUES (?,?,?,?,?)''',(json.dumps(self.account),json.dumps(self.companies),
			json.dumps(self.pending_orders),json.dumps(self.demandsupply),datetime.now()))

		# Save the changes
		self.conn.commit()



 	#thread to handle an incoming client
 	def Client_Handling_Thread(self, client, addr):

 		#the first message received by the user is his username to identify himself
		credential = sock_helper.recv_msg(client)
		print addr, ' >> ', credential
                username, password = credential.split(' ')
                pc_player = False
                if username.startswith('pc_'):
                        pc_player = True
                        longPosition = True                        
                authorized = False

		#if the stock exchange sees a new user, create a new account for him and give him 1000 dollars
		#Reply the client with a welcome message
		if username not in self.account:
			self.account[username] = {}
			self.account[username]['bank'] = 1000
			self.account[username]['password'] = password
			self.account[username]['position'] = {}
			self.pending_orders[username] = []

			sock_helper.send_msg("Welcome, new user!. We have created a new account for you.", client)
                        authorized = True
                elif self.account[username]['password'] == password:
			sock_helper.send_msg("Welcome Back, "+str(username)+".", client)
                        authorized = True
                else:
			sock_helper.send_msg("Unauthorized",client)

 		#listen to the client messages and respond accordingly
 		while authorized and not pc_player:
 			try:

 				#receive the data from the client
				msg_raw = sock_helper.recv_msg(client)

				#deserialize the data into a dictionary
				msg_dict = json.loads(msg_raw) 
				#print addr, ' >> ', msg_dict

				#process the message
				return_msg = self.Process_Message(msg_dict, username)

				data_string = json.dumps(return_msg)
				#send an acknowledgement back to the server
				sock_helper.send_msg(data_string, client)

	 		except Exception as e:
	 			print "Exception: ", e
	 			print "Connection Broken from:", addr
	 			break

                while authorized and pc_player:
                        if longPosition:
                                current_holding, current_price = 'Company', 999
                                for tick in self.companies:
                                        if self.companies[tick] < current_price:
                                                current_holding, current_price = tick, self.companies[tick]
                                max_share = int(self.account[username]['bank'] / current_price)
                                self.account[username]['bank'] -= max_share * current_price
                                if current_holding not in self.account[username]['position']:
                                        self.account[username]['position'][current_holding] = max_share
                                else:
                                        self.account[username]['position'][current_holding] += max_share
                                        
                                longPosition = False
                        if not longPosition:
                                if self.companies[current_holding] > current_price:
                                        self.account[username]['bank'] += self.account[username]['position'][current_holding] *  self.companies[current_holding]
                                        self.account[username]['position'][current_holding] = 0
                                        longPosition = True
                        reply_dict = {}
                        reply_dict['response_type'] = "queryBalanceResponse"
			reply_dict['data'] = {}
			reply_dict['data']['balance'] = self.account[username]['bank']	
			reply_dict['data']['ticks'] = self.account[username]['position']
                        data_string = json.dumps(reply_dict)
			#send an acknowledgement back to the server
			sock_helper.send_msg(data_string, client)
                        time.sleep(20)


	#This function process an incoming command dictionary from the client, and process it accordingly
	#It will reply with a response dictionary that will be sent back to the user
	def Process_Message(self, msg_dict, username):

		reply_dict = {}

		if msg_dict['request_type'] == "queryBalance":
			reply_dict['response_type'] = "queryBalanceResponse"
			reply_dict['data'] = {}
			reply_dict['data']['balance'] = self.account[username]['bank']	
			reply_dict['data']['ticks'] = self.account[username]['position']		
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
				if tick in self.companies:
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
                                                                        print msg_dict
									self.pending_orders[username].append(msg_dict)
									reply_dict['status'] = "Pending Order"
					# Don't have enough money to execute the order
					else:
							reply_dict['status'] = "Not enough account balance"
				else:
					reply_dict['status'] = "Company doesn't exist."				
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
				if tick in self.companies:				
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
				else:
					reply_dict['status'] = "Company doesn't exist."							
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
	try:
		if len(sys.argv) is 2:
			StockExchangeServer(restart = sys.argv[1])
		else:
			StockExchangeServer()
	except Exception as e:
		print e
		print "Restarting Server"
		StockExchangeServer(restart = True)    	
