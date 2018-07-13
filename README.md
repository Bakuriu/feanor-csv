# Feanor CSV

Feanor is an artisan of CSV files. It can generate complex CSV files or file bundles for examples and tests.


## Usage

```
$ feanor --help
usage: feanor [-h] [-c NAME TYPE] [--no-header]
              (-n N | -b N | --stream-mode STREAM_MODE)
              [OUTPUT-FILE]

positional arguments:
  OUTPUT-FILE           The output file name.

optional arguments:
  -h, --help            show this help message and exit
  -c NAME TYPE, --column NAME TYPE
                        Add a column with the given type.
  --no-header           Do not add header to the output.
  -n N, --num-rows N    The number of rows of the produced CSV
  -b N, --num-bytes N   The approximate number of bytes of the produced CSV
  --stream-mode STREAM_MODE
```


## Examples

Generate 10 rows with random integers:

```
$ feanor -c a int -c b int -n 10
a,b
609270,269960
644115,544953
380617,867613
7235,822990
571,67928
577245,893342
947965,384183
158251,910056
664935,511383
817864,59221
```

Generate about 1 kilobyte of rows with 3 random integers in them and write result to `/tmp/out.csv`:

```
$ feanor -c a int -c b int -c c int -b 1024 /tmp/out.csv
$ ls -l /tmp/out.csv
-rw-rw-r-- 1 user user 1038 lug 13 20:48 /tmp/out.csv
```