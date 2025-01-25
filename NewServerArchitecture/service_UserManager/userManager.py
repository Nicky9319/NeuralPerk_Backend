import asyncio
import sys
import os
import threading

import json

from fastapi import Request

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue


class UserManagerService:
    def __init__(self, httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "USER_MANAGER_EXCHANGE")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.users = []
        self.userToSupervisorIdMapping = {} # Email Address of Customer Linked to the User associated with it
        self.supervisorToRoutingKeyMapping = {} # Supervisor Name to Routing Key Mapping
        
        self.CateringRequestLock = threading.Lock()
        

    async def ConfigureHttpRoutes(self):
        @self.httpServer.app.get('/SessionSupervisor')
        async def handleGetSessionSupervisor():
            pass
        
        @self.httpServer.app.post('/SessionSupervisor/NewSession')
        async def handlePostSessionSupervisor(request : Request):
            data = await request.json()
            response = await self.handleSupervisorMessages(data , response=True)
            return response

        @self.httpServer.app.get('/CustomerServer')
        async def handleGetCustomerServer():
            pass

        @self.httpServer.app.post('/CustomerServer')
        async def handlePostCustomerServer():
            pass

        @self.httpServer.app.get('/UserServer')
        async def handleGetUserServer():
            pass

        @self.httpServer.app.post('/UserServer')
        async def handlePostUserServer():
            pass

    

    async def handleSupervisorMessages(self, supervisorMessage, response=False):
        msgType = supervisorMessage['TYPE']
        msgData = supervisorMessage['DATA']
        if msgType == "NEW_SESSION":
            pass
        elif msgType == "ADDITIONAL_USERS":
            pass
        elif msgType == "SEND_MESSAGE_TO_USER":
            pass
        elif msgType == "USER_RELEASED":
            pass
        elif msgType == "INITIALIZE_SESSION":
            sessionId = msgData["SESSION_SUPERVISOR_ID"]
            self.userToSupervisorIdMapping[sessionId] = []
            self.supervisorToRoutingKeyMapping[sessionId] = f"SSE_{sessionId}_UM"
            if response:
                return {"STATUS": "SUCCESS"}
        else:
            print("Unknown Message Type")
            print("Received Message: ", supervisorMessage)

    async def callbackSupervisorMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        await self.handleSupervisorMessages(DecodedMessage)
        self.CateringRequestLock.release()
        


    async def handleCustomerServerMessages(self, customerServerMessage, response=False):
        msgType = customerServerMessage['TYPE']
        print(customerServerMessage)

    async def callbackCustomerServerMessages(self , message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        await self.handleCustomerServerMessages(DecodedMessage)
        self.CateringRequestLock.release()


    async def handleUserServerMessages(self, userServerMessage, response=False):
        msgType = userServerMessage['TYPE']
        msgData = userServerMessage['DATA']
        if msgType == "USER_MESSAGE":
            userId = msgData["USER_ID"]
            userMessage = msgData["MESSAGE"]

            supervisorID = self.userToSupervisorIdMapping[userId]
            supervisorRoutingKey = self.supervisorToRoutingKeyMapping[supervisorID]

            exchangeName = "SESSION_SUPERVISOR_EXCHANGE"

            mainMessage = {"USER_ID" : userId , "MESSAGE" : userMessage}
            messageToSend = {"TYPE" : "USER_MESSAGE" , "DATA" : mainMessage}

            await self.messageQueue.PublishMessage(exchangeName, supervisorRoutingKey, messageToSend)
        elif msgType == "NEW_USER":
            self.users.append(msgData["USER_ID"])
        elif msgType == "REMOVE_USER":
            userId = msgData["USER_ID"]
            if userId in self.users:
                self.users.remove(userId)
            else:
                supervisorID = self.userToSupervisorIdMapping[userId]
                supervisorRoutingKey = self.supervisorToRoutingKeyMapping[supervisorID]

                exchangeName = "SESSION_SUPERVISOR_EXCHANGE"

                mainMessage = {"USER_ID" : userId , "TYPE" : "DISCONNECT"}
                messageToSend = {"TYPE" : "USER_MESSAGE" , "DATA" : mainMessage}

                await self.messageQueue.PublishMessage(exchangeName, supervisorRoutingKey, messageToSend)
        else:
            print("Unknown Message Type")
            print("Received Message: ", userServerMessage)

    async def callbackUserServerMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        await self.handleUserServerMessages(DecodedMessage)
        self.CateringRequestLock.release()

    
    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("UME_USER_SERVER", self.callbackUserServerMessages)
        await self.messageQueue.AddQueueAndMapToCallback("UME_CUSTOMER_SERVER", self.callbackCustomerServerMessages)
        await self.messageQueue.AddQueueAndMapToCallback("UME_SUPERVISOR", self.callbackSupervisorMessages)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureHttpRoutes()
        await self.httpServer.run_app()



async def start_service():
    service = UserManagerService('127.0.0.1', 20000)
    await service.startService()


if __name__ == "__main__":
    print("Starting User Manager Service")
    asyncio.run(start_service())

