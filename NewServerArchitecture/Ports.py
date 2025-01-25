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
        print(f"Service on port {port} has been stopped.")
    else:
        print(f"No service found running on port {port}.")

def list_working_ports():
    """List all the ports on which services are currently running."""
    result = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    ports = set()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) > 8 and ':' in parts[8]:
            port = parts[8].split(':')[-1]
            if port.isdigit():
                ports.add(int(port))
    return sorted(ports)



ports_to_stop = [x for x in range(15000,15025)]  
for port in ports_to_stop:
    stop_service_on_port(port)

working_ports = list_working_ports()
print("Working Ports: ", working_ports)
