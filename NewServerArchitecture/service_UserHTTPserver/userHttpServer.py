import asyncio
import sys
import os
import threading

import socketio
import json
import pickle

import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class userHttpServerService:
    def __init__(self, httpServerHost, httpServerPort, apiServerHost, apiServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "USER_HTTP_SERVER_EXCHANGE")
        self.apiServer = HTTPServer(apiServerHost, apiServerPort)
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.bufferMsgs = {}



    async def handleUserMessage(self, userMessage):
        msgType = userMessage['TYPE']
        msgData = userMessage['DATA']
        if msgType == "FRAME_RENDERED":
            message = msgData["MESSAGE"]
            userId = msgData["USER_ID"]
            mainMessage = {"MESSAGE" : msgData , "USER_ID" : userId}
            messageToSend = {"TYPE" : "USER_MESSAGE" , "DATA" : mainMessage}
            await self.sendMessageToUserManager(messageToSend)
            return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
        elif msgType == "RENDER_COMPLETED":
            userId = msgData["USER_ID"]
            mainMessage = {"MESSAGE" : msgData , "USER_ID" : userId}
            messageToSend = {"TYPE" : "USER_MESSAGE" , "DATA" : mainMessage}
            self.sendMessageToUserManager(messageToSend)
            return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
        elif msgType == "TEST":  
            print("Test message Received : " , message["DATA"])
            return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)
        else:
            print("Received Normal Message !!!")
            return JSONResponse(content={"DATA" : "RECEIVED" , "TIME" : time.time()}, status_code=200)


    async def RefineDataFromMetaData(self, bufferMsg):
        MetaDataType = bufferMsg["META_DATA"]
        if MetaDataType == "EXTRACT_BLEND_FILE_FROM_PATH":
            def getBlendBinaryFromPath(blendPath):
                print(f"Blender File Path : {bufferMsg['DATA']}") 
                
                fileBinary = None
                with open(bufferMsg["DATA"] , 'rb') as file:
                    fileBinary =  file.read()
                
                return fileBinary
                
                
            bufferMsg["DATA"] = getBlendBinaryFromPath(bufferMsg["DATA"])
        else:
            pass

        return bufferMsg

    async def ConfigureHTTPRoutes(self):
        @self.httpServer.app.get("/")
        async def getDataFromServer(bufferUUID: str):
            if bufferUUID in self.bufferMsgs.keys():
                bufferMsg = self.bufferMsgs[bufferUUID]

                if type(bufferMsg) == dict and "META_DATA" in bufferMsg.keys():
                    bufferMsg = self.RefineDataFromMetaData(bufferMsg)

                del self.bufferMsgs[bufferUUID]
                return Response(content=pickle.dumps(bufferMsg), status_code=200, media_type="application/octet-stream")
            return Response(content=pickle.dumps({"message": "No Buffer Message"}), status_code=400, media_type="application/octet-stream")

        @self.httpServer.app.post("/")
        async def sendDataToServer(request: Request):
            data = None
            if request.headers.get("content-type") == "application/octet-stream":
                data = await request.body()
                data = pickle.loads(data)
            else:
                data = await request.json()

            requestResponse = await self.handleUserMessage(data)
            return requestResponse


    async def ConfigureAPIRoutes(self):
        @self.apiServer.app.post("/CommunicationInterface/AddBufferMsg")
        async def addBufferMsg(request: Request):
            data = await request.json()
            response = await self.handleCommunicationInterfaceMessages(data, response=True)
            return Response(content=json.dumps(response), media_type="application/json")
    


    async def handleCommunicationInterfaceMessages(self, CIMessage , response=False):
        msgType = CIMessage['TYPE']
        msgData = CIMessage['DATA']
        responseMsg = None
        if msgType == "ADD_BUFFER_MSG":
            print("Adding buffer message")
            bufferUUID = msgData['BUFFER_UUID']
            bufferMsg = msgData['BUFFER_MSG']
            self.bufferMsgs[bufferUUID] = bufferMsg
            responseMsg = {"STATUS" : "SUCCESS"}
        else:
            print("Unknown message type")
            print(CIMessage)
            responseMsg = {"STATUS" : "FAILED" , "ERROR" : "Unknown message type"}
            
        if response:
            return responseMsg
        
    async def callbackCommunicationInterfaceMessages(self, message):
        DecodedMessage = message.body.decode()
        DecodedMessage = json.loads(DecodedMessage)

        await self.handleCommunicationInterfaceMessages(DecodedMessage)
        


    async def sendMessageToUserManager(self, mainMessage):
        exchangeName = "COMMUNICATION_INTERFACE_EXCHANGE"
        routingKey = "CIE_USER_HTTP_SERVER"

        messageToSend = {"TYPE" : "MESSAGE_FOR_USER_MANAGER" , "DATA" : mainMessage}

        await self.messageQueue.PublishMessage(exchangeName, routingKey, messageToSend)

    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("UHTTPSE_CI", self.callbackCommunicationInterfaceMessages)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        asyncio.create_task(self.apiServer.run_app())

        await self.ConfigureHTTPRoutes()
        await self.httpServer.run_app()




async def start_service():
    service = userHttpServerService("127.0.0.1" , 8000 , "127.0.0.1" , 8001)
    await service.startService()


if __name__ == "__main__":
    asyncio.run(start_service())
