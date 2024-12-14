import pickle
import asyncio
import uuid

from flask import Flask, jsonify , request
# from flask_sock import Sock
# from flask_socketio import SocketIO, emit


import concurrent.futures

import socketio
import eventlet
import eventlet.wsgi
import pickle

# import numpy as np
import time
import threading

import logging

from customerAgent import customerAgent

import redis.asyncio as redis

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import uvicorn

import multiprocessing

import json

from aiohttp import web



def websocket_server_start():
    websocket_server = webSocketServer("0.0.0.0", 6000)
    asyncio.run(websocket_server.startServer())

class webSocketServer:
    def __init__(self, ipAddress="0.0.0.0", port = 6000, redis_url = "redis://localhost:10000"):
        self.sio = socketio.AsyncServer(async_mode='aiohttp',ping_timeout=60, ping_interval=25 , max_http_buffer_size=1024*1024*100)
        self.app = web.Application()
        self.sio.attach(self.app)
        self.port = port
        self.ipAddress = ipAddress
        self.clients = {}
        self.socketLock = threading.Lock()
        self.redis_url = redis_url
        self.channel_name = "WS_SERVER"

        self.userListLength = 0
    
    def methods(self):
        @self.sio.event
        async def connect(sid, environ):
            # self.user_byte_stream_mapping[sid] = bytearray()
            self.socketLock.acquire()
            await self.sio.emit('message', pickle.dumps({"TYPE" : "RESPONSE" , "DATA" : "CONNECTED" , "TIME" : time.time()}), room=sid)
            self.socketLock.release()
            print(f"A New User with ID {sid} Connected")

            await self.sendMessageToUserManager({"TYPE" : "NEW_USER" , "USER_ID" : sid})
            # await self.publishRedisMsg('CI' , json.dumps({"TYPE" : "MESSAGE_FOR_USER_MANAGER", "DATA" : {"TYPE" : "NEW_USER" , "USER_ID" : sid}}))

            self.clients[sid] = environ
    
        @self.sio.event
        async def disconnect(sid):
            del self.clients[sid]
            print(f'Client {sid} disconnected')

            
            # await self.publishRedisMsg('CI' , json.dumps({"TYPE" : "MESSAGE_FOR_USER_MANAGER", "DATA" : {"TYPE" : "REMOVE_USER" , "USER_ID" : sid}}))
            await self.sendMessageToUserManager({"TYPE" : "REMOVE_USER" , "USER_ID" : sid})
        
        
        @self.sio.on("GET_SID")
        async def get_sid(sid):
            return sid


    async def sendMessageToUserManager(self, message):
        await self.publishRedisMsg('CI' , pickle.dumps({"TYPE" : "MESSAGE_FOR_USER_MANAGER", "DATA" : message}))



    async def parserRedisMessage(self, message):
        message = pickle.loads(message)
        messageType = message["TYPE"]
        if messageType == "SEND_CALL_BUFFER_REQUEST":
            print("SEND_CALL_BUFFER_REQUEST")
            userID = message["USER_ID"]
            await self.sio.emit('REQUEST_BUFFER', message["BUFFER_UUID"], to = userID)
        else:
            print("Unknown Message Type")
        
    async def readRedisQueue(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel_name)
        print(f"Subscribed to Redis queue: {self.channel_name}")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                print(f"{self.channel_name}")
                await self.parserRedisMessage(message['data'])



    async def publishRedisMsg(self, channel , message):
        await self.redis.publish(channel , message)

    
    async def startServer(self):
        # await self.initRedis()
        self.redis = await redis.from_url(self.redis_url, decode_responses=False)
        print("Redis Connection Established")
        self.methods()

        asyncio.create_task(self.readRedisQueue())

        print('Starting WS Server')

        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.ipAddress, self.port)
        await site.start()

        print('WS Server Started at ' , self.ipAddress , ':' , self.port)
        await asyncio.Event().wait()







def http_server_start():
    http_server = httpServer()

    http_server.app.add_event_handler("startup", http_server.on_startup)
    http_server.app.add_event_handler("shutdown", http_server.on_shutdown)

    http_server.startServer()

