# gpac Source code compilation environment construction

# Construction process
```shell
docker build -t poc-glibc .
docker run -itd --name poc-glibc poc-glibc
docker exec -it poc-glibc /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone git://sourceware.org/git/glibc.git

```

# Steps to use
cd glibc
mkdir build
cd build
../configure CC=gcc CXX=g++ LD=ld CFLAGS="-O2 -fsanitize=address" CXXFLAGS="-O2 -fsanitize=address" LDFLAGS="-fsanitize=address"  --prefix=/opt/glibc
make -j$(nproc)
make install
