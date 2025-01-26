import aio_pika
import asyncio
import json

async def publishData(exchange_name, routing_key, message, headers=None):
    # Establish a connection to RabbitMQ server
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()

        # Declare an exchange
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)

        # Set the headers
        message_headers = headers if headers else {}
        properties = aio_pika.Message(
            body=message.encode(),
            headers=message_headers
        )

        # Publish the message
        await exchange.publish(
            properties,
            routing_key=routing_key
        )
        print(f" [x] Sent '{message}' to exchange '{exchange_name}' with routing key '{routing_key}' and headers '{message_headers}'")

# Example usage
async def main():
    exchange_name = "USER_MANAGER_EXCHANGE"
    routing_key = "UME_SUPERVISOR"
    message = {"TYPE": "MESSAGE_TEST", "DATA": "NONE"}
    headers = {"header_key": "VALUE"}

    await publishData(exchange_name, routing_key, json.dumps(message), headers)

if __name__ == "__main__":
    asyncio.run(main())