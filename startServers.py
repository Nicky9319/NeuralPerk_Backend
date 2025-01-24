import subprocess
import time

def runScript(location):
    process = subprocess.Popen(['start', 'cmd', '/k', 'python', location], shell=True)

mainServer = "Server.py"
credentialServer = "credentialServer.py"

runScript(mainServer)
runScript(credentialServer)


