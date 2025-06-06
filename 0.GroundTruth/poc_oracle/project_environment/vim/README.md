# vim Source code compilation environment construction
# Construction process
```shell

apt-get update -y
apt-get install git -y

# Configure local SSH for Github and clone the Vim repository. (ssh-keygen)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat ~/.ssh/id_rsa.pub
# The output of the previous stepssh keyAdd togithub

git clone git@github.com:vim/vim.git

# add compiler
apt install gcc make clang libtool-bin build-essential llvm-dev libunwind-dev -y

```
# This environment has been uploaded todockerhub
image_id: meilabixiaoxin/poc-vim:1.0
# Steps to use