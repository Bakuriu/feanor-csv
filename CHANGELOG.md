0.6.0 - NOT RELEASED YET
========================

 * Bugfixes:
 
    | Issue Number     | Fix description                                              |
    |------------------|--------------------------------------------------------------|
    | [issue #26][#26] | Correct error message is raised when the number of produced<br> values is incorrect. | 
    | [issue #29][#29] | The parsing rule for "call" was in the wrong place.          |
 * Added support for function calls and added the built-in `fmt` function that can be used to
   format values. See [issue #27][#27]
 * It is now possible to use constants in expressions such as `%int + 5`. A constant creates a
   `fixed` producer with the given value. See [issue #28][#28]
 * Added support for providing constants in libraries. It was not complete before.
 * Added support for type aliases. It is now possible to define custom types using the
   `-D` or `--define` command line argument. For example:
   
   ```
   $ feanor -D "perc := %float{'min': 0, 'max': 100}" expr "%perc · %int"
   ```
   
   See [issue #25][#25].

[#25]: https://github.com/Bakuriu/feanor-csv/issues/25
[#26]: https://github.com/Bakuriu/feanor-csv/issues/26
[#27]: https://github.com/Bakuriu/feanor-csv/issues/27
[#28]: https://github.com/Bakuriu/feanor-csv/issues/28
[#29]: https://github.com/Bakuriu/feanor-csv/issues/29

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