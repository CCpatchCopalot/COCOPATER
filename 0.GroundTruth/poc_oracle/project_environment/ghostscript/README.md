# gpac Source code compilation environment construction

# Construction process
```shell
docker build -t poc-ghostscript .
docker run -itd --name poc-ghostscript poc-ghostscript
docker exec -it poc-ghostscript /bin/bash

# Preparing the initial environment
apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the repository. (ssh-keygen)
cd /poc
git clone 	git://git.ghostscript.com/ghostpdl.git

```

# Steps to use
```shell
cd ghostpdl
apt install autoconf autoconf automake
autoreconf -f -i
./autogen.sh
./configure CC=clang CXX=clang++ LD=clang CFLAGS="-fsanitize=address" CXXFLAGS="-fsanitize=address" LDFLAGS="-fsanitize=address"
make sanitize -j$(nproc)
make install
