from flask import Flask, jsonify , request, Response
import json
import sqlite3
import os
import pickle
import tensorflow as tf
import keras
import subprocess

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

from MongoManagers import UserDBManager
mongo = UserDBManager()

app = Flask(__name__)




# Customer Routing Section !!! -----------------------------------------------------------------------------------------

@app.route('/updateCustomerData' , methods=['PUT'])
def update_customer_data_callback():
    if request.method == 'PUT':
        data = None
        if request.content_type == 'application/octet-stream':
            data = pickle.loads(request.get_data())
        elif request.content_type == 'application/json':
            data = request.get_json()
        
        if data["TYPE"] == "ADD_NEW_MODEL":
            print("Saving New Model to the Customer Data Directory !!!")
            customerDataPath = "CustomerData/" + data['EMAIL']  
            modelConfig = data['MODEL_CONFIG']
            model = keras.models.model_from_json(modelConfig)
            model.set_weights(data['MODEL_WEIGHTS'])
            model.save(customerDataPath + "/" + data["MODEL_NAME"] + ".h5")



        if os.path.exists(customerDataPath):
            # with open(customerDataPath + "/" + data['FILE_NAME'] , 'w') as file:
            #     file.write(data['FILE_DATA'])
            return jsonify({'message': 'Data Updated'}), 200
        else:
            return jsonify({'message': 'Customer Data Not Found'}), 404
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405

@app.route('/getCustomerData' , methods=['GET'])
def get_customer_data_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        msgType = data["TYPE"]
        if msgType == "GET_TRAINED_MODELS":
            trainedModelList = os.listdir("CustomerData/" + data['EMAIL'])
            modelNameList = [model.split(".")[0] for model in trainedModelList]
            return jsonify({'message': "trained Model List" , "DATA" : modelNameList}), 200
        elif msgType == "GET_MODEL":
            modelName = data['MODEL_NAME']
            modelPath = "CustomerData/" + data['EMAIL'] + "/" + modelName + ".h5"
            if os.path.exists(modelPath):
                model = tf.keras.models.load_model(modelPath)
                modelConfig = model.to_json()
                modelWeights = model.get_weights()
                print(len(pickle.dumps({'message': "Model Found" , "MODEL_CONFIG" : modelConfig , "MODEL_WEIGHTS" : modelWeights})))
                print(type(modelConfig))
                print(type(modelWeights))
                return Response(pickle.dumps({'message': "Model Found" , "MODEL_CONFIG" : modelConfig , "MODEL_WEIGHTS" : modelWeights})  , mimetype='application/octet-stream' , status=200) 
            else:
                return jsonify({'message': "Model Not Found"}), 404
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


# Customer Routing Section END !!! -------------------------------------------------------------------------------------






# Basic Endpoints Section !!! --------------------------------------------------------------------------------------------

@app.route('/credentials', methods=['GET' , 'POST' , 'PUT'])
def credentials_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        return credentials_get_request(data)
    elif request.method == 'POST':
        return credentials_post_request(request.get_json())
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def credentials_get_request(data):
    if(data['TYPE'] == "CUSTOMERS"):
        pass
        # credsVal = (data['EMAIL'], data['PASSWORD'])
        # cursor.execute("select email , password from customers")
        # queryResult = cursor.fetchall()
        # if credsVal in queryResult:
        #     return jsonify({'message': 'VERIFIED'}), 200
        # else:
        #     return jsonify({'message': 'Invalid Customer Credentials'}), 200
    elif(data['TYPE'] == "USERS"):
        email, password = data["EMAIL"], data["PASSWORD"]
        if mongo.credential_CheckCredentials(email, password):
            print("User Exists !!!")
            return jsonify({'message': 'Valid User Credentials'}), 200

        print("User Not Found !!!")
        return jsonify({'message': 'Invalid User Credentials'}), 404

    return jsonify({'message': 'Not a Valid Request'}), 400

