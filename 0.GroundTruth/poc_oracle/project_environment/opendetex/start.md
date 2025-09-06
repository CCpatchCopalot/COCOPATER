To build the program, you need:
* 'make' program
* a C compiler (for example, Clang or GCC)
* 'lex' implementation (for example, flex)

sudo apt-get install make gcc flex


CVE-2019-19601
Rewind version
git checkout v2.8.5

existmakefileAdd at the end of the file：
CFLAGS += -fsanitize=address -g
CXXFLAGS += -fsanitize=address -g

make
sudo make install

CVE-2021-27548
