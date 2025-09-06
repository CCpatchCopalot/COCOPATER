FROM  ubuntu:20.04


WORKDIR /root/dev

RUN apt update && \
    apt install -y vim git wget build-essential \
    clang-11 clang-tools-11 clang-11-doc libclang-common-11-dev \
    libclang-11-dev libclang1-11 clang-format-11 clangd-11 && \
    apt autoremove -y && \
    apt autoclean -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-11 100
RUN update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-11 100

CMD ["/bin/bash"]