def credentials_post_request(data):
    if(data['TYPE'] == "CUSTOMERS"):
        pass
        # email =  data['EMAIL']
        # password = data['PASSWORD']
        # if mongo.CheckUserExist(email):
        #     print("Customer Already Exists !!!")
        #     return jsonify({'message': 'Customer Already Exists'}), 409
        
        # mongo.CreateNewUser(email , password)

        # credsVal = (data['EMAIL'],)

        # cursor.execute("select email from customers")
        # queryResult = cursor.fetchall()
        
        # print(queryResult)
        # print(credsVal)
        # if credsVal in queryResult:
        #     print("Customer Already Exists !!!")
        #     return jsonify({'message': 'Customer Already Exists'}), 409
        
        # credsVal = (data['EMAIL'], data['PASSWORD'])
        # cursor.execute("insert into customers values (?, ?)", credsVal)
        # localConnection.commit()

        # customerDataPath = "CustomerData/" + data['EMAIL']
        # os.mkdir(customerDataPath)
        # return jsonify({'message': 'Customer Credentials Added'}), 200
    elif(data['TYPE'] == "USERS"):  
        email = data['EMAIL']
        password = data['PASSWORD']

        if mongo.CheckUserExist(email):
            print("Customer Already Exists !!!")
            return jsonify({'message': 'Customer Already Exists'}), 409
        
        mongo.CreateNewUser(email , password)
        return jsonify({'message': 'User Credentials Added'}), 200
    
    return jsonify({'message': 'Not a Valid Request'}), 400




@app.route('/check_node' , methods=['GET'])
def check_node_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        return check_node_get_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def check_node_get_request(data):
    if(data['TYPE'] == "CUSTOMERS"):
        pass
        # credsVal = (data['EMAIL'],)
        # cursor.execute("select email from customers")
        # queryResult = cursor.fetchall()
        # if credsVal in queryResult:
        #     return jsonify({'message': 'Registered'}), 200
        # else:
        #     return jsonify({'message': 'Unregistered'}), 200
    elif(data['TYPE'] == "USERS"):
        email = data['EMAIL']
        if mongo.CheckUserExist(email):
            print("User Exists !!!")
            return jsonify({'message': 'Registered'}), 200
        
        return jsonify({'message': 'Unregistered'}), 200
    
    return jsonify({'message': 'Not a Valid Request'}), 400




@app.route('/serverRunning' , methods=['GET'])
def server_running_callback():
    return jsonify({'message': 'Running'}), 200


@app.route('/sendOTP' , methods=['POST'])
def send_OTP_callback():
    if request.method == 'POST':
        data = request.get_json()
        return send_OTP_post_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def send_OTP_post_request(data):
    generatedOTP = random.randint(100000, 999999)

    sender_email = 'neuralperk@gmail.com'
    passkey = 'kibq tobi emip xsqm'
    receiver_email = data['EMAIL']
    subject = 'OTP Verification Neural Perk'
    message = f'Your OTP for Account verification is: {generatedOTP}'

    try:
        sendEmail(sender_email, passkey, receiver_email, subject, message)
        return jsonify({'message': 'OTP Sent', "OTP" : generatedOTP}), 200
    except:
        return jsonify({'message': 'Email Sending Failed'}), 500

def sendEmail(sender_email, passkey, receiver_email, subject, message):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Add body to the email
    msg.attach(MIMEText(message, 'plain'))

    # Create SMTP session
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, passkey)
        server.send_message(msg)
    

# Basic Endpoints Section END !!! ----------------------------------------------------------------------------------------







# User Routing Section !!! -----------------------------------------------------------------------------------------


@app.route('/UserEarnings' , methods=['GET','PUT'])
def user_earnings_callback():
    if request.method == "GET":
        message = request.args.get('message')
        data = json.loads(message)
        return user_earnings_get_requests(data)
    elif request.method == "PUT":
        data = request.get_json()
        return user_earnings_put_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def user_earnings_put_request(data):
    email = data['EMAIL']
    manualStopping = data['MANUAL_STOPPING']
    elapsedTimeSeconds = data['ELAPSED_TIME'] / 1000
    gpuType = data['GPU_TYPE']
    uuid = data['UUID']

    earningsPerMinute = getEarningPerMinuteGPUTime(gpuType)
    earnings = alterEarningsAccordingToTime(earningsPerMinute , elapsedTimeSeconds , manualStopping)
    
    checkAndUpdateUUIDGpu(email, uuid , gpuType)
    return updateEarningOfUser(email , earnings, uuid)

def checkAndUpdateUUIDGpu(email, UUID , gpuType):
    if mongo.CheckUserExist(email):
        print("Checking and Inserting GPU !!!")
        mongo.UEM_UuidGPU_CheckAndInsert(UUID , gpuType)
    else:
        return None

def getEarningPerMinuteGPUTime(gpuType):
    return 0.25

