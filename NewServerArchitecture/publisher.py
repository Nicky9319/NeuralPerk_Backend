import pika
import json

def publishData(exchange_name, routing_key, message):
    # Establish a connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare an exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')

    # Publish the message
    channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
    print(f" [x] Sent '{message}' to exchange '{exchange_name}' with routing key '{routing_key}'")

    # Close the connection
    connection.close()

exchange_name = "USER_MANAGER_EXCHANGE"
routing_key = "UME_SUPERVISOR"
message = {"TYPE" : "MESSAGE_TEST" , "DATA" : "NONE"}

publishData(exchange_name, routing_key, json.dumps(message))