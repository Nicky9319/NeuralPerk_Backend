import multiprocessing as mp

from sessionSupervisor import sessionSupervisor

class customerAgent():
    def __init__(self , userManagerPipe):
        self.sessionData = None
        self.sessionSupervisorPipe , self.backToCustomerAgentPipe = mp.Pipe()
        self.userManagerPipe = userManagerPipe
        self.sessionSupervisor = sessionSupervisor(self.backToCustomerAgentPipe , self.userManagerPipe)

    def initializeSession(self , sessionData):
        self.sessionData = sessionData
        self.sessionSupervisor_Process = mp.Process(target=self.sessionSupervisor.runAndManageSession , args=(sessionData,))
        print("Session Supervisor Process Created and it has Started Working !!!")
        self.sessionSupervisor_Process.start()


    def handleSessionRequests(self , customerRequest):
        print(customerRequest)
        pass
