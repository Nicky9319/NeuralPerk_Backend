import asyncio
import sys
import os
import threading

import socketio
import json


sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue
from WS_SERVER import WebSocketServer

class userWsServerService:
    def __init__(self, wsServerHost, wsServerPort, httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "USER_WS_SERVER_EXCHANGE")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.wsServer = WebSocketServer(wsServerHost, wsServerPort)
        self.wsServer.sio = socketio.AsyncServer(async_mode='aiohttp',ping_timeout=60, ping_interval=25 , max_http_buffer_size=1024*1024*100)

        self.CateringRequestLock = threading.Lock()

        self.clients = {}


    async def ConfigureHttpRoutes(self):
        pass

    async def ConfigureWsMethods(self):
        @self.wsServer.sio.event
        async def connect(sid, environ , auth=None):
            print(auth)
            
            exchangeName = "USER_MANAGER_EXCHANGE"
            routingKey = "UME_USER_SERVER"

            mainMessage = {"USER_ID" : sid}
            messageToSend = {"TYPE": "NEW_USER" , "DATA": mainMessage}

            await self.messageQueue.SendMessage(exchangeName, routingKey, messageToSend)

        @self.wsServer.sio.event
        async def disconnect(sid):
            del self.clients[sid]
            exchangeName = "USER_MANAGER_EXCHANGE"
            routingKey = "UME_USER_SERVER"

            mainMessage = {"USER_ID" : sid}
            messageToSend = {"TYPE": "REMOVE_USER" , "DATA": mainMessage}

            await self.messageQueue.SendMessage(exchangeName, routingKey, messageToSend)

        @self.wsServer.sio.on("GET_SID")
        async def get_sid(sid):
            return sid



    async def handleCommunicationInterfaceMessages(self, CIMessage , response=False):
        msgType = CIMessage['TYPE']
        msgData = CIMessage['DATA']
        if msgType == "SEND_BUFFER_REQUEST":
            userId = msgData['USER_ID']
            bufferUUID = msgData['BUFFER_UUID']
            await self.wsServer.sio.emit("REQUEST_BUFFER" , bufferUUID , to=userId)
            if response:
                return {"STATUS": "SUCCESS"}
        else:
            print("Unknown Message Type")
            print("Received Message: ", CIMessage)

    async def callbackCommunicationInterfaceMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        print(DecodedMessage)
        await self.handleCommunicationInterfaceMessages(DecodedMessage)
        self.CateringRequestLock.release()
        

    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("UWSSE_CI", self.callbackCommunicationInterfaceMessages)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()
        await asyncio.Event().wait()


async def start_service():
    service = userWsServerService("127.0.0.1" , 6000 , "127.0.0.1" , 6001)
    await service.startService()

if __name__ == "__main__":
    print("Starting User Ws Server Service")
    asyncio.run(start_service())

