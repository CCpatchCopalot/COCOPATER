# gpac Source code compilation environment construction

# Construction process
```shell
docker build -t poc-bento4 .
docker run -itd --name poc-bento4 poc-bento4
docker exec -it poc-bento4 /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone git@github.com:axiomatic-systems/Bento4.git

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-bento4:1.0
# Steps to use
mkdir cmakebuild\
cd cmakebuild\
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer" ..\
make