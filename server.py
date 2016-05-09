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


    
	def Price_Update_Thread(self, frequency, DemandSupply_Const, restart):
		"""
		the method Price_Update_Thread is to update the price based on demand supply relationship;
		
		the new price equals the current price plus a Gaussian variable whose mean is the the
		current demand supply variable and variance is 1.
		
		at the same time, when price is updated, it examine the pending order queue if there is buy or sell 
		pending order whose price is acceptable under the updated price condition. 
		If there is server will process them in this method.
		
		param:
			frequency(int): the parameter to control the frequency of updating price
			DemandSupply_Const: the const to control the current demand supply variable
			restart(bool): the variable that flag if the server is restarting, if it is not restarting, then drop the existing table
			               create new backup table
		
		"""
		# record the start time
		start = time.time()
		# construct connection to a data base
		self.conn = sqlite3.connect('./data/server_backup.db')
		# create a cursor sot that can excute the operation in SQL
		self.c = self.conn.cursor()
		# if the server is not restarting, drop the existing backup and create a new one
		if not restart:
			self.c.execute('''DROP TABLE IF EXISTS backup''')
			self.c.execute('''CREATE TABLE backup
			             (account text, companies text, pending_orders text, demandsupply text, time timestamp)''')
		# run the loop to update the price and process relevant pending order				 
		while True:
			for company in self.companies:
				# generate current demand supply variable
				current_demandsupply = self.demandsupply[company]/DemandSupply_Const
				# generate the new price to be the current price plus a Gaussian vaviable decided by demand supply variable
				newprice = self.companies[company] + round(random.normalvariate(0+current_demandsupply, 1), 2)

				#make sure that the price doesn't go below 0
				self.companies[company] = max (newprice, 0.01) 

				#Demand and supply degrade exponentially
				self.demandsupply[company] = self.demandsupply[company]/2
				# save the update to disk 
				self.SaveToDisk();
				# process the relavent pending order
                        for account, account_pending_orders in self.pending_orders.iteritems(): 
                        	# dequeue the pending order
                                for apending_order in account_pending_orders:          
                                        apending_order_data = apending_order['data']
                                        # take the price
                                        price =  float(apending_order_data['price'])
                                        # take volume information   
                                        volume = int(apending_order_data['volume'])
                                        # take the tick information    
                                        tick = apending_order_data['tick']
                                        # when the order has not expired             
                                        if apending_order_data['expirationTime'] >= time.time():
                                        # determine the order type, 'buy' or 'sell'  
                                                if apending_order['request_type'] == 'buy':       
									# if it is buy order, determine whether the price is acceptable after the price updating
									# and if the client has enough balance
                                                            if  price > self.companies[tick] and self.companies[tick] * volume <= self.account[account]['bank']:
                                                            	# process the order and substract balance
                                                                    self.account[account]['bank'] -= self.companies[tick] * volume 
                                                                    # if client has bought the tick before
                                                                    if tick in self.account[account]['position']: 
                                                                    	# just add volume
							                    self.account[account]['position'][tick] += volume                 
							            else:
							            	# if not create new tick
								            self.account[account]['position'][tick] = volume
								            # set the expiration time as current                      
                                                                    apending_order_data['expirationTime'] = time.time()  
                                                                    # when the request type is sell
                                                if apending_order['request_type'] == 'sell':                      
                                                            if price < self.companies[tick] and self.account[username]['position'][tick] >= volume: 
                                                                    self.account[account]['bank'] += self.companies[tick] * volume
                                                                    if tick in self.account[account]['position']:
							                    self.account[username]['position'][tick] -= volume
                                                                    apending_order_data['expirationTime'] = time.time()
                
			#sleep the remaining time of an interval away
			time.sleep(frequency - ((time.time() - start) % frequency))


	def SaveToDisk(self):
		"""
		method SaveToDisk is to  save the current information to the backup database
		"""
		# excute the SQL command to insert the information to the existing backup database
		self.c.execute('''INSERT INTO backup VALUES (?,?,?,?,?)''',(json.dumps(self.account),json.dumps(self.companies),
			json.dumps(self.pending_orders),json.dumps(self.demandsupply),datetime.now()))

		# Save the changes
		self.conn.commit()



 	
 	def Client_Handling_Thread(self, client, addr):
 		"""
 		method Client_Handling_Thread is to start new thread to handle incoming client;
 		the server first identify the user by the credential information, it can handle either pc_player or artificial player;
 		after identifying the new client, server create new account  and send him welcome messages;
 		during the operation, server keeps listening the messages from client and response accordingly

 		param:
 			client: the new incoming client
 			addr: the address of the client

 		"""

 		#the first message received by the user is his username to identify himself
		credential = sock_helper.recv_msg(client)
		#print addresss and login information
		print addr, ' >> ', credential
                username, password = credential.split(' ')
                pc_player = False
                if username.startswith('pc_'): # determin whether the client is a pc_player or not
                        pc_player = True       # set the flag of pc_player
                        longPosition = True    # longPosition is the varialbe relevant to pc_player trading behavior                    
                authorized = False

		#if the stock exchange sees a new user, create a new account for him and give him 1000 dollars
		#Reply the client with a welcome message
		if username not in self.account:
			self.account[username] = {}
			self.account[username]['bank'] = 1000         # initialize bank account
			self.account[username]['password'] = password # store password
			self.account[username]['position'] = {}       # initialize the position of the client
			self.pending_orders[username] = []            # set upt the queue of pending order for the client
            # sent the welcome message to client
			sock_helper.send_msg("Welcome, new user!. We have created a new account for you.", client)
                        authorized = True   # set up the authorization flag to be true
                elif self.account[username]['password'] == password:  # if it is re-login determine if the password is correct
			sock_helper.send_msg("Welcome Back, "+str(username)+".", client)   # authorize the re-login and send message
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
            # throws exception when error occurs and print the address where the error occurs
	 		except Exception as e:
	 			print "Exception: ", e
	 			print "Connection Broken from:", addr
	 			break
                # for authorized pc_player, specify the behavior of the player
                while authorized and pc_player:
                	# if the longPosition=True, buy the cheapest stock
                        if longPosition:
                                current_holding, current_price = 'Company', 999
                                for tick in self.companies:
                                	# buy the cheapest stock
                                        if self.companies[tick] < current_price:
                                                current_holding, current_price = tick, self.companies[tick]
                                #buy with all balance available
                                max_share = int(self.account[username]['bank'] / current_price)
                                self.account[username]['bank'] -= max_share * current_price
                                # add shares of the bought stocks
                                if current_holding not in self.account[username]['position']:
                                        self.account[username]['position'][current_holding] = max_share
                                else:
                                        self.account[username]['position'][current_holding] += max_share
                                # set the longPosition to be False        
                                longPosition = False
                        # when longPostion=False use another behavior
                        if not longPosition:
                        	# short stocks if the prices goes up
                                if self.companies[current_holding] > current_price:
                                        self.account[username]['bank'] += self.account[username]['position'][current_holding] *  self.companies[current_holding]
                                        self.account[username]['position'][current_holding] = 0
                                        longPosition = True
                        reply_dict = {}
                        # reply to server the balance and holding stocks of the pc_player
                        reply_dict['response_type'] = "queryBalanceResponse"
			reply_dict['data'] = {}
			reply_dict['data']['balance'] = self.account[username]['bank']	
			reply_dict['data']['ticks'] = self.account[username]['position']
                        data_string = json.dumps(reply_dict)
			#send an acknowledgement back to the server
			sock_helper.send_msg(data_string, client)
                        time.sleep(20)


	
	def Process_Message(self, msg_dict, username):
		"""
        method Process_Message is to process the message received from client and generate response message accordingly
        it is called by Client_Handling_Thread
        the function first decide the request type and then generate the corresponding messages:
        request_type="queryBalance": response_type="queryBalanceResponse" data={balance:(),tick:()}
        request_type="queryPrice": response_type="queryPriceResponse" data={balance:(),tick:()}
        request_type="queryPendingOrder": response_type="queryPendingOrderResponse" 
        request_type="buy" update the ticket number, volume, tick, and bank balance for the client, response_type="buyResponse"
        request_type="sell" update the ticket number, volume, tick, and bank balance for the client, response_type="sellResponse"
        resquest_type="cancel" cancel the specified pending order, response_typer="cancelResponse"

        param:
        	msg_dict(dictionary): request message from client
        	username(string): specify the client we are processing
        return:
        	reply_dict(dictionary): the reply message that  
		"""


        # initialize the reply_dict
		reply_dict = {}
        # if the request type is queryBalance
		if msg_dict['request_type'] == "queryBalance":
			# specify the response type 
			reply_dict['response_type'] = "queryBalanceResponse"
			reply_dict['data'] = {}
			# specify the bank account and the volume of ticks it owns
			reply_dict['data']['balance'] = self.account[username]['bank']	
			reply_dict['data']['ticks'] = self.account[username]['position']		
			return reply_dict
        # if the request type is query Price
		elif msg_dict['request_type'] == "queryPrice":
			# specify the response type
			reply_dict['response_type'] = "queryPriceResponse"
			reply_dict['data'] = {}	
			# the data in reply dict are the companies and their price	
			for company in self.companies:
				reply_dict['data'][company] = self.companies[company]
			return reply_dict
		# if the requestion type is the pending oder
		elif msg_dict['request_type'] == 'queryPendingOrder':
			# specify the response type
			reply_dict['response_type'] = 'queryPendingOrderResponse'
			# the data in reply dict is the pending order of the requesting client
			reply_dict['data'] = self.pending_orders[username]

			return reply_dict
		# process the buy request
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
								#substract balance from the bank account
									self.account[username]['bank'] -= self.companies[tick] * volume
									# create a new tick or add volume to existing ticks
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
								#substract volume from existing tick
									self.account[username]['position'][tick] -= volume
									# add balance to bank account
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
								reply_dict['status'] = 'Order cancelled' # reply the ceancel status
				return reply_dict

		#opcode not recognized. return invalid command
		reply_dict['response_type']= "invalidCommand"
		reply_dict['data'] = {}
		return reply_dict
# run the client with the param restart
# if no restart flag, just regard it as normal start
if __name__ == "__main__":
	try:
		# restart the server
		if len(sys.argv) is 2:
			StockExchangeServer(restart = sys.argv[1])
		# normally start the server
		else:
			StockExchangeServer()
	# when error occures the server can restart		
	except Exception as e:
		print e
		print "Restarting Server"
		StockExchangeServer(restart = True)    	
