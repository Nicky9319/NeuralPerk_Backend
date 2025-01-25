import asyncio
import aio_pika

async def publish_message():
    # Establish a connection to RabbitMQ
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost/",  # Replace with your RabbitMQ URL
        loop=asyncio.get_event_loop()
    )
    
    try:
        # Creating a channel
        channel = await connection.channel()
        
        # Declaring a queue
        queue_name = "test_queue"
        queue = await channel.declare_queue(queue_name, auto_delete=True)
        
        # Publishing a message
        message_body = "Hello World!"
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key=queue_name
        )

        message_body = "Hello World!"
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key="test"
        )

        print(f" [x] Sent '{message_body}' to {queue_name}")
        
    finally:
        await connection.close()

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(publish_message())
