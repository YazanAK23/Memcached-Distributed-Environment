Open Windows Terminal or Command Prompt: 
wsl --install
wsl --install -d ubantu

Create a virtual Environment to run Python Commands And Library:
python3 -m venv venv
source venv/bin/activate

commands to install memcached  : 

sudo apt update
sudo apt install memcached

start the Memcached service:
sudo service memcached start



to run nodes on container by Doceker
docker run -d --name node1 -p 11211:11211 memcached
docker run -d --name node2 -p 11212:11211 memcached
docker run -d --name node3 -p 11213:11211 memcached

Prepare Docker Compose
docker-compose up -d

simulate for An failove node
docker stop node2

verify my node connections
docker ps



Verify the Server Status:
ps aux | grep memcached