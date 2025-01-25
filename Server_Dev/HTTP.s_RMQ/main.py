import pickle
import asyncio
import uuid


import pickle

import time

import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from ipaddress import ip_address, IPv4Address


import uvicorn

from aiohttp import web

import aio_pika




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

                if "META_DATA" in bufferMsg.keys():
                    if bufferMsg["META_DATA"] == "EXTRACT_BLEND_FILE_FROM_PATH":
                        def getBlendBinaryFromPath(blendPath):
                            print(bufferMsg)
                            print(f"Blender File Path : {bufferMsg['DATA']}") 
                            
                            fileBinary = None
                            with open(bufferMsg["DATA"] , 'rb') as file:
                                fileBinary =  file.read()
                            
                            print(len(pickle.dumps(fileBinary)))
                            return fileBinary
                            
                            
                        bufferMsg["DATA"] = getBlendBinaryFromPath(bufferMsg["DATA"])

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


    async def publishRabbitMqMsg(self, channel , message):
        await self.redis.publish(channel , message)

    async def parserRabbitMqMessage(self, message):
        pass

    async def readRabbitMqQueue(self,connection):
        async with connection:
            queue_name = "test_queue"

            # Creating channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            # Declaring queue
            queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
                queue_name,
                auto_delete=True
            )

            print("All Ready")

            async with queue.iterator() as queue_iter:
                print("Queue Iterator Started")
                # Cancel consuming after __aexit__
                async for message in queue_iter:
                    print("Message Received")
                    async with message.process():
                        print(message.body)

                        if queue.name in message.body.decode():
                            break
        



        # """Async loop to listen to Redis channel."""
        # print("Starting Redis message listener...")
        # while True:
        #     message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
        #     if message:
        #         print(f"{self.channel_name}")
        #         await self.parserRedisMessage(message['data'])
        #         # Act on the message (process it here)

        #     # Non-blocking sleep
        #     await asyncio.sleep(0.1)





    async def on_startup(self):
        pass
        loop = asyncio.get_event_loop()
        connection = await aio_pika.connect_robust(
            "amqp://guest:guest@127.0.0.1/", loop=loop
            )
        loop.create_task(self.readRabbitMqQueue(connection))
        
        # asyncio.create_task(self.readRedisQueue())

    async def on_shutdown(self):
        print("Shutting down Redis connection...")
        await self.redis.close()
        

    def startServer(self):
        uvicorn.run(self.app, host="0.0.0.0", port=8000)


http_server_start()
