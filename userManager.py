import asyncio

class UserManager:
    def __init__(self):
        self.users = []
        self.userToCustomerEmailMapping = {} # Email Address of Customer Linked to the User associated with it
        self.supervisorToPipeMapping = {} # Session Supervisor (Same As Customer Email) Linked to the Pipe associated with it
        self.supervisorToCoroutineMapping = {} # Session Supervisor (Same as Customer Email) Linked to the Coroutine associated with it
        self.userServer_Pipe = None
        self.customerServer_Pipe = None
        self.asyncLoop = None

    async def handleSupervisorRequests(self , pipe , supervisorRequest , supervisorIdentityEmail):
        message = supervisorRequest['TYPE']
        if message == "NEW_SESSION":
            print("New Session Request !!!")
            userNumber = supervisorRequest['USERS']
            if userNumber == "ALL":
                if len(self.users) == 0:
                    jsMsg = {"TYPE" : "USER_LIST" , "USERS" : [] , "NOTICE" : "NOT_SUFFICIENT"}
                    pipe.send(jsMsg)
                    return
                
                jsMsg = {"TYPE" : "USER_LIST" , "USERS" : self.users[:] , "NOTICE" : "SUFFICIENT"}
                for user in self.users[:]:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send(jsMsg)
                self.users = []
            elif len(self.users) < userNumber:
                jsMsg = {"TYPE" : "USER_LIST" , "USERS" : self.users , "NOTICE" : "NOT_SUFFICIENT"}
                for user in self.users:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send(jsMsg)
                self.users = []
            else:
                jsMsg = {"TYPE" : "USER_LIST" , "USERS" : self.users[:userNumber] , "NOTICE" : "SUFFICIENT"}
                for user in self.users[:userNumber]:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send(jsMsg)
                self.users = self.users[userNumber:]

            print("Remaining Users : " , self.users)
        elif message == "ADDITIONAL_USERS":
            print("Additional Users Request !!!")
            userNumber = supervisorRequest['USERS']
            if userNumber == "ALL":
                if len(self.users) == 0:
                    jsMsg = {"TYPE" : "ADDITIONAL_USER_LIST" , "USERS" : [] , "NOTICE" : "NOT_SUFFICIENT"}
                    pipe.send({"TYPE" : "USER_MANAGER_MESSAGE" , "DATA" : jsMsg})
                    return
                
                jsMsg = {"TYPE" : "ADDITIONAL_USER_LIST" , "USERS" : self.users[:] , "NOTICE" : "SUFFICIENT"}
                for user in self.users[:]:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send({"TYPE" : "USER_MANAGER_MESSAGE" , "DATA" : jsMsg})
                self.users = []
            elif len(self.users) < userNumber:
                jsMsg = {"TYPE" : "ADDITIONAL_USER_LIST" , "USERS" : self.users , "NOTICE" : "NOT_SUFFICIENT"}
                for user in self.users:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send({"TYPE" : "USER_MANAGER_MESSAGE" , "DATA" : jsMsg})
                self.users = []
            else:
                jsMsg = {"TYPE" : "ADDITIONAL_USER_LIST" , "USERS" : self.users[:userNumber] , "NOTICE" : "SUFFICIENT"}
                for user in self.users[:userNumber]:
                    self.userToCustomerEmailMapping[user] = supervisorIdentityEmail
                pipe.send({"TYPE" : "USER_MANAGER_MESSAGE" , "DATA" : jsMsg})
                self.users = self.users[userNumber:]

            print("Remaining Users : " , self.users)
        elif message == "SEND_MESSAGE_TO_USER":
            print("Sending Message to User Server For Further Execution of The Request SEND_MESSAGE_TO_USER!!!")
            self.userServer_Pipe.send(supervisorRequest)
        elif message == "USER_RELEASED":
            print("User Released !!!")
            userIds = supervisorRequest['USERS']
            print("List of Users Released : " , userIds)
            self.users.extend(userIds)
            print(self.users)


    async def listenToSupervisorMessages(self , supervisorPipe , supervisorIdentityEmail):
        print("Listening to Supervisor Messages !!!")
        while True:
            #print("Supervisor Listeninig")
            if supervisorPipe.poll():
                supervisorRequest = supervisorPipe.recv()
                await self.handleSupervisorRequests(supervisorPipe , supervisorRequest , supervisorIdentityEmail)
            await asyncio.sleep(1)



    async def handleCustomerServerRequests(self , serverCommunicationPipe , serverRequest):
        message = serverRequest['TYPE']
        if message == "NEW_SESSION":
            # print("Creating New Session !!")
            self.supervisorToPipeMapping[serverRequest['EMAIL']] = serverRequest['SUPERVISOR_PIPE']
            self.supervisorToCoroutineMapping[serverRequest['EMAIL']] = asyncio.create_task(self.listenToSupervisorMessages(serverRequest['SUPERVISOR_PIPE'] , serverRequest['EMAIL']))
            print("Number of Currently Running Sessions : " , len(self.supervisorToPipeMapping))
            print("User Manager Current Job Finished for Creation of New Sessions !!!!")
        # elif message == "USER_MESSAGE":
        #     print("User Message Receuved by User Manager !!!")
        #     print("\n\n")
        #     userMessage = serverRequest['MESSAGE']
        #     userId = serverRequest['USER_ID']
        #     supervisor = self.userToCustomerEmailMapping[userId]
        #     supervisorPipe = self.supervisorToPipeMapping[supervisor]
        #     supervisorPipe.send({"USER_ID" : userId , "DATA" : userMessage})
        # elif message == "NEW_USER":
        #     print("New User Detected !!!")
        #     self.users.append(serverRequest['USER_ID'])
        #     print(self.users)
        else:
            pass

    async def listenToCustomerServerMessages(self , customerServerPipe):
        print("Listening to Customer Server Messages !!!")
        #res = await serverCommunicationPipe.recv()
        while True:
            #print("Server Listening")
            #print(serverCommunicationPipe)
            if customerServerPipe.poll():
                serverRequest = customerServerPipe.recv()
                print("Server Request : " , serverRequest)
                await self.handleCustomerServerRequests(customerServerPipe , serverRequest)
            await asyncio.sleep(1)



    async def handleUserServerRequests(self , serverCommunicationPipe , serverRequest):
        message = serverRequest['TYPE']
        if message == "USER_MESSAGE":
            print("User Message Receuved by User Manager !!!")
            userMessage = serverRequest['MESSAGE']
            userId = serverRequest['USER_ID']
            if self.userToCustomerEmailMapping[userId] in self.supervisorToPipeMapping.keys():
                supervisor = self.userToCustomerEmailMapping[userId]
                supervisorPipe = self.supervisorToPipeMapping[supervisor]
                userData = {"USER_ID" : userId , "MESSAGE" : userMessage}
                supervisorPipe.send({"TYPE" : "USER_MESSAGE" , "DATA" : userData})
                # supervisorPipe.send({"USER_ID" : userId , "MESSAGE" : userMessage})
        elif message == "NEW_USER":
            print("New User Detected !!!")
            self.users.append(serverRequest['USER_ID'])
            print(self.users)
        elif message == "REMOVE_USER":
            print("User Removed !!!")
            userId = serverRequest['USER_ID']
            if userId in self.users:
                self.users.remove(userId)
            else:
                supervisorIdentiy = self.userToCustomerEmailMapping[userId]
                supervisorPipe = self.supervisorToPipeMapping[supervisorIdentiy]
                userManagerMessage = {"USER_ID" : userId , "TYPE" : "DISCONNECT"}
                supervisorPipe.send({"TYPE" : "USER_MANAGER_MESSAGE" , "DATA" : userManagerMessage})
            print(self.users)
        else:
            pass

    async def listenToUserServerMessages(self , userServerPipe):
        print("Listening to User Server Messages !!!")
        #res = await serverCommunicationPipe.recv()
        while True:
            #print("Server Listening")
            #print(serverCommunicationPipe)
            if userServerPipe.poll():
                serverRequest = userServerPipe.recv()
                #print("Server Request : " , serverRequest)
                await self.handleUserServerRequests(userServerPipe , serverRequest)
            await asyncio.sleep(1)




    async def startFunctioning(self , customerServerPipe , userServerPipe):
        self.userServer_Pipe = userServerPipe
        self.customerServer_Pipe = customerServerPipe
        customerServerMessages_Coroutine = asyncio.create_task(self.listenToCustomerServerMessages(customerServerPipe))
        userServerMessages_Coroutine = asyncio.create_task(self.listenToUserServerMessages(userServerPipe))
        await asyncio.gather(customerServerMessages_Coroutine , userServerMessages_Coroutine)

    def Start(self , customerServerPipe , userServerPipe = None):
        #print(serverCommunincationPipe)
        #serverCommunincationPipe.send("User Manager Started !!!")
        #print(serverCommunincationPipe.recv())
        self.asyncLoop = asyncio.get_event_loop()
        asyncio.run(self.startFunctioning(customerServerPipe , userServerPipe))


