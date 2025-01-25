import asyncio
import sys
import os
import threading

import socketio

from fastapi import Request

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class userHttpServerService:
    def __init__(self, httpServerHost, httpServerPort, apiServerHost, apiServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "USER_HTTP_SERVER_EXCHANGE")
        self.apiServer = HTTPServer(apiServerHost, apiServerPort)
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

    async def ConfigureHTTPRoutes(self):
        pass
    
    async def ConfigureAPIRoutes(self):
        pass
    

    
    async def handleCommunicationInterfaceMessages(self, CIMessage , response=False):
        msgType = CIMessage['TYPE']
        msgData = CIMessage['DATA']
        pass

    async def callbackCommunicationInterfaceMessages(self, message):
        DecodedMessage = message.body.decode()
        self.CateringRequestLock.acquire()
        await self.handleCommunicationInterfaceMessages(DecodedMessage)
        self.CateringRequestLock.release()
        

    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("UHTTPSE_CI", self.callbackCommunicationInterfaceMessages)
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        asyncio.create_task(self.apiServer.run_app())

        await self.ConfigureHTTPRoutes()
        await self.httpServer.run_app()



