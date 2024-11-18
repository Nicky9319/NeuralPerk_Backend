import requests
import json

import pickle


blendBinary = ""

with open('./test/test.blend' , 'rb') as file:
    blendBinary = file.read()

jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "PASSWORD" : "test" , "DATA" : {"JOB_PROFILE" : "RENDERING" , "DATA" : blendBinary} , "TYPE" : "CUSTOMERS"}
jsMsgDumps = pickle.dumps(jsMsg) 

statusMsg = { "TYPE" : "CUSTOMERS" , "EMAIL" : "paarthsaxena2005@gmail.com"}
statusMsg = json.dumps(statusMsg)

# ipAddress = '127.0.0.1'
ipAddress = '128.199.31.223'


response = requests.get(f"http://{ipAddress}:5500/serverRunning")
print(response.text)


response = requests.post(f"http://{ipAddress}:5500/requestSessionCreation" , data = jsMsgDumps , headers={'Content-Type': 'application/bytes'})
print(response.text)
print(response.status_code)

response = requests.get(f"http://{ipAddress}:5500/sessionSTATUS?message={statusMsg}")
print(response.text)

response = requests.post(f"http://{ipAddress}:5500/initializeSession" , json = {"EMAIL" : "paarthsaxena2005@gmail.com"})
print(response.text)


print("Wow")

