import time
import threading
# import tensorflow as tf
# import keras
import pickle
import requests
import json
import subprocess
import os
import datetime

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
        elif(messageType == "FRAME_RENDERED"):
            print("Frame Rendered Successfully By user : " , userId)
            self.handleFrameRenderCompletion(userId , mainMessage)
        elif(messageType == "RENDER_COMPLETED"):
            print("Rendering Completed By User : " , userId)
            self.handleRenderingProcessCompletionCheck(userId)
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
        # avgModel = keras.models.model_from_json(self.model.to_json())
        # layerLength = len(avgModel.layers)
        # gradModel = keras.models.model_from_json(self.model.to_json())
        # gradModel.set_weights(self.gradList[0])
        # for ind in range(1 , len(self.gradList)):
        #     print(ind)
        #     gradModel.set_weights(self.aggregateGrads(gradModel.get_weights() , self.gradList[ind]))
        # avgModel.set_weights(self.meanGrads(gradModel.get_weights() , len(self.gradList)))
        # self.gradReadingEvent.clear()
        # self.gradList = [None for indices in range(len(self.userList))]
        # #print("After Finding Aggregated Gradients !! , GradList = " , gradList)

        # self.currentAccuracy = avgAccuracy
        # self.currentLoss = avgLoss
        # return avgModel

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
        print(result)
        return result.stdout.split('\n')[:2]
    
    # Stores the Blend File In Local Directoy from the Binary it is given and also stores the name of the Folder
    def saveBlendFileBinary(self , binaryBlendData , customerEmail):
        dir_path = f'CustomerData/paarthsaxena2005@gmail.com/Rendering'
        os.makedirs(dir_path , exist_ok=True)

        file_name = (datetime.datetime.now().strftime("%Y-%m-%d,%H-%M-%S"))
        sub_dir_path = f'{dir_path}/{file_name}'
        os.makedirs(sub_dir_path , exist_ok=True)

        input_file_path = f'{sub_dir_path}/InputBlendFile'
        os.makedirs(input_file_path , exist_ok=True)

        output_file_path = f'{sub_dir_path}/RenderedFiles'
        os.makedirs(output_file_path , exist_ok=True)

        renderer_images_path = f'{output_file_path}/Images'
        os.makedirs(renderer_images_path , exist_ok=True)

        renderer_videos_path = f'{output_file_path}/Video'
        os.makedirs(renderer_videos_path , exist_ok=True)

        with open(f"{input_file_path}/{str(file_name)}.blend" , "wb") as file:
            file.write(binaryBlendData)
        
        self.currentFolder = sub_dir_path
        self.renderedImagesFolder = renderer_images_path
        return f"{input_file_path}/{str(file_name)}" + ".blend"

    # Assing Frames to Users when No Frame has been assigned to them , Does not send the frames to them
    def assignFramesToUsers(self , first_frame , last_frame , number_of_workers):
        # print("ASSIGN FRAMES TO USERS CODE SNIPPET")
        # print(first_frame , last_frame , number_of_workers)
        frames_list = list(range(first_frame , last_frame + 1))
        # print("FRAMES LIST NOTIONAL")
        # print(frames_list)
        id_to_frames = {}
        for worker_number in range(number_of_workers):
            print("WORKER NUMBER  : " , worker_number)
            print(first_frame + worker_number)
            print(frames_list[first_frame + worker_number :: number_of_workers])
            id_to_frames[self.userList[worker_number]] = frames_list[worker_number :: number_of_workers]
        
        # print(f"Frames Assigned to Each User : \n", id_to_frames)
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
        # print("FRAME STATUS DICT CODE SNIPPET")
        # print(start_frame , last_frame)
        frameStatus = {}
        for frame_number in range(start_frame , last_frame + 1):
            # print(frame_number)
            frameStatus[frame_number] = False
            # print(frameStatus[frame_number])
        
        # print(f"Frame Status Dict Before Sending : \n" , frameStatus)
        return frameStatus

    # Broadcast the Blend File Among all the Users
    def sendBlendFileToUser(self , blendFileBinary):
        msg = {"TYPE" : "BLEND_FILE" , "DATA" : blendFileBinary}
        self.broadcast(msg)
    
    # Sends the Frame List to a particular User
    def sendFramesToUser(self , userId , framesList):
        msg = {"TYPE" : "FRAME_LIST" , "DATA" : framesList}
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

    # Saves the Binary Image derived from Binary in Local Directory with it's extension
    def saveImageInDirectory(self, imageBinary , frameNumber , ext = 'png'):
        print("Image Saved FRAME NUMBER : " , frameNumber)
        # print(self.currentFolder)
        # print(self.renderedImagesFolder)
        with open(self.renderedImagesFolder + f"/{frameNumber}.{ext}" , "wb") as file:
            file.write(imageBinary)

    # Handles What to Do After A User Has Completed Rendering a Frame and Sends it back to Server
    def handleFrameRenderCompletion(self , userId , data):
        print(f"USER {userId} RENDERED FRAME {data['FRAME_NUMBER']}")
        frameNumber = data["FRAME_NUMBER"]
        imageBinary = data["DATA"]
        imageExtension = data["IMAGE_EXTENSION"]
        self.saveImageInDirectory(imageBinary , frameNumber , imageExtension)
        self.frameStatus[frameNumber] = True
        self.idToFrames[userId].remove(frameNumber)
        self.totalFrame -= 1
        if self.totalFrame == 0:
            msg = msg = {"TYPE" : "MESSAGE_FOR_PROCESS_MANAGER" , "DATA" : {"TYPE" : "RENDERING_COMPLETE"}}
            self.broadcast(msg)
            self.renderingCompletion.set()
        print(f"Remaing Frames of User {userId} : " , self.idToFrames[userId])
        
    # Aftermath when a user Says it has completed its process
    def handleRenderingProcessCompletionCheck(self , userId):
        print(self.idToFrames[userId])
        if(len(self.idToFrames[userId]) == 0):
            print("Rendering Process Completed !!!")
            msg = {"TYPE" : "MESSAGE_FOR_PROCESS_MANAGER" , "DATA" : {"TYPE" : "RENDERING_COMPLETE"}}
            self.sendMessageToUser(userId , msg)
        else:
            print("Asking User to Send Frames !!!")
            print("Frame List Pending !!!! : " , self.idToFrames[userId])
            msg = {"TYPE" : "MESSAGE_FOR_PROCESS_MANAGER" , "DATA" : {"TYPE" : "SEND_FRAMES" , "DATA" : self.idToFrames[userId]}}
            self.sendMessageToUser(userId , msg)

    # Combining the Indiviual Frames to Final Video
    def reconcileFrameToVideo(self):
        print("Reconciling the Frames to Video !!!")
        pass

    # Main Function to Handle the Rendering Process
    def handle_rendering(self , renderingInfo):
        savedFileName = self.saveBlendFileBinary(renderingInfo["DATA"] , self.customerEmail)
        last_frame , first_frame = self.getLastAndFirstFrame(savedFileName)
        print(last_frame , first_frame)
        first_frame = int(first_frame)
        last_frame = int(last_frame)
        # first_frame = 2
        # last_frame = 15
        print(type(first_frame) , first_frame , type(last_frame) , last_frame)
        number_of_workers = len(self.userList)
        print(f"Number of Worker Nodes : " , number_of_workers)
        self.idToFrames = self.assignFramesToUsers(first_frame , last_frame , number_of_workers)
        self.frameStatus = self.getFrameStatusDict(first_frame , last_frame)
        self.totalFrame = len(self.frameStatus.keys())
        # print(self.userList)
        print(f"Frame Division to Each Worker : " , self.idToFrames)
        # print(f"Frame Status Dict : {self.frameStatus}")

        self.sendBlendFileToUser(renderingInfo["DATA"])                               # Send the Blend file to users
        self.broadcastFramesToUsers()                                                       # Sends the relevant List of frames to respectives users
        self.initiateRenderProcess()                                                        # Directs the User to Start the Rendering Process
        print("Workers Started Rendering the Scenes")

        self.renderingCompletion.wait()
        self.reconcileFrameToVideo()
        print("Rendering Process Completed !!!")
        self.renderingCompletion.clear()
        # self.renderingCompletion.clear(self.customerEmail)

