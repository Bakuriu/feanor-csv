# Feanor CSV

Feanor is an artisan of CSV files. It can generate complex CSV files or file bundles for examples and tests.

**Note:** Feanor is currently in development. All releases prior to `1.0.0` should be considered alpha releases
and both the command line interface and the library API might change significantly between releases.
Release `1.0.0` will provide a stable API and stable command line interface for the `1.x` series.


## Usage

```
$ feanor --help
usage: feanor [-h] -c NAME EXPR [-d NAME EXPR] [--no-header]
              (-n N | -b N | --stream-mode STREAM_MODE)
              [OUTPUT-FILE]

positional arguments:
  OUTPUT-FILE           The output file name.

optional arguments:
  -h, --help            show this help message and exit
  -c NAME EXPR, --column NAME EXPR
                        Add a column with the given name.
  -d NAME EXPR, --define NAME EXPR
                        Define a Feanor expression with the given name and
                        type.
  --no-header           Do not add header to the output.
  -n N, --num-rows N    The number of rows of the produced CSV
  -b N, --num-bytes N   The approximate number of bytes of the produced CSV
  --stream-mode STREAM_MODE

```


## Arbitrary types

Each arbitrary is assigned an "arbitrary type", which describes how to generate the values.
The syntax of the arbitrary type is the following:

    # <ARBITRARY_NAME> [ CONFIG ]

Where `ARBITRARY_NAME` must match `\w+` and `CONFIG` is a python `dict` literal.

For example the built-in `int` arbitrary type can be used in the following ways:

 - `#int` or `#int{}`: default configuration
 - `#int{"lowerbound": 10}`: do not generate numbers smaller than `10` (inclusive).
 - `#int{"upperbound": 10}`: do not generate numbers bigger than `10` (inclusive).
 - `#int{"lowerbound": 10, "upperbound":1000}`: generate numbers between `10` and `1000` (both inclusive).


## Feanor DSL Expressions

Values are defined by a simple DSL that allows you to combine multiple arbitraries in different ways and they
allow to express complex logic for your data generation.

### Arbitrary definitions

An arbitrary definition is simply its type and follows the syntax `#<NAME>[CONFIG]` as explained before.


### Assignments

You can assign a name to a certain expression with the syntax `(<expr>)=<NAME>`.


### References

You can refer to the values of an expression to which you assigned a name by using the syntax `@<NAME>`.

### Concatenation

You can concatenate multiple values using the syntax `<expr_1> . <expr_2>` or `<expr_1> · <expr_2>`.

### Choice

You can define an expression that can randomly take a value by using the choice operator `|` using the
syntax `<expr_1> | <expr_2>`.

The value of such expression will take the value of `expr_1` for `50%` of the time and the value of `expr_2`
the other times. You can specify the chances with the syntax: `expr_1 <0.3|0.7> expr_2`.
In this case the expression will evaluate to `expr_1` only `30%` of the time and to `expr_2` the remaining `70%`
of the time. You may omit one of the two numbers, hence `expr_1 <0.3|> expr_2` is equivalent to the last
expression.

If the sum of the left and right weight add up to a value smaller than `1` then the remaining portion
is the chance of the value to be empty. For example `expr_1 <0.25|0.25> expr_2` defines
an expression that in `25%` of the time evaluates to `expr_1`, `25%` of the time evaluates to `expr_2`
and `50%` of the time evaluates to `None` (i.e. empty)

### Merge

You can define an expression that can merge values of two different expressions using the `+` operator.

For example `#int + #float` is an expression that evaluates to the sum of a random integer and a random float.


## Examples

Generate 10 rows with random integers:

```
$ feanor -c a '#int' -c b '#int' -n 10
a,b
560419,658031
655804,421309
167612,374010
749885,652208
769247,842866
99285,979394
985242,786600
291957,485927
390879,830346
528892,930577
```

Generate about 1 kilobyte of rows with 2 random integers in them and write result to `/tmp/out.csv`:

```
$ feanor -c a '#int' -c b '#int' -b 1024 /tmp/out.csv
$ ls -l /tmp/out.csv 
-rw-rw-r-- 1 user user 1027 ago  3 00:17 /tmp/out.csv
```



Generate 10 rows with random integers, the first column between `0` and `10`, the second column between `0` and `1000`:

```
$ feanor -c a '#int{"lowerbound":0,"upperbound":10}' -c b '#int{"lowerbound":0,"upperbound":1000}' -n 10
a,b
5,943
4,965
8,962
2,957
8,521
8,630
4,535
10,630
7,139
8,283
```

Generate 10 rows with random integers and their sum:

```
$ feanor -c a '#int' -c b '#int' -c c '@a+@b' -n 10
a,b,c
959911,805488,1765399
963573,781193,1744766
825514,327790,1153304
304667,455607,760274
529196,891481,1420677
100948,692883,793831
991054,975422,1966476
249764,741283,991047
141396,606592,747988
979772,929347,1909119
```