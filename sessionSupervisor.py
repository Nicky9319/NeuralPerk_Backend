import time
import threading
# import tensorflow as tf
import keras
import pickle
import requests
import json


class sessionSupervisor():
    def __init__(self , customerAgentPipe , userManagerPipe) -> None:
        self.userList = []
        self.customerAgentPipe = customerAgentPipe
        self.userManager = userManagerPipe
        self.model = None

        self.gradReadingEvent = None
        self.gradList_Lock = None
        
        self.gradList = []
        self.training_epoch_number = 0
        self.epochs = None
        self.socketio = None
        print("Pipes for Supervisor")
        print()



    def parserUserRequest(self , message):
        userId = message["USER_ID"]
        mainMessage = message["MESSAGE"]
        messageType = mainMessage["TYPE"]   
        if(messageType == "MODEL_GRADS"):
            curTime = time.time()
            print(len(mainMessage["DATA"]))
            sendTime = float(mainMessage["TIME"])
            print("Sending Time : " , sendTime)
            print("Receiving Time : " , curTime)
            print("Total Time Taken : " , curTime - sendTime)

            self.gradList_Lock.acquire()
            
            index = self.userList.index(userId)
            self.gradList[index] = mainMessage["DATA"]
            all_grads_received = True
            for val in self.gradList:
                if val == None:
                    all_grads_received = False
                    break
            if(all_grads_received):
                self.gradReadingEvent.set()
            self.gradList_Lock.release()
            print("Grads Updated for the particular Index !! : " , index)
        if(messageType == "MESSAGE"):
            print("Received Message : " , mainMessage["DATA"])
        pass

    def listenToUserMessages(self):
        print("Listening to User Manager Messages !!!")
        while True:
            if self.userManager.poll():
                message = self.userManager.recv()
                #print("User Said : " , message)
                print(message["USER_ID"])

                relevantResponse = self.parserUserRequest(message)
                if(relevantResponse == "EXIT"):
                    break
            time.sleep(1)

    def preSetup(self , users , customerEmail):
        pass



    def applyGrad(self , grads):
        length = len(grads.get_weights())
        oriWeights = self.model.get_weights()
        gradWeights = grads.get_weights()
        updated_params = []
        for ind in range(length):
            updated_params.append(oriWeights[ind] - gradWeights[ind])
        self.model.set_weights(updated_params)

        print("Parameters of the Original Model has been Updated !!")
        return self.model
    

    def getAvgGrads(self):
        self.gradReadingEvent.wait()
        #print("All Grads Received !!")
        avgModel = keras.models.model_from_json(self.model.to_json())
        layerLength = len(avgModel.layers)
        gradModel = keras.models.model_from_json(self.model.to_json())
        gradModel.set_weights(self.gradList[0])
        for ind in range(1 , len(self.gradList)):
            print(ind)
            gradModel.set_weights(self.aggregateGrads(gradModel.get_weights() , self.gradList[ind]))
        avgModel.set_weights(self.meanGrads(gradModel.get_weights() , len(self.gradList)))
        self.gradReadingEvent.clear()
        self.gradList = [None for indices in range(len(self.userList))]
        #print("After Finding Aggregated Gradients !! , GradList = " , gradList)
        return avgModel

    
    def aggregateGrads(self , w1 , w2):
        length = len(w1)
        updated_params = []
        for ind in range(length):
            updated_params.append((w1[ind] + w2[ind]))
        return updated_params


    def meanGrads(self , w , size):
        length = len(w)
        updated_params = []
        for ind in range(length):
            updated_params.append(w[ind] / size)
        return updated_params
    
    def broadcast(self , message , inBytes = False):
        print("broadcasting the Message to All Relevant Users !!!")
        print(self.userList)
        for users in self.userList:
            print("User Id to Which Message is being Broadcasted is : " , users)
            userMsg = {"USER_ID" : users , "DATA" : message}
            userManagerMsg = {"TYPE" : "SEND_MESSAGE_TO_USER" , "DATA" : userMsg}
            self.userManager.send(userManagerMsg)
        


    def handle_model_training(self , modelData):
        print("Started the process of MODEL Training !!")
        setupMessage = {"TYPE" : "MODEL_SETUP" , "DATA" : modelData , "TOTAL_USERS" : len(self.userList) , "TIME" : time.time() , "CUSTOMER" : self.customerEmail , "EPOCHS" : self.epochs}
        self.broadcast(setupMessage)

        print(type(self.model.get_weights()))
        trainingMessage = {"TYPE" : "TRAIN" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
        self.broadcast(trainingMessage , inBytes=True)

        self.gradList = [None for users in self.userList]

        for epoch_number in range(self.epochs - 1):
            epoch_start_time = time.time()
            finalGrads = self.getAvgGrads()
            print("Aggregation of the Model Grads Completed !!")
            self.applyGrad(finalGrads)
            epoch_end_time = time.time()
            print(f"Total Time For Training Epoch Number {epoch_number + 1} : " , epoch_end_time - epoch_start_time)
            # st = f"Model_{epoch_number}"
            # model.save_weights(st)
            message = {"TYPE" : "UPDATED_MODEL" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
            print("Message has been Finalized !!")
            self.broadcast(message=message , inBytes=True) 
            
        print("Model Training Finished !!!")



    def runAndManageSession(self , data):
        self.gradReadingEvent = threading.Event()
        self.gradList_Lock = threading.Lock()

        print("Running and Managing Session !!!")
        self.customerEmail = data["EMAIL"]

        modelInfo = data["DATA"]

        print(self.socketio)

        userManagerThread = threading.Thread(target=self.listenToUserMessages)
        userManagerThread.start()

        self.userList = []

        while True:
            if(len(self.userList) == 0):
                jsMsg = {"TYPE" : "NEW_SESSION" , "USERS" : 1}
                self.userManager.send(jsMsg)
                response = self.userManager.recv()
                print(response)
                self.userList = response["USERS"]
                if(response["NOTICE"] == "NOT_SUFFICIENT"):
                    print("Not Sufficient Users Available !!!")
                    time.sleep(30)
                elif(response["NOTICE"] == "SUFFICIENT"):
                    print("Sufficient Users Available !!!")
                    break
            else:
                break

        print("The List of Users to be used is Here !!!" , self.userList)
        self.preSetup(self.userList , self.customerEmail)
        print("Pre Setup for the Model Training Has been completed !!!")

        # Main Training Functionalities


        print(type(modelInfo["MODEL_JSON"]))
        #self.model = keras.models.model_from_json(modelInfo["MODEL_JSON"])
        self.model = keras.models.model_from_json(json.dumps(modelInfo["MODEL_JSON"]))
        print(self.model.summary())
        self.epochs = modelInfo["EPOCHS"]
        
        self.handle_model_training(modelInfo)

        response = requests.put("http://127.0.0.1:5500/updateSessionStatus" , json = {"EMAIL" : self.customerEmail , "STATUS" : "IDLE"})
        if response.status_code == 200:
            print("Session Status Updated Successfully !!")
        else:
            print("Session Status Updation Failed !!")

        # End of Session Manager

        userManagerThread.join()
        

