# gpac Source code compilation environment construction

# Construction process
```shell
docker build -t poc-gpac .
docker run -itd --name poc-gpac poc-gpac
docker exec -it poc-gpac /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone git@github.com:gpac/gpac.git


# Install the compilation and installation dependencies.
apt install gcc gdb make pkg-config libtool-bin build-essential llvm-dev libunwind-dev -y
```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-gpac:1.0
# Steps to use


# fix：
# Construction process
```shell
docker run -itd ubuntu:18.04 /bin/bash

# Preparing the initial environment
apt update -y
apt install git zip -y
apt install zlib1g-dev libfreetype6-dev libjpeg62-dev libpng-dev libmad0-dev libfaad-dev libogg-dev libvorbis-dev libtheora-dev liba52-0.7.4-dev libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libavdevice-dev libnghttp2-dev libopenjp2-7-dev libcaca-dev libxv-dev x11proto-video-dev libgl1-mesa-dev libglu1-mesa-dev x11proto-gl-dev libxvidcore-dev libssl-dev libjack-jackd2-dev libasound2-dev libpulse-dev libsdl2-dev dvb-apps mesa-utils libcurl4-openssl-dev
# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone git@github.com:gpac/gpac.git


# Install the compilation and installation dependencies.
```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-gpac:3.0
# Steps to use
 LDFLAGS="-fsanitize=address -ldl" ./configure --extra-cflags="-O0 -g3 -fsanitize=address -fno-omit-frame-pointer" && make -j$(nproc) && make install
