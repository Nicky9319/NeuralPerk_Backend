import asyncio
import sys
import os
import threading

import uuid

import json

from fastapi import Request,  Response

import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class CommunicationInterfaceService():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "COMMUNICATION_INTERFACE_EXCHANGE")
        self.apiServer = HTTPServer(httpServerHost, httpServerPort)

        self.CateringRequestLock = threading.Lock()



    async def getServiceURL(self, serviceName):
        servicePortMapping = json.load(open("ServiceURLMapping.json"))
        return servicePortMapping[serviceName]

    async def ConfigureApiRoutes(self):
        pass





    async def sendMessageToUserManager(self, userManagerMessage):
        print("Sending Message to User Manager")
        exchangeName = "USER_MANAGER_EXCHANGE"
        routing_key = "UME_USER_SERVER"
        messageInJson = json.dumps(userManagerMessage)
        await self.messageQueue.PublishMessage(exchangeName, routing_key, messageInJson)
        print("Message Sent to User Manager")

    async def SendMessageToHttpServer(self, messageToSend):
        exchangeName = "USER_HTTP_SERVER_EXCHANGE"
        routing_key = "UHTTPSE_CI"
        messageInJson = json.dumps(messageToSend)
        await self.messageQueue.PublishMessage(exchangeName, routing_key, messageInJson)

    async def sendMessageToWsServer(self, messageToSend):
        exchangeName = "USER_WS_SERVER_EXCHANGE"
        routing_key = "UWSSE_CI"
        messageInJson = json.dumps(messageToSend)
        await self.messageQueue.PublishMessage(exchangeName, routing_key, messageInJson)
        
    async def sendMessageToUser(self, userId, message):
        generateMessageUUID = str(uuid.uuid4())
        
        mainMessage = {"BUFFER_UUID" : generateMessageUUID , "BUFFER_MSG" : message}
        messageToSend = {"TYPE": "ADD_BUFFER_MSG" , "DATA": mainMessage}

        userHttpServerServiceURL = await self.getServiceURL("USER_HTTP_SERVER")
        response = requests.post(f"http://{userHttpServerServiceURL}/CommunicationInterface/AddBufferMsg", json=messageToSend)
        if response.status_code == 200:
            print("Buffer Message Added to User")
            mainMessage = {"USER_ID" : userId , "BUFFER_UUID" : generateMessageUUID}
            messageToSend = {"TYPE": "SEND_BUFFER_REQUEST" , "DATA": mainMessage}
            await self.sendMessageToWsServer(messageToSend)

            

    
    async def handleUserManagerMessages(self, userManagerMessage, response=False):
        print(type(userManagerMessage))
        msgType = userManagerMessage['TYPE']
        msgData = userManagerMessage['DATA']
        responseMsg = None
        if msgType == "SEND_MESSAGE_TO_USER":
            userId = msgData["USER_ID"]
            messageForUser = msgData["MESSAGE_FOR_USER"]
            await self.sendMessageToUser(userId, messageForUser)
        else:
            print("Unknown Message Type")
            print("Received Message: ", userManagerMessage)
            responseMsg = {"STATUS" : "FAILED" , "ERROR" : "Unknown message type"}

        if response:
            return responseMsg

    async def callbackUserManagerMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        print(type(DecodedMessage))
        self.CateringRequestLock.acquire()
        await self.handleUserManagerMessages(DecodedMessage)
        self.CateringRequestLock.release()



    async def handleUserHttpServerMessages(self, UserHttpServerMessage, response=False):
        msgType = UserHttpServerMessage['TYPE']
        msgData = UserHttpServerMessage['DATA']
        responseMsg = None
        if msgType == "MESSAGE_FOR_USER_MANAGER":
            print("User Http Server Asked to Forward Message to User Manager")
            await self.sendMessageToUserManager(msgData)
            responseMsg = {"STATUS" : "SUCCESS"}
        else:
            print("Unknown Message Type")
            print("Received Message: ", UserHttpServerMessage)
            responseMsg = {"STATUS" : "FAILED" , "ERROR" : "Unknown message type"}
        
        if response:
            return responseMsg

    async def callbackUserHttpServerMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        await self.handleUserHttpServerMessages(DecodedMessage)
        self.CateringRequestLock.release()
        


    async def handleUserWsServerMessages(self, UserWsServerMessage, response=False):
        msgType = UserWsServerMessage['TYPE']
        msgData = UserWsServerMessage['DATA']
        if msgType == "MESSAGE_FOR_USER_MANAGER":
            print("User Ws Server Asked to Forward Message to User Manager")
            await self.sendMessageToUserManager(msgData)
            responseMsg = {"STATUS" : "SUCCESS"}
        else:
            print("Unknown Message Type")
            print("Received Message: ", UserWsServerMessage)
            responseMsg = {"STATUS" : "FAILED" , "ERROR" : "Unknown message type"}
        
        if response:
            return responseMsg

    async def callbackUserWsServerMessages(self , message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)
        self.CateringRequestLock.acquire()
        await self.handleUserWsServerMessages(DecodedMessage)
        self.CateringRequestLock.release()



    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("CIE_USER_MANAGER", self.callbackUserManagerMessages, auto_delete = True)
        await self.messageQueue.AddQueueAndMapToCallback("CIE_USER_HTTP_SERVER", self.callbackUserHttpServerMessages, auto_delete = True)
        await self.messageQueue.AddQueueAndMapToCallback("CIE_USER_WS_SERVER", self.callbackUserWsServerMessages, auto_delete = True)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureApiRoutes()
        await self.apiServer.run_app()


async def start_service():
    service = CommunicationInterfaceService("127.0.0.1" , 7000)
    await service.startService()

if __name__ == "__main__":
    print("Starting Communication Interface Service")
    asyncio.run(start_service())