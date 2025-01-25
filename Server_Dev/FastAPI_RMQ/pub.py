import asyncio
import aio_pika

import json

async def publish_message():
    # Establish a connection to RabbitMQ
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost/",  # Replace with your RabbitMQ URL
        loop=asyncio.get_event_loop()
    )
    
    try:
        # Creating a channel
        channel = await connection.channel()

        q1_name = "queue1"
        q2_name = "queue2"

        q1 = await channel.declare_queue(q1_name, durable=True)
        q2 = await channel.declare_queue(q2_name, durable=True)
        
        message_body = {"KEY" : "VALUE"}


        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message_body).encode()),
            routing_key=q1_name
        )

        message_body = "Hello World!"
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key=q2_name
        )
        
    finally:
        await connection.close()

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(publish_message())
