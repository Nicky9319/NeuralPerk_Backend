import requests
import json

jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "PASSWORD" : "test" , "TYPE" : "CUSTOMERS" , "DATA" : "NOTHING FOR NOW"}
jsMsg = json.dumps(jsMsg)
statusMsg = { "TYPE" : "CUSTOMERS" , "EMAIL" : "paarthsaxena2005@gmail.com"}
statusMsg = json.dumps(statusMsg)


response = requests.get(f"http://127.0.0.1:5500/requestSessionCreation?message={jsMsg}")
print(response.text)

response = requests.get(f"http://127.0.0.1:5500/sessionSTATUS?message={statusMsg}")
print(response.text)

response = requests.post(f"http://127.0.0.1:5500/initializeSession" , json = {"EMAIL" : "paarthsaxena2005@gmail.com"})
print(response.text)

# response = requests.put(f"http://127.0.0.1:6666/handleSessionRequests" , json = {"EMAIL" : "paarthsaxena2005@gmail.com" , "DGSVBH#D" : "f,jwhrbfrwkjrw"})
# print(response.text)

