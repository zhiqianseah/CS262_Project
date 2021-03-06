#CS 262 Project
## Distributed System for Stock Market Simulation
The project is to build a distributed system for stock market simulation. The distributed system is a server-client based system, where the server represents the stock exchange, bank and companies, and the clients represent the artificial and PC players. It is realized under python with hand crafted protocols. The clients can send messages to buy, sell, cancel orders and query relevant information from server. The server can keep listening the the clients, processing their orders, updating the relevant information and responding to them. Moreover, the server can also update prices and can be recovered from failure. There are four parts in the system package, which are 'server.py', 'client.py', 'sock_helper.py', and the 'server_backup.db' in the fold 'data'. Below is a concise description of the function and relationship between the four parts.

- **server.py:**  the class that realizes the function of stock exchange. It can be accessed remotely by 'client.py' class. It can receive messages from client and respond to them by using the methods defined in 'sock_helper.py'. While operating, server keeps saving information in 'server_backup.db' so that it can be recovered from failure.
- **client.py:**  the class that realizes the function of client (player). The player can be artificial or PC. It is also accessed remotely by server.py class. Through 'sock_helper.py', client.py can send and receive messages.
- **sock_helper:**  In the file, there are two methods 'send_msg' and 'recvall' used by 'server.py' and 'client.py' to send and receive messages in sockets. The 'client.py' and 'server.py' will import this file on their head.
- **server_backup.db:** the data base that stores the information in the stock market simulation system like bank balance for all players, prices for companies, and the pending order information. During the running of server, it keeps saving information to the data base. When the server restarts, it can reload the information from data base so that the server restarts correctly.


## Get Started
### Server Commands
To start up the server:

    python server.py

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme1.png?raw=true)

To start up the server by reading from backup file:

    python server.py 1

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme2.png?raw=true)

### Client Commands
To start up a pc player:
A pc player's name must be prefixed with "pc_", there's no command prompt for user to enter, if a pc player is initialized. Every 10 seconds the screen of pc player will be updated with the most recent balance.

    python client.py pc_user password

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme3.png?raw=true)

To start up a human player:
The password will be memorized by the server during the first login attempt and the same password should be used for any future authentication. There's functionality to change/update the password once it's set. 

    python client.py user password

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme4.png?raw=true)

To query all the stock prices:

    Enter Command: queryPrice

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme5.png?raw=true)

To query the account balance and current stock holdings:

    Enter Command: queryBalance

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme6.png?raw=true)

To place a buy order:

    Enter Command: buy,Company1,10,29.5,20

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme7.png?raw=true)

To place a sell order:

    Enter Command: sell,Company1,10,29.5,20

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme8.png?raw=true)

To query all the pending orders:

    Enter Command: queryPendingOrder

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme9.png?raw=true)

To cancel a pending order:

    Enter Command: cancel,1

![alt text](https://github.com/zhiqianseah/CS262_Project/blob/master/Example/readme10.png?raw=true)
