import json
import requests
import multiprocessing
import time

import pickle
import subprocess

from flask import Flask, jsonify , request

from customerAgent import customerAgent







class WebHookHandler:
    def __init__(self, app , mainServer_UserManagerPipe=None):
        self.app = app
        self.mainServer_UserManagerPipe = mainServer_UserManagerPipe
        self.app.add_url_rule('/requestSessionCreation', 'requestSessionCreation', self.createSession, methods=['POST'])
        self.app.add_url_rule('/initializeSession', 'initializeSession', self.initialize_session_callback, methods=['POST'])
        self.app.add_url_rule('/handleSessionRequests', 'handleSessionRequests', self.handle_session_requests_callback, methods=['PUT'])
        self.app.add_url_rule('/serverRunning', 'serverRunning', self.server_running_callback, methods=['GET'])
        self.app.add_url_rule('/sessionSTATUS', 'sessionSTATUS', self.session_status_callback, methods=['GET'])
        self.app.add_url_rule('/updateSessionStatus', 'updateSessionStatus', self.update_session_status_callback, methods=['PUT'])

    def handle_session_creation_request(self , data):
        if data["EMAIL"] not in session_status.keys():
            session_creation_requests[data['EMAIL']] = data["DATA"]
            session_status[data['EMAIL']] = "PENDING"
            # print()
            # print(session_creation_requests.keys())
            # print()
            return jsonify({'message': 'Request Submitted'}), 200
        else:
            return jsonify({'message': 'Session Already Running'}), 403

    # @app.route('/requestSessionCreation', methods=['GET'])
    def createSession(self):
        f = open("customerServerLog.txt" , "a")
        if request.method == 'POST':
            f.write("Session Creation Called !!!")
            # data = json.dumps(request.get_json())
            content_type = request.headers['Content-Type']
            
            data = None
            if(content_type == 'application/json'):
                data = request.get_json()
            elif(content_type == 'application/bytes'):
                data=request.get_data()
                data = pickle.loads(data)

            jsMsg = json.dumps({"EMAIL" : data['EMAIL'] , "PASSWORD" : data['PASSWORD'] , "TYPE" : data['TYPE']})

            global ipAddress
            requestURL = f"http://{ipAddress}:5555/check_node?message={jsMsg}"
            response = requests.get(requestURL)
            if response.status_code == 200:
                if(response.json()['message'] == "Registered"):
                    return self.handle_session_creation_request(data)
                else:
                    return jsonify({'message': 'Invalid Email or Password'}), 200
            else:
                return jsonify({'message': 'Session Creation Failed'}), 404
            pass
        else:
            return jsonify({'message': 'Method not allowed'}), 405
        
        

    def initialize_customer_session(self , customerEmail):
        print(f"Session Inititalized for the Customer : {customerEmail}")
        global customerAgentsList
        sessionSupervisorPipe , userManagerPipe = multiprocessing.Pipe()
        self.mainServer_UserManagerPipe.send({"TYPE" : "NEW_SESSION" , "EMAIL" : customerEmail , "SUPERVISOR_PIPE" : sessionSupervisorPipe})
        currentSessionCustomerAgent = customerAgent(userManagerPipe)
        customerAgentsList[customerEmail] = currentSessionCustomerAgent
        messageForCustomerAgent = {"EMAIL" : customerEmail , "DATA" : session_creation_requests[customerEmail] , "DATETIME" : time.strftime("%Y-%m-%d : %H:%M:%S")}
        currentSessionCustomerAgent.initializeSession(messageForCustomerAgent)
        return True

    # @app.route('/initializeSession', methods=['POST'])
    def initialize_session_callback(self):
        # f = open("customerServerLog.txt" , "w")
        print("Initiate Session Called !!!")
        # f.write("Initiate Session Called !!!")
        if request.method == 'POST':
            global session_creation_requests
            global session_status
            data = request.get_json()
            #print(data)
            email = data['EMAIL']
            print(email)
            #print(email)
            if email in session_creation_requests.keys():
                if(self.initialize_customer_session(email) == True):
                    print(len(customerAgentsList))
                    # f.write(len(customerAgentsList))

                    del session_creation_requests[email]
                    session_status[email] = "RUNNING"
                    print(session_status[email])
                    # f.write(session_status[email])

                    print("Session Succefully Created and Status Updated !!!")
                    # f.write("Session Succefully Created and Status Updated !!!")

                    return jsonify({'message': 'Created'}), 200
                else:
                    print("Session Creation Failed")
                    return jsonify({'message': 'Failed'}), 404
            else:
                print("No Session Pending for the customer")
                return jsonify({'message': 'NO_PENDING_SESSION'}), 404
        else:
            return jsonify({'message': 'Method not allowed'}), 405
        
    # @app.route('/handleSessionRequests', methods=['PUT'])
    def handle_session_requests_callback(self):
        if request.method == 'PUT':
            data = request.get_json()
            email = data['EMAIL']
            agent = customerAgentsList[email]
            agent.handleSessionRequests(data)
            return jsonify({'message': 'Request Handled'}), 200
        else:
            return jsonify({'message': 'Method not allowed'}), 405


    # @app.route('/serverRunning' , methods=['GET'])
    def server_running_callback(self):
        print("Server Running Called !!!")
        if request.method == 'GET':
            return jsonify({'message': 'Running'}), 200
        else:
            return jsonify({'message': 'Method not allowed'}), 405
    
    # @app.route('/sessionSTATUS', methods=['GET'])
    def session_status_callback(self):
        print("Session Status Called !!!")
        if request.method == 'GET':
            message = request.args.get('message')
            data = json.loads(message)
            if data["TYPE"] == "CUSTOMERS":
                email = data["EMAIL"]
                global session_status
                if email in session_status.keys():
                    return jsonify({'message': session_status[email]}), 200
                else:
                    return jsonify({'message': 'IDLE'}), 200
            else:
                return jsonify({'message': 'Not a Valid Request'}), 400
        else:
            return jsonify({'message': 'Method not allowed'}), 405
        
    # @app.route('/updateSessionStatus', methods=['PUT'])
    def update_session_status_callback(self):
        if request.method == 'PUT':
            data = request.get_json()
            email = data['EMAIL']
            status = data['STATUS']
            global session_status
            session_status[email] = status
            if session_status[email] == "IDLE":
                del session_status[email]
            return jsonify({'message': 'Status Updated'}), 200
        else:
            return jsonify({'message': 'Method not allowed'}), 405

    

