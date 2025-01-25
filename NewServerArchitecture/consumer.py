import pika

def start_consuming(exchange_name, queue_name):
    # Establish a connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')

    # Declare the queue
    queueRef = channel.queue_declare(queue=queue_name , auto_delete=True)

    # Bind the queue to the exchange
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=queue_name)


    # Define a callback function to handle messages
    def callback(ch, method, properties, body):
        print(f"Received message: {body}")

    # Start consuming messages
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(f"Waiting for messages in {queue_name}. To exit press CTRL+C")
    channel.start_consuming()

# Example usage
# start_consuming('my_exchange', 'my_queue')


exchange_name = "SESSION_SUPERVISOR_EXCHANGE"
id = "b3ccdeffa8e64d7dabe05bab1fff1bc1"
queue_name = f"SSE_{id}_CA"

start_consuming(exchange_name, queue_name)
