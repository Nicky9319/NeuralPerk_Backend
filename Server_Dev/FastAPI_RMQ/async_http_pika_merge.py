import asyncio
from fastapi import FastAPI
import uvicorn

import asyncio
import aio_pika




class MessageQueueListener:
    def __init__(self, ConnectionURL, ExchangeName=""):
        self.ExchangeName = ExchangeName
        self.ConnectionURL = ConnectionURL
        self.Connection = None
        self.Channel = None
        self.QueueList = []
        self.QueueToCallbackMapping = {}  


    async def InitializeConnection(self):
        self.Connection = await aio_pika.connect_robust(self.ConnectionURL)
        self.Channel = await self.Connection.channel()

    async def BoundeQueueToExchange(self):
        for queues in self.QueueList:
            self.Channel.queue_bind(exchange=self.ExchangeName, queue=queues)
        
    async def AddNewQueue(self, QueueName):
        queue = await self.Channel.declare_queue(QueueName, durable=True)
        self.QueueList.append(queue)
    
    async def MapQueueToCallback(self, QueueName, Callback):
        self.QueueToCallbackMapping[QueueName] = Callback

    async def AddQueueAndMapToCallback(self, QueueName, Callback):
        await self.AddNewQueue(QueueName)
        await self.MapQueueToCallback(QueueName, Callback)

    async def StartListeningToQueue(self):
        for queue in self.QueueList:
            await queue.consume(self.QueueToCallbackMapping[queue.name])

    async def PublishMessage(self, exchangeName , routingKey, message):
        pass
        # exchange = await self.Channel.declare_exchange(exchangeName)
        # await exchange.publish(
        #     aio_pika.Message(body=json.dumps(message).encode()),
        #     routing_key=routingKey
        # )

    async def CloseConnection(self):
        await self.Connection.close()

class HTTPServer:
    def __init__(self, host="127.0.0.1", port=54545):
        self.app = FastAPI()
        self.host = host
        self.port = port

    async def run_app(self):
        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()


class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueueListener("amqp://guest:guest@localhost/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def ConfigureServerRoutes(self):
        @self.httpServer.app.get("/")
        async def read_root():
            print("Running Through Someone Else")
            return {"message": "Hello World"}
    

    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        await self.messageQueue.StartListeningToQueue()
        await self.ConfigureServerRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('127.0.0.1', 8000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
