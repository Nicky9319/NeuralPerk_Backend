import time
import threading
# import tensorflow as tf
import keras
import pickle
import requests
import json
import subprocess
import os
import datetime

import copy


import message_handler
from message_handler import Message , MessageTypes

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



# Basic Utility Section !!! ---------------------------------------------------------------------------------------------------

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

    def parserUserManagerRequest(self , message):
            # print("Parsing User Manager Request !!!")
            msgType = message["TYPE"]
            if(msgType == "DISCONNECT"):
                print("User Disconnected !!! , Message By Session Supervisor")
                self.handleUserDisconnect(message["USER_ID"])
            else:
                pass

    def listenToUserMessages(self):
        print("Listening to User Manager Messages !!!")
        while True:
            if self.userManager.poll():
                message = self.userManager.recv()
                #print("User Said : " , message)
                # print(message["USER_ID"])

                # print(message)

                msgType = message["TYPE"]
                if(msgType == "USER_MESSAGE"):
                    relevantResponse = self.parserUserRequest(message["DATA"])
                elif(msgType == "USER_MANAGER_MESSAGE"):
                    # print("User Manager Message Received !!!")
                    relevantResponse = self.parserUserManagerRequest(message["DATA"])
                else:
                    pass

            time.sleep(1)
  
    def broadcast(self , message , inBytes = False):
        print("broadcasting the Message to All Relevant Users !!!")
        print(self.userList)
        for users in self.userList:
            print("User Id to Which Message is being Broadcasted is : " , users)
            userMsg = {"USER_ID" : users , "DATA" : message}
            userManagerMsg = {"TYPE" : "SEND_MESSAGE_TO_USER" , "DATA" : userMsg}
            self.userManager.send(userManagerMsg)
        
    def sendMessageToUser(self , userId , message):
        userMsg = {"USER_ID" : userId , "DATA" : message}
        userManagerMsg = {"TYPE" : "SEND_MESSAGE_TO_USER" , "DATA" : userMsg}
        self.userManager.send(userManagerMsg)

    def handleUserDisconnect(self , userId):
        print("Handling User Disconnect !!!")
        # self.userList.remove(userId)
        print(self.userList)
        if self.jobProfile == "RENDERING":
            self.userDisconnectRender(userId)

# Basic Utility Section END !!! ----------------------------------------------------------------------------------------------


# Neural Network Training Section !!! -----------------------------------------------------------------------------------------

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
        self.accuracyList = [0.0 for users in self.userList]
        self.lossList = [100.0 for users in self.userList]

        self.finalModelWeights = self.model.get_weights()

        for epoch_number in range(self.epochs):
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
        response = requests.put("http://127.0.0.1:5555/updateCustomerData" , data = customerModelUpdateData , headers={"Content-Type" : "application/octet-stream"})

        print("Credential Server Responded with the Following Status Code : " , response.status_code)
        print("It Also Mentioned the Following Message : " , response.text)

        self.userManager.send({"TYPE" : "USER_RELEASED" , "USERS" :  self.userList})
        print("Model Training Finished !!!")

# Neural Network Section END !!! ---------------------------------------------------------------------------------------------





