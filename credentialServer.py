from flask import Flask, jsonify , request, Response
import json
import sqlite3
import os
import pickle
import tensorflow as tf
import keras
import subprocess

app = Flask(__name__)

def handle_post_request(data):
    localConnection = sqlite3.connect('LoginCredentials.db')
    cursor = localConnection.cursor()
    if(data['TYPE'] == "CUSTOMERS"):
        credsVal = (data['EMAIL'],)
        cursor.execute("select email from customers")
        queryResult = cursor.fetchall()
        print(queryResult)
        print(credsVal)
        if credsVal in queryResult:
            print("Customer Already Exists !!!")
            return jsonify({'message': 'Customer Already Exists'}), 409
        credsVal = (data['EMAIL'], data['PASSWORD'])
        cursor.execute("insert into customers values (?, ?)", credsVal)
        localConnection.commit()
        customerDataPath = "CustomerData/" + data['EMAIL']
        os.mkdir(customerDataPath)
        return jsonify({'message': 'Customer Credentials Added'}), 200
    elif(data['TYPE'] == "USERS"):  
        credsVal = (data['EMAIL'],)
        cursor.execute("select email from users")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            return jsonify({'message': 'User Already Exists'}), 409
        credsVal = (data['EMAIL'], data['PASSWORD'] , 0 , 0 , 0)
        cursor.execute("insert into users values (? ,? ,? ,? ,?)", credsVal)
        localConnection.commit()
        return jsonify({'message': 'User Credentials Added'}), 200
    return jsonify({'message': 'Not a Valid Request'}), 400

def handle_get_request(data):
    localConnection = sqlite3.connect('LoginCredentials.db')
    cursor = localConnection.cursor()
    if(data['TYPE'] == "CUSTOMERS"):
        credsVal = (data['EMAIL'], data['PASSWORD'])
        cursor.execute("select email , password from customers")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            return jsonify({'message': 'VERIFIED'}), 200
        else:
            return jsonify({'message': 'Invalid Customer Credentials'}), 200
    elif(data['TYPE'] == "USERS"):
        print("Querying the User Table !!!")
        credsVal = (data['EMAIL'], data['PASSWORD'])
        cursor.execute("select email , password from users")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            print("Result Found !!!")
            return jsonify({'message': 'Valid User Credentials'}), 200
        else:
            print("Result Not Found !!!")
            return jsonify({'message': 'Invalid User Credentials'}), 404
    return jsonify({'message': 'Not a Valid Request'}), 400


@app.route('/credentials', methods=['GET' , 'POST' , 'PUT'  , 'DELETE'])
def credentials_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        return handle_get_request(data)
    elif request.method == 'POST':
        return handle_post_request(request.get_json())
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


def handle_check_node_request(data):
    localConnection = sqlite3.connect('LoginCredentials.db')
    cursor = localConnection.cursor()
    if(data['TYPE'] == "CUSTOMERS"):
        credsVal = (data['EMAIL'],)
        cursor.execute("select email from customers")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            return jsonify({'message': 'Registered'}), 200
        else:
            return jsonify({'message': 'Unregistered'}), 200
    elif(data['TYPE'] == "USERS"):
        credsVal = (data['EMAIL'],)
        cursor.execute("select email from users")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            return jsonify({'message': 'Registered'}), 200
        else:
            return jsonify({'message': 'Unregistered'}), 200
    return jsonify({'message': 'Not a Valid Request'}), 400

@app.route('/check_node' , methods=['GET'])
def check_node_callback():
    if request.method == 'GET':
        message = request.args.get('message')
        data = json.loads(message)
        return handle_check_node_request(data)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405

@app.route('/serverRunning' , methods=['GET'])
def server_running_callback():
    return jsonify({'message': 'Running'}), 200



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


def getEarningPerMinuteGPUTime(gpuType):
    return 0.25

def alterEarningsAccordingToTime(earningsPerMinute , elapsedTimeSeconds , manualStopping):
    if(manualStopping and elapsedTimeSeconds < 3600):
        print("Stopped the Script Too Early !!!")
        return 0
    
    return earningsPerMinute * (elapsedTimeSeconds / 3600)

def updateEarningOfUser(userEmail ,  earningAmount):
    localconnection = sqlite3.connect('LoginCredentials.db')
    cursor = localconnection.cursor()
    cursor.execute("select email from users")
    queryResult = cursor.fetchall()
    print(queryResult)
    if (userEmail,) not in queryResult:
        return jsonify({'message': 'User Not Found'}), 404

    cursor.execute("update users set earned = earned + ? where email = ?" , (earningAmount , userEmail))
    cursor.execute("update users set balance = earned - payout where email = ?" , (userEmail,))
    localconnection.commit()

    return jsonify({'message': 'Earnings Updated'}), 200

@app.route('/updateCustomerEarnings' , methods=['PUT'])
def update_customer_earnings():
    print("Request to Update Earning Given !!!")
    if request.method == "PUT":
        data = request.get_json()
        print(data)
        email = data['EMAIL']
        manualStopping = data['MANUAL_STOPPING']
        elapsedTimeSeconds = data['ELAPSED_TIME'] / 1000
        gpuType = data['GPU_TYPE']

        earningsPerMinute = getEarningPerMinuteGPUTime(gpuType)
        earnings = alterEarningsAccordingToTime(earningsPerMinute , elapsedTimeSeconds , manualStopping)
        
        return updateEarningOfUser(email , earnings)
    else:
        print("Method not allowed !!!")
        return jsonify({'message': 'Method not allowed'}), 405


if __name__ == '__main__':
    # ipAddressAndPort = '0.0.0.0:5555'
    # print(tf.__version__)
    # command = [
    #     'gunicorn',
    #     '--bind', ipAddressAndPort,
    #     '--workers', str(2),
    #     'credentialServer:app',  # Replace 'app' with your Flask application module name
    # ]
    # subprocess.run(command)
    ipAddress = "0.0.0.0"
    app.run(host=ipAddress, port=5555 , debug=False)
 