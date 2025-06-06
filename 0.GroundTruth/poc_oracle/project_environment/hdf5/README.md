# gpac Source code compilation environment construction

# Construction process
```shell
docker build -t poc-hdf5 .
docker run -itd --name poc-hdf5 poc-hdf5
docker exec -it poc-hdf5 /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone git@github.com:HDFGroup/hdf5.git

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-hdf5:1.0
# Steps to use
exist最高的几个版本中, Noconfiguredocument
cd hdf5\
CC=gcc CXX=g++ ./configure --enable-cxx --disable-fortran --disable-quadmath --prefix=/usr/local/hdf5 \
make\
make install \
/usr/local/hdf5/bin/(commands)

# existubuntu18:04 Mirror in
apt-get install git wget zip build-essential automake autoconf libtool

ln -s /usr/bin/libtoolize /libtoolize
image_id: meilabixiaoxin/poc-hdf5:2.0

cd hdf5\
./autogen.sh
CC=gcc CXX=g++ ./configure --enable-cxx --disable-fortran --disable-quadmath --prefix=/usr/local/hdf5 \
make\