# Rendering Section END !!! --------------------------------------------------------------------------------------------------






    def runAndManageSession(self , data):
        self.gradReadingEvent = threading.Event()
        self.gradList_Lock = threading.Lock()

        self.renderingCompletion = threading.Event()

        print("Running and Managing Session !!!")
        # print(data)

        userManagerThread = threading.Thread(target=self.listenToUserMessages)
        userManagerThread.start()

        
        self.jobProfile = data["DATA"]["JOB_PROFILE"]
        
        self.userList = []

        while True:
            if(len(self.userList) == 0):
                jsMsg = {"TYPE" : "NEW_SESSION" , "USERS" : "ALL"}
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
        # print("Pre Setup for the Model Training Has been completed !!!")




# Main Training Functionalities

        # print(self.jobProfile)
        print("\n\n")
        if self.jobProfile == "NEURAL_NETWORK_TRAINING":
            pass
            # self.customerEmail = data["EMAIL"]
            # modelInfo = data["DATA"]

            # self.currentDateTime = data["DATETIME"]
            # print("Current Date Time : " , self.currentDateTime)

            # print(type(modelInfo["MODEL_JSON"]))
            # self.model = keras.models.model_from_json(json.dumps(modelInfo["MODEL_JSON"]))
            # print(self.model.summary())
            # self.epochs = modelInfo["EPOCHS"]
            
            # self.handle_model_training(modelInfo)

            # response = requests.put("http://127.0.0.1:5500/updateSessionStatus" , json = {"EMAIL" : self.customerEmail , "STATUS" : "IDLE"})
            # if response.status_code == 200:
            #     print("Session Status Updated Successfully !!")
            # else:
            #     print("Session Status Updation Failed !!")
        elif self.jobProfile == "RENDERING":
            self.customerEmail = data["EMAIL"]
            renderingInfo = data["DATA"]
            self.handle_rendering(renderingInfo)
        else:
            pass



# End of Session Manager

        userManagerThread.join()


        



        