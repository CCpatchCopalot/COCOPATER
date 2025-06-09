# libredwg Source code compilation environment construction

# Construction process
```shell

docker build -t poc-libredwg .
docker run -itd --name poc-libredwg poc-libredwg
docker exec -it poc-libredwg /bin/bash
apt update -y
apt install git zip wget -y

# Configure local SSH for Github and clone the Vim repository. (ssh-keygen)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat ~/.ssh/id_rsa.pub
# The output of the previous stepssh keyAdd togithub

git clone git@github.com:LibreDWG/libredwg.git

# add compiler
apt install build-essential make automake clang autoconf libtool pkg-config libiconv-hook-dev libbz2-dev libtool-bin texinfo -y
export LD_LIBRARY_PATH=/usr/local/lib:/poc/libredwg/src/.libs:$LD_LIBRARY_PATH
source ~/.bashrc

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-libredwg:1.0

# Steps to use
1. git clean -xdf
2. sh ./autogen.sh (if you checked out the source code from git)
3. CFLAGS="-O0 -g -fsanitize=address" LDFLAGS="-fsanitize=address" ./configure
4. make -j$(nproc) V=s
5. make install
6. dxf2dwg /poc/testcase -o /dev/null
# example
CVE-2023-36274
