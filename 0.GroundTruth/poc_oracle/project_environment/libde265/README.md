# libde265 Source code compilation environment construction

# Construction process
```shell

docker build -t poc-libde265 .
docker run -itd --name poc-libde265 poc-libde265
docker exec -it poc-libde265 /bin/bash

apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the Vim repository. (ssh-keygen)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat ~/.ssh/id_rsa.pub
# The output of the previous stepssh keyAdd togithub

git clone git@github.com:strukturag/libde265.git

# add compiler
apt install  clang wget automake libtool m4 pkg-config -y

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-libde265:1.0

# Steps to use
1. git reset designate version
2. sh autogen.sh
3. mkdir build
4. cd build
5. CC=clang CXX=clang++ cmake ../ -DCMAKE_CXX_FLAGS="-fsanitize=address"
6. make -j$(nproc)
7. ./dec265/dec265 poc
