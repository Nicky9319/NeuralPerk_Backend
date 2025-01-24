import requests
import json

import pickle

import io
import tqdm


blendBinary = ""

with open('./test/test.blend' , 'rb') as file:
    blendBinary = file.read()


# with open('./test/test_scene.blend' , 'rb') as file:
#     blendBinary = file.read()

jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "PASSWORD" : "test" , "DATA" : {"JOB_PROFILE" : "RENDERING" , "DATA" : blendBinary} , "TYPE" : "CUSTOMERS"}
jsMsgDumps = pickle.dumps(jsMsg) 

statusMsg = { "TYPE" : "CUSTOMERS" , "EMAIL" : "paarthsaxena2005@gmail.com"}
statusMsg = json.dumps(statusMsg)

ipAddress = '127.0.0.1'
# ipAddress = '128.199.31.223'
# ipAddress = "209.38.123.24"


response = requests.get(f"http://{ipAddress}:5500/serverRunning")
print(response.text)



# Sending the Blender File to the Server

progressBar = tqdm.tqdm(total = len(jsMsgDumps) , unit = 'B' , unit_scale = True, desc='Uploading' , ncols=100)

def readSendDataInChunks(file_object, chunk_size = 1024 * 1024):
    while chunk := file_object.read(chunk_size):
        yield chunk
        progressBar.update(len(chunk))

response = requests.post(f"http://{ipAddress}:5500/requestSessionCreation" , data = readSendDataInChunks(io.BytesIO(jsMsgDumps)) , headers={'Content-Type': 'application/bytes'})
print(response.text)
print(response.status_code)

progressBar.close()






response = requests.get(f"http://{ipAddress}:5500/sessionSTATUS?message={statusMsg}")
print(response.text)

response = requests.post(f"http://{ipAddress}:5500/initializeSession" , json = {"EMAIL" : "paarthsaxena2005@gmail.com"})
print(response.text)


print("Wow")

