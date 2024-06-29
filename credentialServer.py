from flask import Flask, jsonify , request
import json
import sqlite3

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
        cursor.execute("select * from customers")
        queryResult = cursor.fetchall()
        if credsVal in queryResult:
            return jsonify({'message': 'Valid Customer Credentials'}), 200
        else:
            return jsonify({'message': 'Invalid Customer Credentials'}), 404
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

if __name__ == '__main__':
    ipAddress = '127.0.0.1'
    app.run(host=ipAddress, port=5555 , debug=False)
 


