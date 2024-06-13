from websocket import create_connection

ws = create_connection("ws://localhost:5000")
print("Sending 'Hello, Server'...")
ws.send("Hello, Server")
print("Sent")
print("Receiving...")
result = ws.recv()
print("Received '%s'" % result)
ws.close()