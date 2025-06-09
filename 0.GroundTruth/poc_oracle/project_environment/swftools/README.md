# swftools Source code compilation environment construction
Construction process
```shell
docker build -t poc-swftools .
docker run -itd --name poc-swftools poc-swftools
docker exec -it poc-swftools /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone https://github.com/swftools/swftools.git

# Install the compilation and installation dependencies.
apt install gcc g++ make libtool libfreetype6-dev libgif-dev libjpeg-dev zlib1g-dev python3-dev ruby-dev
```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-swftools:1.0
# Steps to use

1. 切换到需要的分支
2.  vim lib/lame/quantize.c Revise // inline
void bitpressure_strategy1( Comment out inline， It's not known why the compilation failed
3. ./configure --disable-shared CFLAGS="-fsanitize=address" CXXFLAGS="-fsanitize=address" LDFLAGS="-fsanitize=address"
4. make -j$(nproc)
5. make install