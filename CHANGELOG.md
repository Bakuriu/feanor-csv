0.5.0 - 2018/09/21
==================

 * Bugfixes. Including:
    - CSV files now always use comma as separator
    - `date` producer now correctly generates dates in ranges
 * Added `--library`, allowing the user to use custom producers in place of built-in ones.
 * Added the ability to provide a `--global-configuration` to avoid configuration repetition.
 * Changed type introducer token from `#` to `%`. This makes it easier to write expressions on the command line.
 * Can specify the `--random-module` to use. It should provide an interface similar to the `random` module but this
    allows to provide a cryptographically strong PRNG if needed.
 * Can specify the `--random-seed`. This allows for reproducibility. Useful in tests mainly.
 * Test coverage is now 100%.



0.4.0 - 2018/08/29
==================

 * Bugfixes
 * Added more built-in arbitraries:
   - `float`
   - `date`
   - `string`
   - `alpha`
   - `alnum`
   - `fixed`
   - `cycle`   
 
 * Added the concept of type compatibility
 * Added pytest for testing and coverage reports

0.3.2 - 2018/08/10
==================

 * Can define the CSV file using a single expression.
 * Changed cmdline interface to use subcommands.


0.3.1 - 2018/08/03
==================

 * Changed interface to use an expression language to define columns instead
    of using something like explicit arbitraries+columns+transformers.
 * Old library interface is still there, but the command line has changed


0.2.1 - 2018/07/23
==================

 * added transformers as a way to combine values
   - allows to define columns that are equal to other columns
   - can produce non integer values by using transformers

0.1.0 - 2018/07/13
==================

Initial version.

This version provides extremely basic functionality. It can only generate random integers.