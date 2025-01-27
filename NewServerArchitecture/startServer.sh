clear

sudo docker stop rabbit-server
sleep 1

sudo docker run -d --rm --name rabbit-server -p 5672:5672 -p 15672:15672 rabbitmq:3-management
sleep 10

/home/Server/bin/python3.12 service_UserManager/userManager.py &
/home/Server/bin/python3.12 service_CommunicationInterface/communicationInterface.py &
/home/Server/bin/python3.12 service_UserHTTPserver/userHTTPserver.py &
/home/Server/bin/python3.12 service_UserWSserver/userWSserver.py &
/home/Server/bin/python3.12 service_CustomerServer/customerServer.py 
