import requests
import json

ipAddress = "128.199.31.223"

jsonMsg = {"EMAIL" : "paarthsaxena2005@gmail.com", "MANUAL_STOPPING" : False, "ELAPSED_TIME" : 36000000, "GPU_TYPE": "GTX 1080"}
response = requests.put(f"http://{ipAddress}:5555/UserEarnings", json=jsonMsg)




jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com"}
response = requests.get(f"http://{ipAddress}:5555/UserEarnings?message={json.dumps(jsMsg)}")
print(response.json())




jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com"}
response = requests.get(f"http://{ipAddress}:5555/UserInfo?message={json.dumps(jsMsg)}")
print(response.json())



jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "UUID":"46091650568035" , "START_TIME" : "29/10/2024:06/35/37" , "END_TIME" : "3/11/2024:18/10/56"}
response = requests.post(f"http://{ipAddress}:5555/UserAppSession" , json = jsMsg)
print(response.json())



jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com" , "UUID":"5161160406605016553" , "START_TIME" : "29/10/2024:06/35/37" , "END_TIME" : "3/11/2024:18/10/56"}
response = requests.post(f"http://{ipAddress}:5555/UserContainerSession" , json = jsMsg)
print(response.json())



jsMsg = {"UUID" : "46091650568035"}
response = requests.post(f"http://{ipAddress}:5555/UserUUID" , json = jsMsg)
print(response.json())


jsMsg = {"EMAIL" : "paarthsaxena2005@gmail.com", "UPI_ID" : "paarthsaxena2005@okaxis", "AMOUNT" : 100}
response =  requests.put(f"http://{ipAddress}:5555/UserWithdraw" , json = jsMsg)
print(response.json())