class CustomerServer():
    def __init__(self):
        self.userManager = None
        self.mainServer_UserManagerPipe = None
        # self.socketio = socketio
    
    def startServer(self , mainServer_UserManagerPipe = None):
        app = Flask(__name__)
        # app.config['SECRET_KEY'] = 'secret!'
        # self.socketio = SocketIO(app)

        self.mainServer_UserManagerPipe = mainServer_UserManagerPipe

        print("User Manager Pipe : " , self.mainServer_UserManagerPipe)

        global ipAddress
        ipAddress = "0.0.0.0"

        global session_creation_requests 
        global session_status
        global customerAgentsList
        session_creation_requests = {}
        customerAgentsList = {}
        session_status = {}


        # serverUserManager = userManager()
        # self.mainServer_UserManagerPipe , userManagerPipe = multiprocessing.Pipe()
        # userManager_Process = multiprocessing.Process(target=serverUserManager.Start , args=(userManagerPipe,))
        # userManager_Process.start()

        webhook_handler = WebHookHandler(app , self.mainServer_UserManagerPipe)

        print("Customer Server Starting !!!")
        Flask.run(app, host=ipAddress, port=5500 , debug=False)

        # ipAddressAndPort = '0.0.0.0:5500'
        # command = [
        #     'gunicorn',
        #     '--bind', ipAddressAndPort,
        #     '--workers', str(1),
        #     'credentialServer:app',  # Replace 'app' with your Flask application module name
        #     '--error-logfile' , 'customerServerLog.log',
        #     '--log-level' , 'debug'
        # ]
        # subprocess.run(command)


    
    def userMessageHandler(self , sid , message):
        self.socketio.emit('response', 'Message Received', room=sid)
        self.mainServer_UserManagerPipe.send({"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid})
        print("User Message Send to User Manager !!!")

        




if __name__ == "__main__":
    mainServer = CustomerServer()
    mainServer.startServer()
    
   