import subprocess

def find_pid_by_port(port):
    """Find the PID of the process running on the specified port."""
    result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if len(lines) > 1:
        # Extract the PID from the output
        pid = int(lines[1].split()[1])
        return pid
    return None

def stop_service_on_port(port):
    """Stop the service running on the specified port."""
    pid = find_pid_by_port(port)
    if pid:
        subprocess.run(["sudo", "kill", "-9", str(pid)])
        print(f"{port} : Service Stopped")
    else:
        print(f"{port} : No Service Found")



def stopServer():
    # portList = [5500, 5555, 6000, 6001, 7000, 8000,8001, 20000]
    portList = [5500, 6000, 6001, 7000, 8000,8001, 20000]

    portList.extend([i for i in range(15000,15010)])

    for ports in portList:
        stop_service_on_port(ports)

    stopRabbitMQ


def stopRabbitMQ():
    command = "docker stop rabbit-server"
    subprocess.run(command)

stopServer()
