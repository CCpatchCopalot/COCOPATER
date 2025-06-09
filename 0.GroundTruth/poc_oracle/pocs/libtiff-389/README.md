# Heap Buffer Overflow in reverseSamples24bits (libtiff)

## POC URL
https://gitlab.com/libtiff/libtiff/-/issues/389

## Compilation Environment
- **Operating System**: Ubuntu 20.04.3 LTS
- **Kernel Version**: 5.13.0-28-generic
- **Compiler**: GCC 9.3.0
- **libtiff Version**: 4.3.0
- **Build Configuration**:
  ```
  CC=gcc CXX=g++ CFLAGS="-ggdb -fsanitize=address,undefined -fno-sanitize-recover=all" CXXFLAGS="-ggdb -fsanitize=address,undefined -fno-sanitize-recover=all" LDFLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -lm" ./configure --disable-shared
  ```

## Run Command
```
./tiffcrop -i -E t -Z 0:0,1:1 -e c -F both poc.tif out.tif
```

## Expected Output
When running the command with a specially crafted TIFF file (`poc.tif`), the application will crash due to a heap buffer overflow in the `reverseSamples24bits` function at `tiffcrop.c:8899`. The AddressSanitizer will report a heap-buffer-overflow error similar to:

```
=================================================================
==22023==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x616000000581 at pc 0x5649e5d9f948 bp 0x7fffc3d935c0 sp 0x7fffc3d935b0
READ of size 4 at 0x616000000581 thread T0
    #0 0x5649e5d9f947 in reverseSamples24bits /home/targets/libtiff/tools/tiffcrop.c:8899
    #1 0x5649e5dab441 in mirrorImage /home/targets/libtiff/tools/tiffcrop.c:9172
    #2 0x5649e5dc253b in processCropSelections /home/targets/libtiff/tools/tiffcrop.c:7526
    #3 0x5649e5d95472 in main /home/targets/libtiff/tools/tiffcrop.c:2396
    #4 0x7f4db90530b2 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x270b2)
    #5 0x5649e5d9e4ed in _start (/home/targets/libtiff/tools/tiffcrop+0x324ed)

0x616000000584 is located 0 bytes to the right of 516-byte region [0x616000000380,0x616000000584)
allocated by thread T0 here:
    #0 0x7f4db9496bc8 in malloc (/lib/x86_64-linux-gnu/libasan.so.5+0x10dbc8)
    #1 0x5649e5dc1e2e in processCropSelections /home/targets/libtiff/tools/tiffcrop.c:7455

SUMMARY: AddressSanitizer: heap-buffer-overflow /home/targets/libtiff/tools/tiffcrop.c:8899 in reverseSamples24bits
==22023==ABORTING
```

This demonstrates a heap buffer overflow vulnerability in libtiff's tiffcrop utility when processing specially crafted TIFF images.