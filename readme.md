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
