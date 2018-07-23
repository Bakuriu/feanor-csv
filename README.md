# Feanor CSV

Feanor is an artisan of CSV files. It can generate complex CSV files or file bundles for examples and tests.

**Note:** Feanor is currently in development. All releases prior to `1.0.0` should be considered alpha releases
and both the command line interface and the library API might change significantly between releases.
Release `1.0.0` will provide a stable API and stable command line interface for the `1.x` series.


## Usage

```
$ feanor --help
usage: feanor [-h] -c NAME [-a NAME TYPE] [-t NAME INPUTS OUTPUTS EXPR]
              [--no-header] (-n N | -b N | --stream-mode STREAM_MODE)
              [OUTPUT-FILE]

positional arguments:
  OUTPUT-FILE           The output file name.

optional arguments:
  -h, --help            show this help message and exit
  -c NAME, --column NAME
                        Add a column with the given name.
  -a NAME TYPE, --arbitrary NAME TYPE
                        Add an arbitrary with the given name and type.
  -t NAME INPUTS OUTPUTS EXPR, --transformer NAME INPUTS OUTPUTS EXPR
                        Add a transformer with the given name, inputs, outputs
                        and expression.
  --no-header           Do not add header to the output.
  -n N, --num-rows N    The number of rows of the produced CSV
  -b N, --num-bytes N   The approximate number of bytes of the produced CSV
  --stream-mode STREAM_MODE

```


## Arbitrary types

Each arbitrary is assigned an "arbitrary type", which describes how to generate the values of that column.
The syntax of the arbitrary type is the following:

    <ARBITRARY_NAME> [ CONFIG ]

Where `ARBITRARY_NAME` must match `\w+` and `CONFIG` is a python `dict` literal.

For example the built-in `int` arbitrary type can be used in the following ways:

 - `int` or `int{}`: default configuration
 - `int{"lowerbound": 10}`: do not generate numbers smaller than `10` (inclusive).
 - `int{"upperbound": 10}`: do not generate numbers bigger than `10` (inclusive).
 - `int{"lowerbound": 10, "upperbound":1000}`: generate numbers between `10` and `1000` (both inclusive).


## Transformer definitions

Transformers allow to express complex logic for data generation. They allow you to fill a column only `10%` of the time,
or to fill a column with the sum of two other columns in the same row.

A transformer is defined by the `-t/--transformer` option:

```
--transformer NAME INPUTS OUTPUTS EXPR
```

The `NAME` is needed to identify one transformer. You can have multiple transformers with the same `INPUTS`, `OUTPUTS`
and `EXPR`, but not with the same name.

The `INPUTS` is a comma-delimited list of defined names. The `OUTPUTS` is a comma-delimited list of names that
this transformer defines. `EXPR` is a python expression that should return a tuple or a single value.

A transformer is applied to the values it receives from its `INPUTS` (which might be arbitraries defined with `--arbitrary`,
or names found in `OUTPUTS` of other transformers), by evaluating the Python expression `EXPR`.
The scope in which `EXPR` is evaluated contains the references to `INPUTS` values and the `random` module.

The value returned by `EXPR` should be a tuple with the same size of the `OUTPUTS` (or might be a plain value if there is only
one output value).

After evaluation the current scope is updated with the newly defined values.

Transformers are applied in the order in which they are defined, and a transformer can overwrite an existing value.


## Examples

Generate 10 rows with random integers:

```
$ feanor -c a -c b --arbitrary a int --arbitrary b int -n 10
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
$ feanor -c a -c b --arbitrary a int --arbitrary b int -b 1024 /tmp/out.csv
$ ls -l /tmp/out.csv
-rw-rw-r-- 1 user user 1038 lug 13 20:48 /tmp/out.csv
```



Generate 10 rows with random integers, the first column between `0` and `10`, the second column between `0` and `1000`:

```
$ feanor -c a -c b --arbitrary a 'int{"lowerbound":0,"upperbound":10}' --arbitrary b 'int{"lowerbound":0,"upperbound":1000}' -n 10
a,b
2,883
5,244
8,959
3,248
10,275
0,827
3,245
5,345
0,396
6,137
```

Generate 10 rows with random integers and their sum:

```
$ feanor -c a -c b -c c --arbitrary a 'int' --arbitrary b 'int' -t sum a,b c 'a+b' -n 10
a,b,c
469985,425117,895102
563866,161162,725028
672940,845418,1518358
87775,16432,104207
332363,237117,569480
18358,250279,268637
808188,560466,1368654
881993,905116,1787109
322832,707592,1030424
876583,256120,1132703
```