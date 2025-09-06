# ffmpeg Source code compilation environment construction

# Construction process
```shell
docker build -t poc-ffmpeg .
docker run -itd --name poc-ffmpeg poc-ffmpeg
docker exec -it poc-ffmpeg /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg


# Install the compilation and installation dependencies.

# Install basic build tools
apt-get update -qq &&  apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  git-core \
  libass-dev \
  libfreetype6-dev \
  libgnutls28-dev \
  libmp3lame-dev \
  libsdl2-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  meson \
  ninja-build \
  pkg-config \
  texinfo \
  wget \
  yasm \
  zlib1g-dev
```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-ffmpeg:1.0
# Steps to use
cd /poc/ffmpeg
./configure --cc=clang --cxx=clang++ --ld=clang --enable-debug --toolchain=clang-asan
make -j$(nproc)
make install

**注意**：The relevant version number ispocDisplay version removalgThe hash value afterward
