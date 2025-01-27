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
    # exchange_name = "SESSION_SUPERVISOR_EXCHANGE"
    # exchange_name = "COMMUNICATION_INTERFACE_EXCHANGE"


    routing_key = "UME_SUPERVISOR"
    # routing_key = f"SSE_{'d3b11affc7654de083d7b6d109f2a590'}_CA"
    # routing_key = "CIE_USER_MANAGER"
    print(routing_key)

    
    mainMessage = {"USER_ID":"erkHhKdbfxmzhHfBAAAD","MESSAGE_FOR_USER":"Nothing"}
    message = {"TYPE": "SEND_MESSAGE_TO_USER", "DATA": mainMessage}

    headers = {"SESSION_SUPERVISOR_ID" : "nothing"}

    await publishData(exchange_name, routing_key, json.dumps(message), headers=headers)

if __name__ == "__main__":
    asyncio.run(main())