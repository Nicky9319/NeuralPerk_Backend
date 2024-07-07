import time
import threading
# import tensorflow as tf
import keras
import pickle
import requests
import json

import copy

class sessionSupervisor():
    def __init__(self , customerAgentPipe , userManagerPipe) -> None:
        self.userList = []
        self.customerAgentPipe = customerAgentPipe
        self.userManager = userManagerPipe
        self.model = None

        self.gradReadingEvent = None
        self.gradList_Lock = None
        
        self.gradList = []
        self.accuracyList = []
        self.lossList = []
        self.training_epoch_number = 0
        self.epochs = None
        self.socketio = None

        self.finalModelWeights = None

        self.highestAccuracy = 0.0
        self.currentAccuracy = 0.0

        self.lowestLoss = 100.0
        self.currentLoss = 100.0

        self.currentDateTime = None



    def parserUserRequest(self , message):
        userId = message["USER_ID"]
        mainMessage = message["MESSAGE"]
        messageType = mainMessage["TYPE"]   
        if(messageType == "MODEL_GRADS"):
            curTime = time.time()
            #print(len(mainMessage["DATA"]))
            sendTime = float(mainMessage["TIME"])
            print("Sending Time : " , sendTime)
            print("Receiving Time : " , curTime)
            print("Total Time Taken : " , curTime - sendTime)

            self.gradList_Lock.acquire()
            
            index = self.userList.index(userId)
            self.gradList[index] = mainMessage["DATA"]
            self.accuracyList[index] = mainMessage["ACCURACY"]
            self.lossList[index] = mainMessage["LOSS"]

            all_grads_received = True
            for val in self.gradList:
                if val == None:
                    all_grads_received = False
                    break
            if(all_grads_received):
                self.gradReadingEvent.set()
            self.gradList_Lock.release()
            print("Grads Updated for the particular Index !! : " , index)
        elif(messageType == "MESSAGE"):
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
        self.model.set_weights([ori - grad for ori , grad in zip(self.model.get_weights() , grads.get_weights())])
    

    def getAvgGrads(self):
        self.gradReadingEvent.wait()
        #print("All Grads Received !!")
        avgAccuracy = sum(self.accuracyList) / len(self.accuracyList)
        avgLoss = sum(self.lossList) / len(self.lossList)
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

        self.currentAccuracy = avgAccuracy
        self.currentLoss = avgLoss
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
        if "MODEL_WEIGHTS" in modelData.keys():
            print("Model Weights Have Been Successfully Received !!!")
            self.model.set_weights(modelData["MODEL_WEIGHTS"])

        print("Started the process of MODEL Training !!")
        modelDataUpdated = copy.deepcopy(modelData)
        modelDataUpdated["MODEL_WEIGHTS"] = None
        setupMessage = {"TYPE" : "MODEL_SETUP" , "DATA" : modelDataUpdated , "TOTAL_USERS" : len(self.userList) , "TIME" : time.time() , "CUSTOMER" : self.customerEmail , "EPOCHS" : self.epochs}
        self.broadcast(setupMessage)

        print(type(self.model.get_weights()))

        self.model.set_weights(modelData["MODEL_WEIGHTS"])
        # print(self.model.get_weights()[0][0][0][0])

        time.sleep(10)
        trainingMessage = {"TYPE" : "TRAIN" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
        self.broadcast(trainingMessage , inBytes=True)

        self.gradList = [None for users in self.userList]

        self.finalModelWeights = self.model.get_weights()

        for epoch_number in range(self.epochs - 1):
            epoch_start_time = time.time()
            finalGrads = self.getAvgGrads()

            if self.currentAccuracy > self.highestAccuracy:
                self.highestAccuracy = self.currentAccuracy
                self.finalModelWeights = self.model.get_weights()
                self.lowestLoss = self.currentLoss
                print("Highest Accuracy Updated !!!") 
                print("Lowest Loss Updated !!!")

            print("Aggregation of the Model Grads Completed !!")
            self.applyGrad(finalGrads)
            epoch_end_time = time.time()
            print(f"Total Time For Training Epoch Number {epoch_number + 1} : " , epoch_end_time - epoch_start_time)

            message = {"TYPE" : "UPDATED_MODEL" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
            print("Message has been Finalized !!")
            self.broadcast(message=message , inBytes=True)
            

        customerModelUpdateData = {"TYPE" : "ADD_NEW_MODEL" , "EMAIL" : self.customerEmail , "MODEL_WEIGHTS" : self.finalModelWeights , "MODEL_CONFIG" : self.model.to_json() , "MODEL_NAME" : self.currentDateTime}
        customerModelUpdateData = pickle.dumps(customerModelUpdateData)
        response = requests.put("http://127.0.0.1:5555/updateCustomerModel" , data = customerModelUpdateData , headers={"Content-Type" : "application/octet-stream"})
        
        print("Model Training Finished !!!")



    def runAndManageSession(self , data):
        self.gradReadingEvent = threading.Event()
        self.gradList_Lock = threading.Lock()


        print("Running and Managing Session !!!")

        self.customerEmail = data["EMAIL"]
        modelInfo = data["DATA"]

        self.currentDateTime = data["DATETIME"]
        print("Current Date Time : " , self.currentDateTime)

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

        







# class testSessionSupervisor():
#     def __init__(self , customerAgentPipe , userManagerPipe , data) -> None:
#         self.userList = []
#         self.customerAgentPipe = customerAgentPipe
#         self.userManager = userManagerPipe
#         self.model = None

#         self.gradReadingEvent = None
#         self.gradList_Lock = None
        
#         self.gradList = []
#         self.training_epoch_number = 0
#         self.epochs = None
#         self.socketio = None
        
#         self.gradReadingEvent = threading.Event()
#         self.gradList_Lock = threading.Lock()
        
#         self.customerEmail = data["EMAIL"]
#         self.userList = []




#     def parserUserRequest(self , message):
#         userId = message["USER_ID"]
#         mainMessage = message["MESSAGE"]
#         messageType = mainMessage["TYPE"]   
#         if(messageType == "MODEL_GRADS"):
#            # print(mainMessage["DATA"][0][0][0][0])
#             curTime = time.time()
#             print(len(mainMessage["DATA"]))
#             sendTime = float(mainMessage["TIME"])
#             print("Sending Time : " , sendTime)
#             print("Receiving Time : " , curTime)
#             print("Total Time Taken : " , curTime - sendTime)

#             self.gradList_Lock.acquire()
            
#             index = self.userList.index(userId)
#             self.gradList[index] = mainMessage["DATA"]
#             all_grads_received = True
#             for val in self.gradList:
#                 if val == None:
#                     all_grads_received = False
#                     break
#             if(all_grads_received):
#                 self.gradReadingEvent.set()
#             self.gradList_Lock.release()
#             print("Grads Updated for the particular Index !! : " , index)
#         elif(messageType == "MESSAGE"):
#             print("Received Message : " , mainMessage["DATA"])
#         pass

#     def listenToUserMessages(self):
#         print("Listening to User Manager Messages !!!")
#         while True:
#             if self.userManager.poll():
#                 message = self.userManager.recv()
#                 #print("User Said : " , message)
#                 print(message["USER_ID"])

#                 relevantResponse = self.parserUserRequest(message)
#                 if(relevantResponse == "EXIT"):
#                     break
#             time.sleep(1)

#     def preSetup(self , users , customerEmail):
#         pass



#     def applyGrad(self , grads):
#         self.model.set_weights([ori - grad for ori , grad in zip(self.model.get_weights() , grads.get_weights())])
    

#     def getAvgGrads(self):
#         self.gradReadingEvent.wait()
#         #print("All Grads Received !!")
#         avgModel = keras.models.model_from_json(self.model.to_json())
#         layerLength = len(avgModel.layers)
#         gradModel = keras.models.model_from_json(self.model.to_json())
#         gradModel.set_weights(self.gradList[0])
#         for ind in range(1 , len(self.gradList)):
#             print(ind)
#             gradModel.set_weights(self.aggregateGrads(gradModel.get_weights() , self.gradList[ind]))
#         avgModel.set_weights(self.meanGrads(gradModel.get_weights() , len(self.gradList)))
#         self.gradReadingEvent.clear()
#         self.gradList = [None for indices in range(len(self.userList))]
#         #print("After Finding Aggregated Gradients !! , GradList = " , gradList)
#         return avgModel


#     def aggregateGrads(self , w1 , w2):
#         length = len(w1)
#         updated_params = []
#         for ind in range(length):
#             updated_params.append((w1[ind] + w2[ind]))
#         return updated_params


#     def meanGrads(self , w , size):
#         length = len(w)
#         updated_params = []
#         for ind in range(length):
#             updated_params.append(w[ind] / size)
#         return updated_params
    
#     def broadcast(self , message , inBytes = False):
#         print("broadcasting the Message to All Relevant Users !!!")
#         print(self.userList)
#         for users in self.userList:
#             print("User Id to Which Message is being Broadcasted is : " , users)
#             userMsg = {"USER_ID" : users , "DATA" : message}
#             userManagerMsg = {"TYPE" : "SEND_MESSAGE_TO_USER" , "DATA" : userMsg}
#             self.userManager.send(userManagerMsg)
        


#     def handle_model_training(self , modelData):
#         print("Started the process of MODEL Training !!")
#         setupMessage = {"TYPE" : "MODEL_SETUP" , "DATA" : modelData , "TOTAL_USERS" : len(self.userList) , "TIME" : time.time() , "CUSTOMER" : self.customerEmail , "EPOCHS" : self.epochs}
#         self.broadcast(setupMessage)

#         print(type(self.model.get_weights()))
#         self.model.load_weights("C:/Users/paart/OneDrive/Documents/Paarth Workshop/Start-Up/Deep Logic/Network Prototyping/Server Client Methods/SocketIO Server/model.h5")
#         trainingMessage = {"TYPE" : "TRAIN" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
#         self.broadcast(trainingMessage , inBytes=True)

#         self.gradList = [None for users in self.userList]

#         for epoch_number in range(self.epochs - 1):
#             epoch_start_time = time.time()
#             finalGrads = self.getAvgGrads()
#            # print(finalGrads.get_weights()[0][0][0][0])
#             print("Aggregation of the Model Grads Completed !!")
#             self.applyGrad(finalGrads)
#            # print(self.model.get_weights()[0][0][0][0])
#             epoch_end_time = time.time()
#             print(f"Total Time For Training Epoch Number {epoch_number + 1} : " , epoch_end_time - epoch_start_time)
#             # st = f"Model_{epoch_number}"
#             # model.save_weights(st)
#             message = {"TYPE" : "UPDATED_MODEL" , "DATA" : self.model.get_weights() , "TIME" : time.time()}
#             print("Message has been Finalized !!")
#             self.broadcast(message=message , inBytes=True)
            
#         print("Model Training Finished !!!")



#     def runAndManageSession(self , data):
#         print("Running and Managing Session !!!")
#         modelInfo = data["DATA"]


#         userManagerThread = threading.Thread(target=self.listenToUserMessages)
#         userManagerThread.start()


#         while True:
#             if(len(self.userList) == 0):
#                 jsMsg = {"TYPE" : "NEW_SESSION" , "USERS" : 1}
#                 self.userManager.send(jsMsg)
#                 response = self.userManager.recv()
#                 print(response)
#                 self.userList = response["USERS"]
#                 if(response["NOTICE"] == "NOT_SUFFICIENT"):
#                     print("Not Sufficient Users Available !!!")
#                     time.sleep(30)
#                 elif(response["NOTICE"] == "SUFFICIENT"):
#                     print("Sufficient Users Available !!!")
#                     break
#             else:
#                 break

#         print("The List of Users to be used is Here !!!" , self.userList)
#         self.preSetup(self.userList , self.customerEmail)
#         print("Pre Setup for the Model Training Has been completed !!!")

#         # Main Training Functionalities


#         print(type(modelInfo["MODEL_JSON"]))
#         #self.model = keras.models.model_from_json(modelInfo["MODEL_JSON"])
#         self.model = keras.models.model_from_json(json.dumps(modelInfo["MODEL_JSON"]))
#         print(self.model.summary())
#         self.epochs = modelInfo["EPOCHS"]
        
#         self.handle_model_training(modelInfo)

#         response = requests.put("http://127.0.0.1:5500/updateSessionStatus" , json = {"EMAIL" : self.customerEmail , "STATUS" : "IDLE"})
#         if response.status_code == 200:
#             print("Session Status Updated Successfully !!")
#         else:
#             print("Session Status Updation Failed !!")

#         # End of Session Manager

#         userManagerThread.join()


# class startTheSupervisor():
#     def __init__(self , customerAgentPipe , userManagerPipe) -> None:
#         self.customerAgentPipe = customerAgentPipe
#         self.userManager = userManagerPipe
    
#     def runAndManageSession(self , data):
#         sessionSupervisorObject = testSessionSupervisor(self.customerAgentPipe , self.userManager , data)
#         modelInfo = data["DATA"]
#         self.customerEmail = data["EMAIL"]

#         userManagerThread = threading.Thread(target=sessionSupervisorObject.listenToUserMessages)
#         userManagerThread.start()

#         self.userList = []
#         while True:
#             if(len(self.userList) == 0):
#                 jsMsg = {"TYPE" : "NEW_SESSION" , "USERS" : 1}
#                 self.userManager.send(jsMsg)
#                 response = self.userManager.recv()
#                 print(response)
#                 self.userList = response["USERS"]
#                 if(response["NOTICE"] == "NOT_SUFFICIENT"):
#                     print("Not Sufficient Users Available !!!")
#                     time.sleep(30)
#                 elif(response["NOTICE"] == "SUFFICIENT"):
#                     print("Sufficient Users Available !!!")
#                     break
#             else:
#                 break
        
#         sessionSupervisorObject.userList = self.userList
        
#         print("The List of Users to be used is Here !!!" , self.userList)
#         sessionSupervisorObject.preSetup(self.userList , self.customerEmail)
#         print("Pre Setup for the Model Training Has been completed !!!")

#         print(type(modelInfo["MODEL_JSON"]))
#         #self.model = keras.models.model_from_json(modelInfo["MODEL_JSON"])
#         sessionSupervisorObject.model = keras.models.model_from_json(json.dumps(modelInfo["MODEL_JSON"]))
#         print(sessionSupervisorObject.model.summary())
#         sessionSupervisorObject.epochs = modelInfo["EPOCHS"]
        
#         sessionSupervisorObject.handle_model_training(modelInfo)

#         response = requests.put("http://127.0.0.1:5500/updateSessionStatus" , json = {"EMAIL" : self.customerEmail , "STATUS" : "IDLE"})
#         if response.status_code == 200:
#             print("Session Status Updated Successfully !!")
#         else:
#             print("Session Status Updation Failed !!")

#         # End of Session Manager

#         userManagerThread.join()


        

