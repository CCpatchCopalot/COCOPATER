# 使用 Ubuntu 18.04 作为基础镜像
FROM ubuntu:18.04

ENV POC_PATH /poc

# 更新并安装必要的工具和 Clang 6.0
RUN apt-get update && \
    apt-get install -y software-properties-common wget && \
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    apt-add-repository "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-6.0 main" && \
    apt-get update && \
    apt-get install -y clang-6.0 && \
    rm -rf /var/lib/apt/lists/*

# 设置 clang-6.0 为默认的 clang 版本
RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-6.0 60 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-6.0 60

# 显示 Clang 版本
CMD ["clang", "--version"]

# Create a `poc` folder inside the container
RUN mkdir -p $POC_PATH

WORKDIR $POC_PATH
