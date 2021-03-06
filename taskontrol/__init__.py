"""
A framework for developing behavioral experiments.

dispatcher
----------
.. automodule:: taskontrol.dispatcher
   :members:

paramgui
--------
.. automodule:: taskontrol.paramgui
   :members:

savedata
--------
.. automodule:: taskontrol.savedata
   :members:

smclient
--------
.. automodule:: taskontrol.smclient
   :members:

statematrix
-----------
.. automodule:: taskontrol.statematrix
   :members:

utils
-----
.. automodule:: taskontrol.utils
   :members:
"""

import os
import sys
import pathlib
import importlib.util

# -- Load taskontrol/settings/rigsettings.py file --
_packageDir = os.path.dirname(os.path.abspath(__file__))
_settingsDir = os.path.split(_packageDir)[0] # One directory above
_settingsBasename = 'rigsettings.py'
rigsettingPath = os.path.join(_settingsDir,'settings',_settingsBasename)
_spec = importlib.util.spec_from_file_location('taskontrol.rigsettings', rigsettingPath)
rigsettings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rigsettings)