class httpServer:
    def __init__(self, host="localhost" , port=8000 , redis_url = "redis://localhost:10000"):
        self.app = FastAPI()
        self.host = host
        self.port = port
        self.redis_url = redis_url
        self.channel_name = "HTTP_SERVER"
        self.redis = None
        self.pubsub = None

        self.bufferMsgs = {}

        # Setting up routes
        self.routes()


    
    def routes(self):
        """Set up basic FastAPI routes."""

        @self.app.get("/")
        async def getDataFromServer(bufferUUID: str):
            print(bufferUUID)
            if bufferUUID in self.bufferMsgs.keys():
                bufferMsg = self.bufferMsgs[bufferUUID]
                del self.bufferMsgs[bufferUUID]
                return Response(content=pickle.dumps(bufferMsg), status_code=200, media_type="application/octet-stream")
            return Response(content=pickle.dumps({"message": "No Buffer Message"}), status_code=400, media_type="application/octet-stream")


    
        async def parserClientMessage(message):
            userID = message["USER_ID"]
            message = message["MESSAGE"]
            messageType = message["TYPE"]
            if messageType == "FRAME_RENDERED":
                print("Received Rendered Image")
                msgToUserManager = {"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : userID}
                await self.sendMessageToUserManager(msgToUserManager)
                return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
            elif messageType == "RENDER_COMPLETED":
                print("User Says it has Completed the Process !!!")
                msgToUserManager = {"TYPE" : "USER_MESSAGE" , "MESSAGE" : message , "USER_ID" : userID}
                self.sendMessageToUserManager(msgToUserManager)
                return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
            elif messageType == "TEST":  
                print("Test message Received : " , message["DATA"])
                return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
            else:
                print("Received Normal Message !!!")
                return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)

        @self.app.post("/")
        async def sendDataToServer(request: Request):
            print("Received ")
            data = None
            if request.headers["Content-Type"] == "application/octet-stream":
                data = await request.body()
                data = pickle.loads(data)
            elif request.headers["Content-Type"] == "application/json":
                data = await request.json()

            requestResponse  = await parserClientMessage(data)
            return requestResponse


    async def sendMessageToUserManager(self, message):
            await self.publishRedisMsg('CI' , pickle.dumps({"TYPE" : "MESSAGE_FOR_USER_MANAGER", "DATA" : message}))


    async def publishRedisMsg(self, channel , message):
        await self.redis.publish(channel , message)

    async def parserRedisMessage(self, message):
        message = pickle.loads(message)
        messageType = message["TYPE"]
        print(messageType)
        if messageType == "ADD_BUFFER_MSG":
            bufferUUID = message["BUFFER_UUID"]
            bufferMsg = message["BUFFER_MSG"]
            self.bufferMsgs[bufferUUID] = bufferMsg
            print("Buffer Message Added")
        else:
            print("Unknown Message Type")

    async def readRedisQueue(self):
        """Async loop to listen to Redis channel."""
        print("Starting Redis message listener...")
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message:
                print(f"{self.channel_name}")
                await self.parserRedisMessage(message['data'])
                # Act on the message (process it here)

            # Non-blocking sleep
            await asyncio.sleep(0.1)

    async def on_startup(self):
        # await self.init_redis()
        print("Initializing Redis...")
        self.redis = redis.from_url(self.redis_url, decode_responses=False)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(self.channel_name)
        print(f"Subscribed to Redis channel: {self.channel_name}")
        asyncio.create_task(self.readRedisQueue())

    async def on_shutdown(self):
        print("Shutting down Redis connection...")
        await self.redis.close()
    

    def startServer(self):
        uvicorn.run(self.app, host="localhost", port=8000)





