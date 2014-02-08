.. highlight:: python

Getting started with TASKontrol
===============================

This document explains how to run an simple paradigm.

* First, you need to install TASKontrol. See ???. Make sure the taskontrol directory in in the python path. TODO: How to verify?

* Open a text editor and copy the following code into a file called testparadigm.py:

.. code-block:: python
   :linenos:

    from taskontrol.plugins import templates

    class Paradigm(templates.Paradigm2AFC):
        def __init__(self,parent=None):
            super(Paradigm, self).__init__(parent,dummy=True)

    if __name__ == "__main__":
        (app,paradigm) = templates.create_app(Paradigm)
 
* The first line imports the module with paradigm templates. This module will in turn import all necessary modules from PySide (QtCore and QtGui) and taskontrol (rigsettings, statematrix, etc).
* Lines 3-5 create the class Paradigm(), where we will define all details of the task.
* Lines 7-8 create an instance of the class Paradigm(), set up our application, and open the main window.

* There are two ways to run your paradigm: (1) from the console, or (2) from ipython. To run from the console, simple type:
  python testparadigm.py


* State #0 (named 'ready_next_trial' by default) will be the last state of each trial. When reached, the state machine will yield control to the program running the user interface to prepare the next trial. Once done, the method dispatcher.ready_to_start_trial() will trigger a jump to State #1 to get the trial started (and give control back to the state machine).


