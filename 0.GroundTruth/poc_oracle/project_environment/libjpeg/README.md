# libjpeg Source code compilation environment construction

# Construction process
```shell

docker build -t poc-libjpeg .
docker run -itd --name poc-libjpeg poc-libjpeg
docker exec -it poc-libjpeg /bin/bash
apt update -y
apt install git zip wget -y


git clone https://github.com/thorfdbg/libjpeg.git

# add compiler
apt-get install build-essential clang make autoconf automake

```

# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-libjpeg:1.0

# Steps to use
1. git reset designate version
2. export FLAGS='-g -fPIC -fsanitize=address' && CC="clang $FLAGS" CXX="clang++ $FLAGS" ./configure && make -j
3. make -j$(nproc)
4. ./jpeg -p @@ /dev/null
# example
