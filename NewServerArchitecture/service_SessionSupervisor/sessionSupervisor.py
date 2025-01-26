import socketserver
import argparse

import asyncio

import sys 
import os

import threading



sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))

from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue



class sessionSupervisorService:
    def __init__(self, httpServerHost, httpServerPort , supervisorID = None):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "SESSION_SUPERVISOR_EXCHANGE")
        self.apiServer = HTTPServer(httpServerHost, httpServerPort)

        self.ID = supervisorID

        self.CateringRequestLock = threading.Lock()
    
    async def ConfigureApiRoutes(self):
        pass



    async def handleCustomerAgentMessages(self, customerAgentMessage, response=False):
        pass

    async def callbackCustomerAgentMessages(self, message):
        pass



    async def handleUserManagerMessages(self, userManagerMessage, response=False):
        pass

    async def callbackUserManagerMessages(self, message):
        pass




    async def start_server(self):
        await self.messageQueue.InitializeMessageQueue()
        await self.messageQueue.AddQueueAndMapToCallback(f"{self.ID}_CA", self.callbackCustomerAgentMessages)
        await self.messageQueue.AddQueueAndMapToCallback(f"{self.ID}_UM", self.callbackUserManagerMessages)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureApiRoutes()
        await self.apiServer.run_app()
        


async def start_service():
    parser = argparse.ArgumentParser(description='Start a simple HTTP server.')
    parser.add_argument('--host', type=str, default='localhost', help='Hostname to listen on')
    parser.add_argument('--port', type=int, default=15000, help='Port to listen on')
    parser.add_argument('--id', type=str, default=None, help='Id of the Session Supervisor')
    args = parser.parse_args()

    print(args)

    server = sessionSupervisorService(host=args.host, port=args.port , supervisorID=args.id)
    server.start_server()

if __name__ == "__main__":
    asyncio.run(start_service())