import subprocess
import time

def runScript(location):
    process = subprocess.Popen(['gnome-terminal', "--",  'python', location], shell=False)

mainServer = "Server.py"
credentialServer = "credentialServer.py"

runScript(mainServer)
runScript(credentialServer)


