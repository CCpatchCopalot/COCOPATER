# gpmf-parser Source code compilation environment construction

# Construction process
```shell
docker run -it --network host --name gpmf-parser ubuntu:18.04 /bin/bash

# Preparing the initial environment
apt-get update -y &&
apt-get install git wget clang cmake zip -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
mkdir poc;cd /poc
git clone https://github.com/gopro/gpmf-parser.git

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-gpmf-parser:1.0

mkdir build; cd build
cmake ..
make -j