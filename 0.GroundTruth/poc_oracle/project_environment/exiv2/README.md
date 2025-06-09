

# Construction process
```shell
docker build -t poc-exiv2 .
docker run -itd --name poc-exiv2 poc-exiv2
docker exec -it poc-exiv2 /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone https://github.com/Exiv2/exiv2.git
apt install --yes build-essential ccache clang cmake git google-mock libbrotli-dev libcurl4-openssl-dev libexpat1-dev libgtest-dev libinih-dev libssh-dev libxml2-utils libz-dev python3 zlib1g-dev autoconf
# Need to install inih
cd ..
git clone https://github.com/benhoyt/inih.git
cd inih
apt install meson ninja-build
meson setup build
meson compile -C build
sudo meson install -C build
```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-exiv2:1.0
# Steps to use
### New version
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
export CXXFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
export LDFLAGS="-fsanitize=address"
cmake -S . -B build -DCMAKE_BUILD_TYPE=debugfull -DEXIV2_TEAM_USE_SANITIZERS=ON \
cmake --build build \
ctest --test-dir build --verbose -fno-omit-frame-pointer" ..  # RUN tests
### Old version
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
export CXXFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
export LDFLAGS="-fsanitize=address"
make config
./configure
make
# example 
CVE-2017-14858
CVE-2017-14859