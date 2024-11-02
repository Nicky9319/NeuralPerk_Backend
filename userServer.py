import pickle
import asyncio
import uuid

from flask import Flask, jsonify , request
from flask_sock import Sock
from flask_socketio import SocketIO, emit


import concurrent.futures

import socketio
import eventlet
import eventlet.wsgi
import pickle

import numpy as np
import time

import threading

from flask import Flask, jsonify , request



from customerAgent import customerAgent


class webSocketServer:
    def __init__(self, app , sio , lock , sessionSupervisorInteraction , userServer_UserManagerPipe=None):
        self.app = app
        self.sio = sio
        print("Sio of Websocket Server : " , self.sio)
        self.clients = {}
        self.socketLock = lock
        self.user_byte_stream_mapping = {}
        self.userServer_UserManagerPipe = userServer_UserManagerPipe
        
        if sessionSupervisorInteraction:
            self.sio.start_background_task(sessionSupervisorInteraction.listenToUserManager)
    


    def connect(self):
        @self.sio.event
        def connect(sid, environ):
            self.user_byte_stream_mapping[sid] = bytearray()
            self.socketLock.acquire()
            self.sio.emit('message', pickle.dumps({"TYPE" : "RESPONSE" , "DATA" : "CONNECTED" , "TIME" : time.time()}), room=sid)
            self.socketLock.release()
            print(f"A New User with ID {sid} Connected")
            self.userServer_UserManagerPipe.send({"TYPE" : "NEW_USER" , "USER_ID" : sid})
            self.clients[sid] = environ
    
    def disconnect(self):
        @self.sio.event
        def disconnect(sid):
            del self.clients[sid]
            print(f'Client {sid} disconnected')
            self.userServer_UserManagerPipe.send({"TYPE" : "REMOVE_USER" , "USER_ID" : sid})

    
    def parserMessage(self , sid , message):
        msgType = message["TYPE"]
        if msgType == "MODEL_GRADS":
            t1 = time.time()
            print("Received Model")
            t2 = message["TIME"]
            print("Time Taken to Send Model : " , t1-t2)
            #ser_data = pickle.dumps({"TYPE" : "MODEL" , "DATA" : "MODEL_WEIGHTS" , "TIME" : time.time()})
            print(sid)


            # f = open("user_server_params.txt" , "w")
            # f.write(str(message["DATA"]))

            msgToUserManager = {"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid}
            self.userServer_UserManagerPipe.send(msgToUserManager)
            #self.sio.emit('message', ser_data , room=sid) 
        elif msgType == "FRAME_RENDERED":
            print("Received Rendered Image")
            msgToUserManager = {"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid}
            self.userServer_UserManagerPipe.send(msgToUserManager)
        elif msgType == "RENDER_COMPLETED":
            print("User Says it has Completed the Process !!!")
            msgToUserManager = {"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid}
            self.userServer_UserManagerPipe.send(msgToUserManager)
        elif msgType == "TEST":  
            print("Test message Received : " , message["DATA"])
        else:
            print("Received Normal Message !!!")
            jsMsg = {"TYPE" : "RESPONSE" , "DATA" : "RECEIVED" , "TIME" : time.time()}
            print(jsMsg)
            ser_data = pickle.dumps(jsMsg)
            self.socketLock.acquire()
            # print("Socket Acquired !!!")
            self.sio.emit('message', ser_data , room=sid)
            # print("Socket Released !!!")
            self.socketLock.release()



    def userMessageHandler(self , sid , message):
        self.userServer_UserManagerPipe.send({"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : sid})
        print("User Message Send to User Manager !!!")

    def message_in_batches(self):
        @self.sio.on('message_in_batches')
        def my_message_in_batches(sid, data):
            #print("message Received !!!")
            self.user_byte_stream_mapping[sid].extend(data)

            if(b'<EOF>' in self.user_byte_stream_mapping[sid]):
                index = self.user_byte_stream_mapping[sid].index(b'<EOF>')
                print("Lenght of Byte Array : " , len(self.user_byte_stream_mapping[sid]))
                unpickledData = self.user_byte_stream_mapping[sid][:index]
                try:
                    message = pickle.loads(unpickledData)
                except:
                    print("Error in Unpickling the Data")
                    self.user_byte_stream_mapping[sid] = self.user_byte_stream_mapping[sid][index+5:]
                    print("Length of Remaining Byte Array : " , len(self.user_byte_stream_mapping[sid]))
                    return
                # print("Message Received in Batches : " , message)
                self.user_byte_stream_mapping[sid] = self.user_byte_stream_mapping[sid][index+5:]
                print("Length of Remaining Byte Array : " , len(self.user_byte_stream_mapping[sid]))
                #print(self.user_byte_stream_mapping[sid])
                self.socketLock.acquire()
                self.sio.emit('response', pickle.dumps({"TYPE" : "RESPONSE" , "DATA" : "RECEIVED" , "TIME" : time.time()}), room=sid)
                self.socketLock.release()
                #self.userMessageHandler(sid , message)
                self.parserMessage(sid , message)

    def message(self):
        @self.sio.on('message')
        def my_message(sid, data):
            message = pickle.loads(data)
            #print(message)
            self.socketLock.acquire()
            self.sio.emit('response', pickle.dumps({"TYPE" : "RESPONSE" , "DATA" : "RECEIVED" , "TIME" : time.time()}), room=sid)
            self.socketLock.release()
            #self.userMessageHandler(sid , message)
            self.parserMessage(sid , message)


class sessionSupervisorInteraction():
    def __init__(self, sio , lock , userServer_UserManagerPipe = None):
        self.sio = sio
        print("Sio Of User Server : " , self.sio)
        self.socketLock = lock
        self.userServer_UserManagerPipe = userServer_UserManagerPipe

    
    def sendMessageToParticularUser(self , message):
        data = message["DATA"]
        userId = message["USER_ID"]
        newData = pickle.dumps(data)
        print(f"To The Following User the Data is being Send : {userId}")
        print(f"Length of The Message that is being Send to the User : {len(newData)}")
        #print("Sleeping for Next 10 Seconds !!!")
        #time.sleep(10)
        self.socketLock.acquire()
        print("Socket Has Been Acquired !!!")
        self.sio.emit('message', newData, room=userId)
        self.socketLock.release()
        print("Message Send , Socket Released !!!")

    def listenToUserManager(self):
        print("Started Listening to the User Manager Messages !!!")
        while True:
            if self.userServer_UserManagerPipe.poll():
                message = self.userServer_UserManagerPipe.recv()
                print("Request Received From User Manager !!!")
                if message["TYPE"] == "SEND_MESSAGE_TO_USER":
                    print("The Request to Send Message to User is Being Executed !!!")
                    # with concurrent.futures.ThreadPoolExecutor() as executor:
                    #     future = executor.submit(self.sendMessageToParticularUser , message["DATA"])
                    #     result = future.result()
                    # self.sio.start_background_task(self.sendMessageToParticularUser , message["DATA"])
                    self.sendMessageToParticularUser(message["DATA"])
            else:
                #print("Sleeping For 1 Second to Listen to User Manager Messages !!!")
                eventlet.sleep(1.5)



class UserServer():
    def __init__(self , socketio=None):
        self.userManager = None
        # self.socketio = socketio

    def startServer(self, userServer_UserManagerPipe = None):
        sio = socketio.Server(ping_timeout=60, ping_interval=25 , max_http_buffer_size=1024*1024*150)
        app = socketio.WSGIApp(sio) 
        socketLock = threading.Lock()

        

        webhook_App = Flask(__name__)
        sessionSupervisor = sessionSupervisorInteraction(sio , socketLock , userServer_UserManagerPipe)
        

        socketServer = webSocketServer(app , sio , socketLock , sessionSupervisor , userServer_UserManagerPipe)
        socketServer.connect()
        socketServer.disconnect()
        socketServer.message_in_batches()
        socketServer.message()

        global ipAddress
        ipAddress = "0.0.0.0"
        # ipAddress = "192.168.0.147"
        # ipAddress = '127.0.0.1'
        # listenToUserManagerThread = threading.Thread(target=sessionSupervisor.listenToUserManager)
        # listenToUserManagerThread.start()

        eventlet.wsgi.server(eventlet.listen((ipAddress, 6000)), app)
        # listenToUserManagerThread.join()


        