FROM ubuntu
ENV POC_PATH /poc

# Create and set the working directory
WORKDIR $POC_PATH


RUN apt-get update -y && rm -rf /var/lib/apt/lists/*


RUN apt-get update -y && \
    apt-get install -y git wget && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update -y && \
    apt-get install -y clang build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update -y && \
    apt-get install -y bison flex libgmp-dev libmpc-dev libmpfr-dev && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update -y && \
    apt-get install -y texinfo libz-dev libisl-dev libc++-dev libc++abi-dev libasan6 && \
    rm -rf /var/lib/apt/lists/*

# Clone the repository as a separate layer
RUN git clone git://sourceware.org/git/binutils-gdb.git
