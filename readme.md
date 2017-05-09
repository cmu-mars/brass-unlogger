* `header.csv` gives the names of the columns in the order that they'll
  appear. to move columns around, just move the names in around in this
  file. these names can't contain any weird characters -- specifically, if
  you replace all the ` `s with `_`s, they must be valid python function
  names.

* `unlogger.py` reads `header.csv` and calls the functions in `columns.py`
  with the names given in the order given. so to add a new column, add a
  name to `header.csv` in the place you'd like it to appear, and a function
  with the same name (modulo underscores for spaces) in `columns.py`.

* one caveat is that this means you cannot have any other variables
  anywhere in the python with names that are the same as column
  headers. For example there is a column header "final x", so you cannot
  have a variable named `final_x` because it'll shadow the associated
  function in `columns.py`.

* from the tarballs of logs we got, the directory structure of
  `initialTests` and `randomTests` isn't quite the same; `initialTests/*/`
  looks like `randomTests/`, with json files that share hashes in their
  names with directories. this is reflected in the slightly odd structure
  of `run.sh`.
