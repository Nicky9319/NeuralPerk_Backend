import requests
import json

jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "PASSWORD" : "test" , "DATA" : {"JOB_PROFILE" : "RENDERING" , "DATA" : "BLENDER_BINARY_FILE"} , "TYPE" : "CUSTOMERS"}
jsMsgDumps = json.dumps(jsMsg)
statusMsg = { "TYPE" : "CUSTOMERS" , "EMAIL" : "paarthsaxena2005@gmail.com"}
statusMsg = json.dumps(statusMsg)


# jsMsg = {"DATA" : "RENDERING DATA !!!"}

ipAddress = "127.0.0.1"

response = requests.get(f"http://{ipAddress}:5500/serverRunning")
print(response.text)


response = requests.post(f"http://{ipAddress}:5500/requestSessionCreation" , json = jsMsg)
print(response.text)

response = requests.get(f"http://{ipAddress}:5500/sessionSTATUS?message={statusMsg}")
print(response.text)

response = requests.post(f"http://{ipAddress}:5500/initializeSession" , json = {"EMAIL" : "paarthsaxena2005@gmail.com"})
print(response.text)

# response = requests.put(f"http://127.0.0.1:6666/handleSessionRequests" , json = {"EMAIL" : "paarthsaxena2005@gmail.com" , "DGSVBH#D" : "f,jwhrbfrwkjrw"})
# print(response.text)

