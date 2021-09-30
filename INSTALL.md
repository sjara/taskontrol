# TASKontrol installation and setup

## Installation for Ubuntu 20.04

* Before starting, you may need to update the list of packages:
  * `sudo apt-get update`

* Install dependencies:
  * `sudo apt install python3-numpy ipython3 python3-qtpy python3-h5py python3-serial python3-jack-client python3-pyqtgraph python3-pygame python3-pip`

* If you are installing it on a rig (and need "real-time" sound presentation), you also need:
  * `sudo apt-get install linux-lowlatency jackd`

* Create directory where you want the code to reside and go there:
  * `mkdir ~/src`
  * `cd ~/src/`

* Clone source code from repository:
  * `git clone git://github.com/sjara/taskontrol.git`

* Define the settings for this compupter/rig:
  * `cd ~/src/taskontrol/settings/`
  * `cp rigsettings_template.py rigsettings.py`
  * [edit rigsettings.py to match your settings, e.g. STATE_MACHINE_TYPE]

* Install the packages (in development mode):
  * `cd ~/src/taskontrol/`
  * `pip3 install -e ./`

* If using an arduino as server (e.g., in a rig), you need to have access to the serial port:
  * Add yourself to the dialout group: `sudo usermod -aG dialout <username>`
  * You need to re-login for this to take effect.

### Testing the system:
* Set the appropriate value for STATE_MACHINE_TYPE in `~/src/taskontrol/settings/rigsettings.py`. To test with the emulator, this should be set to `'emulator'`.
* In a terminal, go to the examples directory:
  * `cd ~/src/taskontrol/examples/`
  * From a terminal, run a simple example:
    * `python example003_dispatcher.py`
    * you should see a small window with a 'run' button.

* Full documentation can be found at http://taskontrol.readthedocs.org


## Installation steps for Windows

These instructions assume you have installed the following applications:
1. Python (via the Anaconda Individual Edition): https://www.anaconda.com/products/individual#windows
1. git (64bit): https://git-scm.com/download/win
   * Recommended: during installation, choose Nano as the default editor.

Open the Anaconda Powershell Prompt to follow the steps below:
1. Create a virtual environment:
   * conda create -n taskontrol --clone base
1. Activate the virtual environment:
   * conda activate taskontrol
   * If successful, `(taskontrol)` should appear at the beginning of your prompt.
1. Install dependencies:
   * FINISH THIS SECTION
   * conda install XXXXX
   * conda install -c conda-forge YYYYY
1. Choose or create a folder to install this package and go to that folder:
   * `mkdir ~/src/`
   * `cd ~/src/`
1. Clone the repository:
   * `git clone --single-branch --branch python3 https://github.com/sjara/taskontrol.git`
1. Install the package in editable/development mode:
   * `cd taskontrol`
   * `pip install -e ./`
1. Create a local rigsettings file:
   * FINISH THIS SECTION



## TROUBLESHOOTING:

For each error (E) we describe a probable cause (C) and solution (S):

* E: System only shows "Waiting for Arduino to be ready..." and never connects:
  * C: You have no access to the serial port, or the arduino is not available (unplugged).
  * S: See above for how to add yourself to the 'dialout' group.

* E: 'ImportError: No module named PySide
  * C: The necessary modules (in this case PySide) have not been installed correctly.
  * S: Install all the dependencies as explained above.

* E: 'ImportError: No module named taskontrol.settings'
  * C:  Your PYTHON path is not setup correctly.
  * S:  export PYTHONPATH=$PYTHONPATH:~/src
