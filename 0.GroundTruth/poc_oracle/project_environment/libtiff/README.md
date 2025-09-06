# libtiff Source code compilation environment construction

# Construction process
```shell

docker build -t poc-libtiff .
docker run -itd --name poc-libtiff poc-libtiff
docker exec -it poc-libtiff /bin/bash
apt update -y
apt install git zip wget -y
apt install clang cmake autoconf automake libtool pkg-config
# The output of the previous stepssh keyAdd togithub

git clone https://gitlab.com/libtiff/libtiff.git

# add compiler

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-libtiff:1.0

# Steps to use
1. git reset designate version
2. sh ./autogen.sh
3. CC="clang" CXX="clang++"  CFLAGS="-g -fsanitize=address -fno-omit-frame-pointer" CXXFLAGS="-g -fsanitize=address -fno-omit-frame-pointer" ./configure --prefix=$PWD/build_asan --disable-shared
4. make CFLAGS="-g -fsanitize=address -fno-omit-frame-pointer" CXXFLAGS="-g -fsanitize=address -fno-omit-frame-pointer"
5. make install
6. ./build_asan/bin/tiffcrop -E right  -z 1,1,2048,2048:1,2049,2048,4097 -i -s poc /tmp/foo

CVE-2023-0804
