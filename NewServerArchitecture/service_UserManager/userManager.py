import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue


class UserManagerService:
    def __init__(self, httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "USER_MANAGER_EXCHANGE")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)
        

    async def ConfigureServerRoutes(self):
        pass
    

    async def handleSupervisorMessages(self, supervisorRequest, response=False):
        pass

    async def callbackSupervisorMessages(self, message):
        pass


    async def handleCustomerServerMessages(self, customerServerRequest, response=False):
        pass

    async def callbackCustomerServerMessages(self , message):
        pass


    async def handleUserServerMessages(self, userServerRequest, response=False):
        pass

    async def callbackUserServerMessages(self, message):
        pass

    
    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("UME_USER_SERVER", self.callbackUserServerMessages)
        await self.messageQueue.AddQueueAndMapToCallback("UME_CUSTOMER_SERVER", self.callbackCustomerServerMessages)
        await self.messageQueue.AddQueueAndMapToCallback("UME_SUPERVISOR", self.callbackSupervisorMessages)
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureServerRoutes()
        await self.httpServer.run_app()



async def start_Service():
    service = UserManagerService('127.0.0.1', 20000)
    await service.startService()


if __name__ == "__main__":
    print("Starting User Manager Service")
    asyncio.run(start_Service())

