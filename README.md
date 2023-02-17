
#  TASKontrol

TASKontrol is an open source framework for developing behavioral experiments for neuroscience research.

It consists of modules written in Python and Qt (via QtPy) for designing behavioral paradigms and providing a graphical user interface to control the experiments. It also includes software that runs in an [Arduino Due](https://www.arduino.cc/en/Main/ArduinoBoardDue) to provide an interface for detecting external events and triggering stimuli.

TASKontrol was developed by Santiago Jaramillo and it is maintained by the [Jaramillo lab](http://jaralab.uoregon.edu) at the University of Oregon. The framework was largely inspired by systems such as [BControl](http://brodywiki.princeton.edu/bcontrol) and the [Linux+RTAI statemachine](https://github.com/cculianu/rt-fsm) originally developed at Cold Spring Harbor Laboratory.

You can find the full documentation at:
  http://taskontrol.readthedocs.org


## INSTALLATION

**NOTE**: If installing the system in the Jaramillo lab, see instead [INSTALL.jaralab.md](./INSTALL.jaralab.md) to install the required packages from the Ubuntu repository rather than using conda/pip.

Outside the Jaramillo lab, you can install the package in a conda virtual environment. The installation requires that you have working versions of Anaconda and Git.

1. Using Git, clone the stable version of TASKontrol:
  * `git clone -b v1.1_stable --single-branch https://github.com/sjara/taskontrol.git`
1. Go to the `taskontrol` folder that was just created:
  * `cd taskontrol`
1. Create a conda environment for taskontrol:
  * `conda env create -f environment.yml`
1. Activate the `taskontrol` environment:
  * `conda activate taskontrol`
  * The prompt should now say `(taskontrol)`, indicating you are in the environment.
1. Create a taskontrol rig settings file (based on the template):
  * `cp rigsettings_template.py rigsettings.py`
  * Edit the rigsettings.py file if necessary (for example, to set a specific `STATE_MACHINE_TYPE`)
1. Inside that virtual environment, install the package (in development mode):
  * `pip install -e ./`
1. Test the installation:
  * `python examples/tutorial001.py`
  * You should see a window with a big green button and an emulator window.


Mac:
1. XCode to get git
1. Anaconda
1. conda env create -f environment.yml
  * qt qtpy h5py numpy pyserial pyqtgraph
  
to avoid conflicts with system-wide Python packages. Below are the instructions to run on a terminal (on Linux or Mac):
