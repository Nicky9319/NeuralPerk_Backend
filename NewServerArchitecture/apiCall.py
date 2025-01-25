import requests

response = requests.post('http://127.0.0.1:8001/CommunicationInterface/AddBufferMsg', json={"TYPE": "ADD_BUFFER_MSG", "DATA": {"BUFFER_UUID": "1234", "BUFFER_MSG": "Hello World"}})
print(response.json())