def alterEarningsAccordingToTime(earningsPerMinute , elapsedTimeSeconds , manualStopping):
    if(manualStopping and elapsedTimeSeconds < 3600):
        print("Stopped the Script Too Early !!!")
        return 0
    elif(not manualStopping and elapsedTimeSeconds < 120):
        print("Script Ran for Less than 2 Mins, So Auto Closing Doesnt Count !!!")
        return 0    
    
    return earningsPerMinute * (elapsedTimeSeconds / 60)

def updateEarningOfUser(userEmail ,  earningAmount, UUID = None):
    if mongo.CheckUserExist(userEmail) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    print(earningAmount)
    mongo.credential_IncrementUserTotalEarningsAndBalance(userEmail , earningAmount)
    # Update the UUID with the GPU
    return jsonify({'message': 'Earnings Updated'}), 200


def user_earnings_get_requests(data):
    print(data)
    email = data["EMAIL"]
    if mongo.CheckUserExist(email) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    return jsonify({'message': 'User Found' , 'DATA' : mongo.GetUserFinancials(email)}), 200




@app.route('/UserInfo', methods=['GET'])
def user_info_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        return user_info_get_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def user_info_get_request(data):
    email = data["EMAIL"]
    if mongo.CheckUserExist(email) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    return jsonify({'message': 'User Found' , 'DATA' : userInfoRetrivalAndFormating(email) }), 200

def userInfoRetrivalAndFormating(email):
    userFinancials = mongo.GetUserFinancials(email)
    totalEarnings = userFinancials['TOTAL_EARNINGS']
    balance = userFinancials['BALANCE']

    totalEarningTime = mongo.credential_TotalTimeSpent(email)
    return {"TOTAL_EARNINGS" : totalEarnings, "BALANCE" : balance, "TOTAL_EARNING_TIME" : totalEarningTime}




@app.route('/UserAppSession', methods=['POST'])
def app_session_callback():
    if request.method == 'POST':
        data = request.get_json()
        return app_session_post_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405
    

def app_session_post_request(data):
    email = data['EMAIL']
    if mongo.CheckUserExist(email) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    UUID = data['UUID']
    StartTime = data['START_TIME']
    EndTime = data['END_TIME']

    mongo.UEM_UuidEmail_CheckAndInsert(UUID , email)

    mongo.activity_InsertAppSession(email , UUID , StartTime , EndTime)
    return jsonify({'message': 'App Session Added'}), 200




@app.route('/UserContainerSession', methods=['POST'])
def container_session_callback():
    if request.method == 'POST':
        data = request.get_json()
        return container_session_post_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405
    

def container_session_post_request(data):
    email = data['EMAIL']
    if mongo.CheckUserExist(email) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    UUID = data['UUID']
    StartTime = data['START_TIME']
    EndTime = data['END_TIME']

    mongo.UEM_UuidEmail_CheckAndInsert(UUID , email)

    mongo.activity_InsertContainerSession(email , UUID , StartTime , EndTime)
    return jsonify({'message': 'Container Session Added'}), 200




@app.route('/UserUUID' , methods=['POST'])
def user_uuid_callback():
    if request.method == 'POST':
        data = request.get_json()
        return user_uuid_post_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405
    

def user_uuid_post_request(data):
    UUID = data["UUID"]
    if mongo.UEM_CheckUuidExist(UUID):
        return jsonify({'message': 'UUID Exists'}), 200
    
    mongo.UEM_InsertNewUUID(UUID)
    return jsonify({'message': 'UUID Added'}), 200




@app.route('/UserWithdraw' , methods=["PUT"])
def user_withdraw_callback():
    if request.method == 'PUT':
        data = request.get_json()
        return user_withdraw_put_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def user_withdraw_put_request(data):
    email = data['EMAIL']
    upiID = data['UPI_ID']
    amount = data['AMOUNT']
    addNote = data['ADDITIONAL_NOTE']


    if mongo.CheckUserExist(email) == False:
        return jsonify({'message': 'User Not Found'}), 404
    
    if mongo.WithdrawAmount(upiID , amount , email, addNote) == False:
        return jsonify({'message': 'Insufficient Balance'}), 400

    return jsonify({'message': 'Withdrawal Process Initiated Successfully'}), 200

# User Routing Section END !!! --------------------------------------------------------------------------------------






if __name__ == '__main__':
    ipAddress = "0.0.0.0"
    app.run(host=ipAddress, port=5555 , debug=True)
 