class CommunicationInterface():
    def __init__ (self, redis_url = "redis://localhost:10000", userServer_UserManagerPipe = None):   
        self.userServer_UserManagerPipe = userServer_UserManagerPipe
        print(type(self.userServer_UserManagerPipe))
        self.redis = redis.from_url(redis_url , decode_responses=False)
        self.pubsub = self.redis.pubsub()
        self.channel_name = "CI"

    async def sendMessageToUser(self, userId , message):
        generatedMessageCode = str(uuid.uuid4())
        await self.publishMsgToRedis("HTTP_SERVER" , pickle.dumps({"TYPE" : "ADD_BUFFER_MSG" , "BUFFER_UUID" : generatedMessageCode , "BUFFER_MSG" : message}))
        time.sleep(10)
        await self.publishMsgToRedis("WS_SERVER" , pickle.dumps({"TYPE" : "SEND_CALL_BUFFER_REQUEST" , "USER_ID" : userId , "BUFFER_UUID" : generatedMessageCode}))



    async def parserUserManagerMessage(self, message):
        if message["TYPE"] == "SEND_MESSAGE_TO_USER":
            userID = message["DATA"]["USER_ID"]
            actualMsg = message["DATA"]["DATA"]
            await self.sendMessageToUser(userID , actualMsg)

    async def listenToUserManager(self):
        while True:
            if self.userServer_UserManagerPipe.poll():
                message = self.userServer_UserManagerPipe.recv()
                await self.parserUserManagerMessage(message)
                # if message["TYPE"] == "SEND_MESSAGE_TO_USER":
                #     self.sendMessageToUser(message["USER_ID"] , message["DATA"])
            else:
                await asyncio.sleep(1)
        


    async def parserRedisMessage(self, message):
        message = pickle.loads(message)
        messageType = message["TYPE"]

        if messageType == "MESSAGE_FOR_USER_MANAGER":
            print("Message Being Forwarded to User Manager")
            self.userServer_UserManagerPipe.send(message["DATA"])
        else:
            print("Unknown Message Type")
        
    async def listenToRedisQueue(self):
        await self.pubsub.subscribe(self.channel_name)
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message:
                print(f"{self.channel_name}")
                await self.parserRedisMessage(message['data'])


    async def publishMsgToRedis(self, channel , message):
        await self.redis.publish(channel , message)


    def startListeningToUserManager(self):
        asyncio.run(self.listenToUserManager())

    def startCommunicationInterface(self):
        # asyncio.to_thread(self.listenToUserManager)
        userManagerListeningThread = threading.Thread(target=self.startListeningToUserManager)
        userManagerListeningThread.start()
        # self.listenToRedisQueue()
        asyncio.run(self.listenToRedisQueue())
        print("Testing End of File")
        userManagerListeningThread.join()






class UserServer():
    def __init__(self , socketio=None):
        self.userManager = None
        # self.socketio = socketio

    # def start_Server(self, userServer_UserManagerPipe = None):
    #     logger = logging.getLogger('socketio_server')
    #     logger.setLevel(logging.DEBUG)  # Set the desired logging level
    #     file_handler = logging.FileHandler('serverConnection.log')
    #     file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    #     logger.addHandler(file_handler)

    #     sio = socketio.Server(ping_timeout=60, ping_interval=25 , max_http_buffer_size=1024*1024*150, logger=logger,engineio_logger=logger)
    #     app = socketio.WSGIApp(sio) 
    #     socketLock = threading.Lock()

        

    #     webhook_App = Flask(__name__)
    #     sessionSupervisor = sessionSupervisorInteraction(sio , socketLock , userServer_UserManagerPipe)
        

    #     socketServer = webSocketServer(app , sio , socketLock , sessionSupervisor , userServer_UserManagerPipe)
    #     socketServer.connect()
    #     socketServer.disconnect()
    #     socketServer.message_in_batches()
    #     socketServer.message()

    #     global ipAddress
    #     ipAddress = "0.0.0.0"
    #     # ipAddress = "192.168.0.147"
    #     # ipAddress = '127.0.0.1'
    #     # listenToUserManagerThread = threading.Thread(target=sessionSupervisor.listenToUserManager)
    #     # listenToUserManagerThread.start()

    #     eventlet.wsgi.server(eventlet.listen((ipAddress, 6000)), app)
    #     # listenToUserManagerThread.join()


    
    def startServer(self, userServer_UserManagerPipe = None):
        websocketServerProcess = multiprocessing.Process(target=websocket_server_start)
        websocketServerProcess.start()

        httpServerProcess = multiprocessing.Process(target=http_server_start)
        httpServerProcess.start()

        communicationInterface = CommunicationInterface(userServer_UserManagerPipe = userServer_UserManagerPipe)
        communicationInterface.startCommunicationInterface()

        websocketServerProcess.join()
        httpServerProcess.join()

    


        