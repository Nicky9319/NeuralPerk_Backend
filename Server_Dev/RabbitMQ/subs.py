import pika

# Connection parameters with a specific port (5672 is the default port for RabbitMQ)
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 12000, '/', credentials)

# Establish a connection to RabbitMQ server
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare the queue from which we'll consume messages
channel.queue_declare(queue='my_queue')

# Define a callback function for receiving messages
def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    print(f" [x] Received headers: {properties.headers}")

# Set up consuming from the queue
channel.basic_consume(queue='my_queue',
                      on_message_callback=callback,
                      auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')

# Start consuming (this blocks the thread)
channel.start_consuming()

print("Consming !!!")