# Rendering Section !!! ------------------------------------------------------------------------------------------------------

    # Returns the Last and First Frame of a Scene in Blender
    def getLastAndFirstFrame(self , blendFileName):
        script_path = "getFrameRange.py"
        result = subprocess.run(["blender", "--background", blendFileName, "--python", script_path], capture_output=True , text = True)
        return result.stdout.split('\n')[:2]
    
    # Stores the Blend File In Local Directoy from the Binary it is given
    def saveBlendFileBinary(self , binaryBlendData , customerEmail):
        dir_path = f'CustomerData/{customerEmail}/InputBlendFiles'
        os.makedirs(dir_path , exist_ok=True)
        file_name = (datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        with open(f"{dir_path}/{str(file_name)}.blend" , "wb") as file:
            file.write(binaryBlendData)
        
        return str(file_name) + ".blend"

    # Assing Frames to Users when No Frame has been assigned to them , Does not send the frames to them
    def assignFramesToUsers(self , first_frame , last_frame , number_of_workers):
        frames_list = list(range(first_frame , last_frame + 1))
        id_to_frames = {}
        for worker_number in range(number_of_workers):
            id_to_frames[self.userList[worker_number]] = frames_list[first_frame + worker_number :: number_of_workers]
        
        return id_to_frames

    # Distribute Frames of a list among users and sends that to them
    def distributeFramesToUsers(self , frameList , number_of_workers):
        for worker_number in range(number_of_workers):
            # self.idToFrames[self.userList[worker_number]].extend(frameList[worker_number :: number_of_workers])
            self.addFrameToUser(self.userList[worker_number] , frameList[worker_number :: number_of_workers])

    # Add a List of Frames to a User and Sends that to them
    def addFrameToUser(self , userId , frameList):
        self.sendFramesToUser(userId , frameList)
        self.idToFrames[userId].extend(frameList)

    # Returns a Dictionary Storing the Status of Frames ranging from [Start Frame , End Frame]
    def getFrameStatusDict(self , start_frame , last_frame):
        frameStatus = {}
        for frame_number in range(start_frame , last_frame + 1):
            frameStatus[frame_number] = False

    # Broadcast the Blend File Among all the Users
    def sendBlendFileToUser(self , blendFileBinary):
        msg = {"TYPE" : "RENDER" , "BLEND_FILE" : blendFileBinary}
        self.broadcast(msg)
    
    # Sends the Frame List to a particular User
    def sendFramesToUser(self , userId , framesList):
        msg = {"TYPE" : "FRAME_LIST" , "FRAMES" : framesList}
        self.sendMessageToUser(userId , msg)
    
    # BroadCasts the Respective Frame List to respective Users.
    def broadcastFramesToUsers(self):
        for userId in self.userList:
            self.sendFramesToUser(userId , self.idToFrames[userId])

    # Sends the Message to User to Start the Rendering Process
    def initiateRenderProcess(self):
        for userId in self.userList:
            msg = {"TYPE" : "START_RENDERING"}
            self.sendMessageToUser(userId , msg)

    # Handles the Case When a User Disconnects and How to React to it
    def userDisconnectRender(self , userId):
        userFrames = self.idToFrames[userId]
        self.userList.remove(userId)
        fiteredFrames = [frame for frame in userFrames if self.frameStatus[frame] == False]
        del self.idToFrames[userId]
        self.distributeFramesToUsers(fiteredFrames , len(self.userList)) # Distributes and Sends the Data to Users

    # Handles What to Do After A User Has Completed Rendering a Frame and Sends it back to Server
    def handleFrameRenderCompletion(self , userId , data):
        pass

    def handle_rendering(self , renderingInfo):
        savedFileName = self.saveBlendFileBinary(renderingInfo["BLEND_FILE"] , self.customerEmail)
        first_frame , last_frame = self.getLastAndFirstFrame(savedFileName)
        number_of_workers = len(self.userList)
        self.idToFrames = self.assignFramesToUsers(first_frame , last_frame , number_of_workers)
        self.frameStatus = self.getFrameStatusDict(first_frame , last_frame)
        self.sendBlendFileToUser(renderingInfo["BLEND_FILE"])                               # Send the Blend file to users
        self.broadcastFramesToUsers()                                                       # Sends the relevant List of frames to respectives users
        self.initiateRenderProcess()                                                        # Directs the User to Start the Rendering Process


# Rendering Section END !!! --------------------------------------------------------------------------------------------------






    def runAndManageSession(self , data):
        self.gradReadingEvent = threading.Event()
        self.gradList_Lock = threading.Lock()

        print("Running and Managing Session !!!")
        print(data)

        userManagerThread = threading.Thread(target=self.listenToUserMessages)
        userManagerThread.start()

        
        self.jobProfile = data["DATA"]["JOB_PROFILE"]
        
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
        # self.preSetup(self.userList , self.customerEmail)
        print("Pre Setup for the Model Training Has been completed !!!")




# Main Training Functionalities

        print(self.jobProfile)
        if self.jobProfile == "NEURAL_NETWORK_TRAINING":
            self.customerEmail = data["EMAIL"]
            modelInfo = data["DATA"]

            self.currentDateTime = data["DATETIME"]
            print("Current Date Time : " , self.currentDateTime)

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
        elif self.jobProfile == "RENDERING":
            self.customerEmail = data["EMAIL"]
            renderingInfo = data["DATA"]
            self.handle_rendering(renderingInfo)
        else:
            pass



# End of Session Manager

        userManagerThread.join()


        



        