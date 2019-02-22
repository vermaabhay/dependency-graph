Infra Dependency Graph. This project comprises of following parts -
1 - App : Python
2 - Cache : Redis
3 - Datastore : Neo4j
####################################################################

Steps To Run :

####################################################################

Datastore : Neo4j

1 - Stepup & Install Neo4j version 3.4.7
2 - Run two instances of the datastore.
3 - Create a user for authenication. And put the credentials in scripts/config.properties file.

#####################################################################

Cache : Redis
1 - Setup & Install Redis version 5.0.0.
2 - Authentication not required.

####################################################################

App : Python 

1 - yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel
2 - cd /opt && wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tgz
3 - tar -xzf Python-3.6.2.tgz && cd Python-3.6.2 && ./configure --prefix=/opt/python-3.6.2 --with-ssl
4 - make && make install
5 - echo "export PATH=/opt/python-3.6.2/bin:$PATH" >> /etc/profile
6 - source /etc/profile
7 - pip3 install virtualenv && virtualenv -p python3 /opt/project
8 - source /opt/project/bin/activate
9 - pip install --upgrade pip && pip install pip-tools
10 - pip-sync requirements.txt
11 - Fill the file scripts/config.properties with correct credentials. Gitlab section can be left blank.
12 - python dependency-graph.py (This will run the app)
