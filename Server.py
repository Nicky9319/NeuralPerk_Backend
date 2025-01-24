import multiprocessing

import subprocess

from customerServer import CustomerServer
from userManager import UserManager
from userServer import UserServer



if __name__ == "__main__":
    customerServer = CustomerServer()
    userManager = UserManager()
    userServer = UserServer()

    
    customerServer_UserManagerPipe , userManager_CustomerServerPipe = multiprocessing.Pipe()
    userServer_UserManaegerPipe , userManager_UserServerPipe = multiprocessing.Pipe()


    mainServer_Process = multiprocessing.Process(target=customerServer.startServer , args=(customerServer_UserManagerPipe,))
    mainServer_Process.start()

    
    userServer_Process = multiprocessing.Process(target=userServer.startServer , args=(userServer_UserManaegerPipe,))
    userServer_Process.start()

    userManager_Process = multiprocessing.Process(target=userManager.Start , args=(userManager_CustomerServerPipe, userManager_UserServerPipe))
    userManager_Process.start()


    mainServer_Process.join()
    userManager_Process.join()
    userServer_Process.join()

