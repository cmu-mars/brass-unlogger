when run from a directory containing uncompressed copies of the data from
MIT/LL, `run.sh` will produce a CSV with one row per test described in the
logs and columns as given in `column-names.txt`. For example:

```
iev@bruce brass-unlogger % ls
column-names.txt randomTests      run.sh           waypoints.py
initialTests     readme.md        unlogger.py
iev@bruce brass-unlogger % ./run.sh
iev@bruce brass-unlogger % ls
column-names.txt randomTests      results.csv      unlogger.py
initialTests     readme.md        run.sh           waypoints.py
iev@bruce brass-unlogger %

```

`run.sh` is not meant to be especially robust, so it should really only be
used in this way. it's up to you to download and uncompress `initialTests`
and `randomTests` and put them in the right place; the `.gitignore` file
for this repo explicitly bans them from being committed because together
they are about 4.5 GB.

* `column-names.txt` gives the names of the columns in the order that
  they'll appear. to move columns around, just move the names in around in
  this file. these names can't contain any weird characters --
  specifically, if you replace all the ` `s with `_`s, they must be valid
  python function names.

* `unlogger.py` reads `column-names.txt` and calls the functions with the
  corresponding names given in file-order.

* to add a new column, add a name to `column-names.txt` in the place you'd
  like it to appear, and a function with the same name (modulo underscores
  for spaces) in python that defines what its values should be in terms of
  the variables in scope in the inner most loop where the call to
  `locals()` is made (those variables will all be in scope inside the
  function you define, as a consequence of the meaning of `locals()`)

* one caveat is that this means you cannot have any other variables
  anywhere in the python with names that are the same as column
  headers. for example, there is a column header "final x", so you cannot
  have a variable named `final_x` because it'll shadow the associated
  function.

* from the tarballs of logs we got, the directory structure of
  `initialTests` and `randomTests` isn't quite the same; `initialTests/*/`
  looks like `randomTests/`, with json files that share hashes in their
  names with directories. this is reflected in the slightly odd structure
  of `run.sh`.

* there is a slight security risk here, in that names in the colums file
  are being used to look up into the locals dictionary. this shouldn't be a
  problem because this is not world facing: just don't adversarially name
  columns things like `Robert'); DROP TABLE Students; --`.

Once the `results.csv` file is made, `make_maps.py` can process it to
create a visualization for each test run. Currently, this means a copy of
the base map with the start, target, final, and obstacle locations marked
for each row in the `csv` in a PNG named with the test hash number in a
directory called `images/`. That directory must not exist when you run
`make_maps.py`. It takes about a half a second to run for each, so this
will be fairly lengthy for the whole results file.

Many thanks to [Tom7](https://www.cs.cmu.edu/~tom7/) for making his font
"Hockey is Lif" available for free use on
[http://fonts.tom7.com/fonts98.html].
