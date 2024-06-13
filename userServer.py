from flask import Flask, jsonify , request
from flask_socketio import SocketIO , emit

from customerAgent import customerAgent


class WebSocketServer:
    def __init__(self, app , socketio , userServer_UserManagerPipe=None):
        self.app = app
        self.socketio = socketio
        self.clients = {}
        self.userServer_UserManagerPipe = userServer_UserManagerPipe
        self.app.add_url_rule('/sendMessageToParticularUser', 'sendMessageToParticularUser', self.sendMessageToParticularUser, methods=['POST'])

    def register(self, event, handler):
        @self.socketio.on(event)
        def handle_event(*args):
            handler(request.sid, *args)

    def connect(self):
        @self.socketio.on('connect')
        def handle_connect():
            sid = request.sid
            print(f'Client {sid} connected')
            emit('response', 'Connected', room=sid)
            self.userServer_UserManagerPipe.send({"TYPE" : "NEW_USER" , "USER_ID" : sid})

    def disconnect(self):
        @self.socketio.on('disconnect')
        def handle_disconnect():
            sid = request.sid
            del self.clients[sid]
            print(f'Client {sid} disconnected')
    
    # @app.route('/sendMessageToParticularUser', methods=['POST'])
    def sendMessageToParticularUser(self):
        if request.method == 'POST':
            data = request.get_json()
            userId = data['USER_ID']
            message = data['DATA']
            self.socketio.emit('response', message, room=userId)
            return jsonify({'message': 'Message Sent'}), 200
        else:
            return jsonify({'message': 'Method not allowed'}), 405




class UserServer():
    def __init__(self , socketio=None):
        self.userManager = None
        # self.socketio = socketio
    
    def startServer(self, userServer_UserManagerPipe):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(app)

        self.userServer_UserManagerPipe = userServer_UserManagerPipe

        global ipAddress
        ipAddress = "127.0.0.1"

        webSocketServer = WebSocketServer(app , self.socketio , self.userServer_UserManagerPipe)

        webSocketServer.register('USER_MESSAGE' , self.userMessageHandler)
        webSocketServer.connect()
        webSocketServer.disconnect()

        print("User Server Starting !!!")
        self.socketio.run(app, host=ipAddress, port=6000 , debug = False)

    def userMessageHandler(self , sid , message):
        self.socketio.emit('response', 'Message Received', room=sid)
        self.userServer_UserManagerPipe.send({"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid})
        print("User Message Send to User Manager !!!")
