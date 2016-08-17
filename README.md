prepare:

dio prepare dce:1.4.1
dio prepare --compose=1.8.0 --dce=1.4.0 --docker=1.2.0 --lsb=centos:7.0 --image=
dio prepare -c config.json


dist \
	  dce-1.4.1 \
	  			 docker-1.12.0-ubuntu-16.04.tar.gz
	  			 dce-1.4.0.tar.gz
	  			 docker-compose-Linux-x86_64
	  			 install.sh

install:

dio install

pack and send dist/dce-1.4.1 to remote
unpack and run install.sh