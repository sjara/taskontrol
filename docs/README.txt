
To compile documentation:
-------------------------

- Make sure you have Sphinx (package python-sphinx) installed.
  When installing, say 'yes' to autodoc.
- .../doc/ and run: make html
- Open in browser: .../doc/_build/html/index.html

NOTE:
- You may need to install additional Sphinx extensions like:
  sphinxcontrib.napoleon 
  (I don't know if there is an Ubuntu package, so use pip)


To build in ReadTheDocs:
------------------------
I believe it's done automatically from GitHub, but if you login to
https://readthedocs.org/projects/taskontrol/
You will see button too.

