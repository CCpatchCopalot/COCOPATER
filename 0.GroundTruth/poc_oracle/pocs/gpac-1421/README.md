## POC URL
https://github.com/gpac/gpac/issues/1421

## Compilation Environment
- Ubuntu 18.04.6 LTS, X64
- gcc version 7.4.0
- gpac (latest master 4a7a63)

## Run Command
```
wget https://www.mediafire.com/file/crsh1.zip/file -O crsh1.zip
unzip crsh1.zip
./MP4Box -dash 1000 crsh1
```

## Compile Command:
$ CC="gcc -fsanitize=address -g" CXX="g++ -fsanitize=address -g" ./configure --static-mp4box
$ make

## Run Command:
./MP4Box -dash 1000 crsh1

## ASAN info:

=================================================================
==9568==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000491 at pc 0x55a56f2ac689 bp 0x7fff440c4d00 sp 0x7fff440c4cf0
READ of size 1 at 0x602000000491 thread T0
    #0 0x55a56f2ac688 in gf_m2ts_process_pmt media_tools/mpegts.c:2163
    #1 0x55a56f29e975 in gf_m2ts_section_complete media_tools/mpegts.c:1610
    #2 0x55a56f29f3ab in gf_m2ts_gather_section media_tools/mpegts.c:1740
    #3 0x55a56f2a519e in gf_m2ts_process_packet media_tools/mpegts.c:3446
    #4 0x55a56f2a519e in gf_m2ts_process_data media_tools/mpegts.c:3507
    #5 0x55a56f2b4886 in gf_m2ts_probe_file media_tools/mpegts.c:4641
    #6 0x55a56f1dc7f0 in gf_dash_segmenter_probe_input media_tools/dash_segmenter.c:5505
    #7 0x55a56f20350a in gf_dasher_add_input media_tools/dash_segmenter.c:6669
    #8 0x55a56eddea6f in mp4boxMain /home/dr3dd/fuzzing/gpac/applications/mp4box/main.c:4704
    #9 0x7f56187cfb96 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x21b96)
    #10 0x55a56edcd7a9 in _start (/home/dr3dd/fuzzing/gpac/bin/gcc/MP4Box+0x1657a9)

0x602000000491 is located 0 bytes to the right of 1-byte region [0x602000000490,0x602000000491)
allocated by thread T0 here:
    #0 0x7f5619457b50 in __interceptor_malloc (/usr/lib/x86_64-linux-gnu/libasan.so.4+0xdeb50)
    #1 0x55a56f29dfb5 in gf_m2ts_section_complete media_tools/mpegts.c:1550
    #2 0x55a56f664196  (/home/dr3dd/fuzzing/gpac/bin/gcc/MP4Box+0x9fc196)

SUMMARY: AddressSanitizer: heap-buffer-overflow media_tools/mpegts.c:2163 in gf_m2ts_process_pmt
Shadow bytes around the buggy address:
  0x0c047fff8040: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8050: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8060: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8070: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8080: fa fa 00 00 fa fa 03 fa fa fa 00 00 fa fa 00 00
=>0x0c047fff8090: fa fa[01]fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80a0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80b0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80c0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80d0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80e0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07 
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
==9568==ABORTING
## gdb Info:

Program received signal SIGSEGV, Segmentation fault.
0x0000555555d47488 in gf_m2ts_process_pmt (ts=<optimized out>, pmt=<optimized out>, sections=<optimized out>, table_id=<optimized out>, ex_table_id=<optimized out>, 
    version_number=<optimized out>, last_section_number=<optimized out>, status=<optimized out>) at media_tools/mpegts.c:2541
2541			if (es->stream_type == GF_M2TS_VIDEO_HEVC) nb_hevc++;
(gdb) bt
#0  0x0000555555d47488 in gf_m2ts_process_pmt (ts=<optimized out>, pmt=<optimized out>, sections=<optimized out>, table_id=<optimized out>, ex_table_id=<optimized out>, 
    version_number=<optimized out>, last_section_number=<optimized out>, status=<optimized out>) at media_tools/mpegts.c:2541
#1  0x0000555555d35506 in gf_m2ts_section_complete (ts=ts@entry=0x5555562c5a40, sec=sec@entry=0x5555562d74a0, ses=ses@entry=0x5555562d73f0) at media_tools/mpegts.c:1610
#2  0x0000555555d3638a in gf_m2ts_gather_section (ts=ts@entry=0x5555562c5a40, sec=0x5555562d74a0, ses=ses@entry=0x5555562d73f0, data=0x7ffffffa680d "", 
    data@entry=0x7ffffffa67ef "", data_size=<optimized out>, hdr=<optimized out>, hdr=<optimized out>) at media_tools/mpegts.c:1740
#3  0x0000555555d3f3be in gf_m2ts_process_packet (data=0x7ffffffa67ef "", ts=0x5555562c5a40) at media_tools/mpegts.c:3446
#4  gf_m2ts_process_data (ts=ts@entry=0x5555562c5a40, data=data@entry=0x7ffffffa66e0 "\377\377\377\376zWCG@", data_size=<optimized out>) at media_tools/mpegts.c:3507
#5  0x0000555555d54ca1 in gf_m2ts_probe_file (fileName=<optimized out>) at media_tools/mpegts.c:4641
#6  0x0000555555bf0844 in gf_dash_segmenter_probe_input (io_dash_inputs=io_dash_inputs@entry=0x5555562c4978, nb_dash_inputs=nb_dash_inputs@entry=0x5555562c4980, 
    idx=idx@entry=0) at media_tools/dash_segmenter.c:5505
#7  0x0000555555c2dabb in gf_dasher_add_input (dasher=0x5555562c4970, input=<optimized out>) at media_tools/dash_segmenter.c:6669
#8  0x00005555555c88f5 in mp4boxMain (argc=<optimized out>, argv=<optimized out>) at main.c:4704
#9  0x00007ffff722bb97 in __libc_start_main () from /lib/x86_64-linux-gnu/libc.so.6
#10 0x00005555555a3e0a in _start () at main.c:5985
(gdb)