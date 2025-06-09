# Construction process
```shell

docker build -t poc-radare2-u20 .
docker run -itd --network host --name poc-radare2 poc-radare2-u20 /bin/bash

apt-get install libboost-all-dev

export CC=clang-11
export CXX=clang++-11

export PassPluginDir=$PWD
clang++-11 `llvm-config-11 --cxxflags` -fPIC -shared -o $PassPluginDir/FunctionDynamicPluginPass.so $PassPluginDir/FunctionDynamicPluginPass.cpp `llvm-config-11 --ldflags --system-libs --libs all`
clang++-11 `llvm-config-11 --cxxflags` -fPIC -shared -o $PassPluginDir/BBDynamicPluginPass.so $PassPluginDir/BBDynamicPluginPa
ss.cpp `llvm-config-11 --ldflags --system-libs --libs all`
clang++-11 `llvm-config-11 --cxxflags` -fPIC -shared -o $PassPluginDir/InstructionDynamicPluginPass.so $PassPluginDir/InstructionDynamicPluginPass.cpp `llvm-config-11 --ldflags --system-libs --libs all`
clang++-11 -fPIC -shared $PassPluginDir/savepath.cpp -o $PassPluginDir/libsavepath.so -lboost_system -lboost_filesystem
# ln -s $PassPluginDir/libsavepath.so /usr/lib/libsavepath.so 


export CXXFLAGS="-g -fplugin=$PassPluginDir/FunctionDynamicPluginPass.so -fsanitize=address"
# BBlevel
export CXXFLAGS="-g -fplugin=$PassPluginDir/BBDynamicPluginPass.so -fsanitize=address"
# Command level
export CXXFLAGS="-g -fplugin=$PassPluginDir/InstructionDynamicPluginPass.so -fsanitize=address"
export CFLAGS=$CXXFLAGS
export LDFLAGS="-L$PassPluginDir -lsavepath  -fsanitize=address"
CFGARG=" --enable-shared=no " PREFIX=`realpath install` bash sys/build.sh --with-capstone4

# No stakes
export CXXFLAGS="-g -fsanitize=address"
export CFLAGS=$CXXFLAGS
export LDFLAGS="-fsanitize=address"
CFGARG=" --enable-shared=no " PREFIX=`realpath install` bash sys/build.sh --with-capstone4

export ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:symbolize=0:allocator_may_return_null=1:detect_odr_violation=0
# existradare2Run in the directory
LIBR_PATHS=$(find $(pwd)/libr -maxdepth 1 -type d)
export LD_LIBRARY_PATH=$PassPluginDir:$(echo $LIBR_PATHS | tr ' ' ':')
cd binr/radare2
./radare2 -A -q seed1



```