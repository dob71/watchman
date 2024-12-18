#!/bin/bash
# Install docker under Ubuntu 22.04

echo
echo "Add Docker's official GPG key"
echo "(Ctrl-C to terminate, s - skip the step, just Enter to continue)"
read REPLAY
if [ "$REPLAY" != "s" ]; then
set -v
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
set +v
fi

echo
echo "Add the repository to Apt sources"
echo "(Ctrl-C to terminate, s - skip the step, just Enter to continue)"
read REPLAY
if [ "$REPLAY" != "s" ]; then
set -v
# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
set +v
fi

echo
echo "Install latest docker packages"
echo "(Ctrl-C to terminate, s - skip the step, just Enter to continue)"
read REPLAY
if [ "$REPLAY" != "s" ]; then
set -v
# Install latest
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 
set +v
fi

echo
echo "Test the docker installation"
echo "(Ctrl-C to terminate, s - skip the step, just Enter to continue)"
read REPLAY
if [ "$REPLAY" != "s" ]; then
set -v
# Test the installation
sudo docker run hello-world
set +v
fi

echo
echo "Add current user to the docker group"
echo "(Ctrl-C to terminate, s - skip the step, just Enter to continue)"
read REPLAY
if [ "$REPLAY" != "s" ]; then
set -v
# Add current user to the docker group
sudo groupadd docker
sudo gpasswd -a $USER docker
newgrp docker
docker run hello-world
set +v
fi

sudo apt  install docker-compose

echo "All Done"
