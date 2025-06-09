# ImageMagick Source code compilation environment construction

# Construction process
```shell

docker build -t poc-imagemagick .
docker run -itd --name poc-imagemagick poc-imagemagick
docker exec -it poc-imagemagick /bin/bash

apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the Vim repository. (ssh-keygen)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat ~/.ssh/id_rsa.pub
# The output of the previous stepssh keyAdd togithub

git clone git@github.com:ImageMagick/ImageMagick.git

# add compiler
apt install gcc make clang libtool-bin build-essential llvm-dev libunwind-dev libmagickwand-dev -y

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-imagemagick:1.0

# Steps to use
1. git reset designate version
2. CC=clang CXX=clang++ CFLAGS="-fsanitize=address,undefined -g" CXXFLAGS="-fsanitize=address,undefined -g" ./configure  --disable-openmp
3. make -j$(nproc)
4. make install
5. ldconfig
