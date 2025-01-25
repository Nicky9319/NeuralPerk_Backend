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


class QueueListener:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
        self.channel = None
        self.queueToCallbackMapping = {}

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.connection_string)
        self.channel = await self.connection.channel()

    async def setup_queue(self, queue_name, callback):
        queue = await self.channel.declare_queue(queue_name , durable=True)
        await queue.consume(callback)

    async def start_listening(self):
        # Define your callback functions here
        async def callback_queue1(message: aio_pika.IncomingMessage):
            async with message.process():
                print(f"Received message from queue1: {message.body.decode()}")

        async def callback_queue2(message: aio_pika.IncomingMessage):
            async with message.process():
                print(f"Received message from queue2: {message.body.decode()}")

        # Setup queues with their respective callbacks
        await self.setup_queue('queue1', callback_queue1)
        await self.setup_queue('queue2', callback_queue2)

    async def close(self):
        await self.connection.close()

async def fun1(message: aio_pika.IncomingMessage):
    msg = message.body.decode()
    print(json.loads(msg))

async def fun2(message: aio_pika.IncomingMessage):
    msg = message.body.decode()
    print(msg)


async def main():
    listener = QueueListener("amqp://guest:guest@localhost/")
    await listener.connect()


    messageQueue = MessageQueueListener("amqp://guest:guest@localhost/", "")
    await messageQueue.InitializeConnection()
    await messageQueue.AddQueueAndMapToCallback("queue1", fun1)
    await messageQueue.AddQueueAndMapToCallback("queue2", fun2)

    await messageQueue.StartListeningToQueue()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await listener.close()

if __name__ == "__main__":
    asyncio.run(main())

