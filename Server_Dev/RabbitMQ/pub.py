import pika

# Connection parameters with a specific port (5672 is the default port for RabbitMQ)
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 12000, '/', credentials)

# Establish a connection to RabbitMQ server
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare a queue to which we'll publish messages
channel.queue_declare(queue='my_queue')

# Publish a message
message = "Hello, RabbitMQ!"
channel.basic_publish(exchange='',
                      routing_key='my_queue',
                      body=message,
                      properties=pika.BasicProperties(
                          headers={'key1': 'value1', 'key2': 'value2'}
                      ))

print(f" [x] Sent '{message}'")

# Close the connection
connection.close()
