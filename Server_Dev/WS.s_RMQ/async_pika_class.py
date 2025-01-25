import asyncio
import aio_pika

import json

import time

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
        exchange = await self.Channel.declare_exchange(exchangeName)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routingKey
        )

    async def CloseConnection(self):
        await self.Connection.close()


async def fun1(message: aio_pika.IncomingMessage):
    msg = message.body.decode()
    print(json.loads(msg))

async def fun2(message: aio_pika.IncomingMessage):
    msg = message.body.decode()
    print(msg)


async def main():


    messageQueue = MessageQueueListener("amqp://guest:guest@localhost/", "")
    await messageQueue.InitializeConnection()
    await messageQueue.AddQueueAndMapToCallback("queue1", fun1)
    await messageQueue.AddQueueAndMapToCallback("queue2", fun2)

    await messageQueue.StartListeningToQueue()


if __name__ == "__main__":
    asyncio.run(main())

