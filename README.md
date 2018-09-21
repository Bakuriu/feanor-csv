# Feanor CSV

Feanor is an artisan of CSV files. It can generate complex CSV files or file bundles for examples and tests.

**Note:** Feanor is currently in development. All releases prior to `1.0.0` should be considered alpha releases
and both the command line interface and the library API might change significantly between releases.
Release `1.0.0` will provide a stable API and stable command line interface for the `1.x` series.


## Usage

```
$ feanor --help
usage: feanor [-h] [--no-header] [-L LIBRARY] [-C GLOBAL_CONFIGURATION]
              [-r RANDOM_MODULE] [-s RANDOM_SEED] [--version]
              (-n N | -b N | --stream-mode STREAM_MODE)
              {expr,cmdline} ...

optional arguments:
  -h, --help            show this help message and exit
  --no-header           Do not add header to the output.
  -L LIBRARY, --library LIBRARY
                        The library to use.
  -C GLOBAL_CONFIGURATION, --global-configuration GLOBAL_CONFIGURATION
                        The global configuration for arbitraries.
  -r RANDOM_MODULE, --random-module RANDOM_MODULE
                        The random module to be used to generate random data.
  -s RANDOM_SEED, --random-seed RANDOM_SEED
                        The random seed to use for this run.
  --version             show program's version number and exit
  -n N, --num-rows N    The number of rows of the produced CSV
  -b N, --num-bytes N   The approximate number of bytes of the produced CSV
  --stream-mode STREAM_MODE

Schema definition:
  {expr,cmdline}        Commands to define a CSV schema.
```

Checking the version:

```
$ feanor --version
feanor 0.5.0
```

## Arbitrary types

Each arbitrary is assigned an "arbitrary type", which describes how to generate the values.
The syntax of the arbitrary type is the following:

    # <ARBITRARY_NAME> [ CONFIG ]

Where `ARBITRARY_NAME` must match `\w+` and `CONFIG` is a python `dict` literal.

For example the built-in `int` arbitrary type can be used in the following ways:

 - `%int` or `%int{}`: default configuration
 - `%int{"min": 10}`: do not generate numbers smaller than `10` (inclusive).
 - `%int{"max": 10}`: do not generate numbers bigger than `10` (inclusive).
 - `%int{"min": 10, "max":1000}`: generate numbers between `10` and `1000` (both inclusive).


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

For example `%int + %float` is an expression that evaluates to the sum of a random integer and a random float.


## Examples

**NOTE:** the following examples all specify the option `-s 0`. This is used solely for reproducibility reason.
The common use cases for Feanor do not need to specify a random seed and in fact doing so often defeats the purpose of the tool.

### Using the `cmdline` subcommand

Generate 10 rows with random integers:

```
$ feanor -s 0 -n 10 cmdline -c a '%int' -c b '%int'
a,b
885440,403958
794772,933488
441001,42450
271493,536110
509532,424604
962838,821872
870163,318046
499748,375441
611720,934973
952225,229053
```

Generate about 1 kilobyte of rows with 2 random integers in them and write result to `/tmp/out.csv`:

```
$ feanor -s 0 -b 1024 cmdline -c a '%int' -c b '%int'  /tmp/out.csv
$ head /tmp/out.csv 
a,b
885440,403958
794772,933488
441001,42450
271493,536110
509532,424604
962838,821872
870163,318046
499748,375441
611720,934973
```



Generate 10 rows with random integers, the first column between `0` and `10`, the second column between `0` and `1000`:

```
$ feanor -s 0 -n 10 cmdline -c a '%int{"min":0, "max":10}' -c b '%int{"min": 0, "max":1000}'
a,b
6,776
6,41
4,988
8,497
6,940
4,991
7,366
9,913
3,516
2,288
```

Generate 10 rows with random integers and their sum:

```
$ feanor -s 0 -n 10 cmdline -c a '%int' -c b '%int' -c c '@a+@b'
a,b,c
885440,403958,1289398
794772,933488,1728260
441001,42450,483451
271493,536110,807603
509532,424604,934136
962838,821872,1784710
870163,318046,1188209
499748,375441,875189
611720,934973,1546693
952225,229053,1181278
```

### Using the `expr` subcommand

Generate 10 rows with random integers:

```
$ feanor -s 0 -n 10 expr -c a,b '%int·%int'
a,b
885440,403958
794772,933488
441001,42450
271493,536110
509532,424604
962838,821872
870163,318046
499748,375441
611720,934973
952225,229053
```

Generate about 1 kilobyte of rows with 2 random integers in them and write result to `/tmp/out.csv`:

```
$ feanor -s 0 -b 1024 expr -c a,b /tmp/out.csv '%int·%int'
$ head /tmp/out.csv 
a,b
885440,403958
794772,933488
441001,42450
271493,536110
509532,424604
962838,821872
870163,318046
499748,375441
611720,934973
```



Generate 10 rows with random integers, the first column between `0` and `10`, the second column between `0` and `1000`:

```
$ feanor -s 0 -n 10 expr -c a,b '%int{"min":0, "max":10}·%int{"min": 0, "max":1000}'
a,b
6,776
6,41
4,988
8,497
6,940
4,991
7,366
9,913
3,516
2,288
```

Generate 10 rows with random integers and their sum:

```
$ feanor -s 0 -n 10 expr -c a,b,c '(%int)=a·(%int)=b·(@a+@b)'
a,b,c
885440,403958,1289398
794772,933488,1728260
441001,42450,483451
271493,536110,807603
509532,424604,934136
962838,821872,1784710
870163,318046,1188209
499748,375441,875189
611720,934973,1546693
952225,229053,1181278
```

or also:

```
$ feanor -s 0 -n 10 expr -c a,b,c 'let a:=%int b:=%int in @a·@b·(@a+@b)'
a,b,c
885440,403958,1289398
794772,933488,1728260
441001,42450,483451
271493,536110,807603
509532,424604,934136
962838,821872,1784710
870163,318046,1188209
499748,375441,875189
611720,934973,1546693
952225,229053,1181278
```