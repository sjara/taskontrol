.. highlight:: python

Getting started with TASKontrol
===============================

To define an experiment with TASKontrol, you create a *paradigm*. Within a paradigm, you define all the parameters that describe the behavioral task, as well as the graphical user interface to enable starting and stopping the session.

This document explains how to run a simple paradigm using TASKontrol. We will start by running paradigms using the emulator before we try connecting to external interfaces (like an Arduino).

1. First, you need to `download and install TASKontrol`_.
2. Make sure that in your ``settings/rigsettings.py`` file, you have set ``STATE_MACHINE_TYPE = 'emulator'``.
3. Open your favorite editor and save the following Python code into a file (any folder would work). Let's assume you called the file ``testparadigm.py``.

.. code-block:: python
    :linenos:

    from taskontrol.plugins import templates

    class Paradigm(templates.ParadigmMinimal):
        def __init__(self, parent=None):
            super().__init__(parent)

    if __name__ == "__main__":
        (app, paradigm) = templates.paramgui.create_app(Paradigm)

4. In a terminal, go to the folder where you saved the file, and open the paradigm by running the command: ``python testparadigm.py``




Interacting with the paradigm
-----------------------------

.. image:: images/emulator.png
   :scale: 50 %
   :alt: Example of a graphical interface
   :align: right

.. image:: images/testparadigm001.png
   :scale: 50 %
   :alt: Example of a graphical interface
   :align: right


* The command above should open two windows: one with a big "**Start**" button, and one emulator window with multiple buttons.
* When you press the "**Start**" button, the paradigm will run and you will see the time counter increase.
* Pressing buttons in the emulator window will make the "Events" counter in the paradigm window increase, but nothing else should happen.

What is the code doing?
-----------------------

* **Line 1** imports a module that contains paradigm templates. This module will in turn import all necessary modules from Qt (for the graphical interface) and taskontrol (rigsettings, dispatcher, etc).
* **Line 3** is where we define the class for our paradigm, which we call ``Paradigm``. In this example, our class is a subclass of the simplest template called ``ParadigmMinimal``. To see what is being inherited, look at `plugins/templates.py`_.
* **Line 4-5** are part of the constructor of the class. These lines should appear in any paradigm we create based on a template.
* **Line 7** is a standard Python way of checking if the file is run directly (as opposed to being imported as a module by another file).
* **Line 8** will call the ``create_app()`` method, which will return:

  * An instance of the ``QtGui.QApplication`` class (the main class for running Qt applications).
  * An instance of our ``Paradigm`` class (which gives us access to everything inside our paradigm).


..
 * Line 1 imports a module that contains paradigm templates. This module will in turn import all necessary modules from PySide (QtCore and QtGui) and taskontrol (rigsettings, statematrix, etc).
 * Lines 3-5 create the class Paradigm(), where we will define all details of the task.
 * Lines 7-8 create an instance of the class Paradigm(), set up our application, and open the main window.
 * There are two ways to run your paradigm: (1) from the console, or (2) from ipython. To run from the console, simple type:
  python testparadigm.py
 * State #0 (named 'ready_next_trial' by default) will be the last state of each trial. When reached, the state machine will yield control to the program running the user interface to prepare the next trial. Once done, the method dispatcher.ready_to_start_trial() will trigger a jump to State #1 to get the trial started (and give control back to the state machine).


.. _download and install TASKontrol: https://github.com/sjara/taskontrol/blob/master/INSTALL.md
.. _plugins/templates.py: https://github.com/sjara/taskontrol/blob/master/plugins/templates.py
