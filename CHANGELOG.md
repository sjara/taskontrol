# v1.0 (2020-12-29)

In addition to listing the changes, we write some hints for what to check in your paradigm so it works with this new version.

* Transitioned completely to Python 3.
  * Check your paradigms for `print` statements. They should be functions.
* Use qtpy instead of PySide.
  * Use `qtpy.QWidgets` instead of `PySide.QtGui`.
* Moved all modules from taskontrol.core to taskontrol.
  * Change imports of core modules to something like: `from taskontrol import dispatcher`
* Method `paramgui.update_history()` now requires parameter "`lastTrial`", which is used to verify that the history is of the correct length.
* Method `paramgui.center_in_screen()` is now `paramgui.center_on_screen()`.
* Class `arraycontainer.Container` is now `utils.EnumContainer`.
* Module `messenger.py` has been deleted.
  * Class `messenger.Messenger` is now `paramgui.Messenger`.
  * Method `messenger.Messenger_stringlist()` is now `messenger.Messenger_get_list()`.
* Class `dispatcher.DispatcherGUI` doesn't have to be called explicitly. An instance is now created as an attribute of `dispatcher.Dispatcher` (under the name `dispatcher.Dispatcher.widget`).

# v0.2 (2017)
* Extratimers work on Arduino and emulator.

# v0.1 (2013)
* Initial version (written for Python 2.x).
