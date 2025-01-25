# import multiprocessing as mp


# from ..service_SessionSupervisor.sessionSupervisor import sessionSupervisor

# class customerAgent():
#     def __init__(self , userManagerPipe):
#         self.sessionData = None
#         self.sessionSupervisorPipe , self.backToCustomerAgentPipe = mp.Pipe()
#         self.userManagerPipe = userManagerPipe
#         self.sessionSupervisor = sessionSupervisor(self.backToCustomerAgentPipe , self.userManagerPipe)

#     def initializeSession(self , sessionData):
#         self.sessionData = sessionData
#         self.sessionSupervisor_Process = mp.Process(target=self.sessionSupervisor.runAndManageSession , args=(sessionData,))
#         print("Session Supervisor Process Created and it has Started Working !!!")
#         self.sessionSupervisor_Process.start()


#     def handleSessionRequests(self , customerRequest):
#         print(customerRequest)
#         pass




import uuid
import json 
import subprocess
import os
import socket

from ServiceTemplates.Basic.MESSAGE_QUEUE import MessageQueue


class customerAgent():
    def __init__(self):
        self.sessionData = None
        self.SessionSupervisorID = None
        self.SessionSupervisorRoutingKey = None

        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/" , "CUSTOMER_AGENT_EXCHANGE")

    def CheckGenerateSessionIdIsUnique(self , sessionID):
        return True

    def GenerateUniqueSessionID(self):
        while True:
            sessionID = uuid.uuid4().hex
            if self.CheckGenerateSessionIdIsUnique(sessionID):
                self.SessionSupervisorID = sessionID
                self.SessionSupervisorRoutingKey = f"SSE_{sessionID}_CA"
                return sessionID

    def CheckPortFree(self , port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    def FindFreePort(self):
        for portNumber in range(15000,16000):
            if self.CheckPortFree(portNumber):
                return portNumber

    def SpawnSessionSupervisorService(self):
        portToRunService = self.FindFreePort()
        print("Running on Port : " , portToRunService)
        subprocess.Popen(["python3" , "service_SessionSupervisor/sessionSupervisor.py" , "--host", "127.0.0.1" , "--port", f"{portToRunService}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        # Command to Run the Session Supervisor Service With On the Specific Port

    async def InitializeSession(self , sessionData):
        await self.messageQueue.InitializeConnection()

        self.sessionData = sessionData


        sessionId = self.GenerateUniqueSessionID()
        print(sessionId)
        await self.messageQueue.Channel.declare_exchange("SESSION_SUPERVISOR_EXCHANGE" , type="direct")

        sessionSupervisorQueue =  await self.messageQueue.Channel.declare_queue(f"SSE_{sessionId}_CA" , auto_delete=True)
        await sessionSupervisorQueue.bind("SESSION_SUPERVISOR_EXCHANGE" , routing_key=f"SSE_{sessionId}_CA")

        sessionInfo = {"SESSION_DATA" : self.sessionData , "SESSION_ID" : sessionId}
        messageToPublish = {"TYPE" : "SESSION_INIT_DATA" , "DATA" : sessionInfo}
        messageToPublish = json.dumps(messageToPublish)

        await self.messageQueue.PublishMessage("SESSION_SUPERVISOR_EXCHANGE" , f"SSE_{sessionId}_CA" , messageToPublish)

        self.SpawnSessionSupervisorService()

        





