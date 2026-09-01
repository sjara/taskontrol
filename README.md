
#  TASKontrol

TASKontrol is an open source framework for developing behavioral experiments for neuroscience research.

It consists of modules written in Python and Qt (via QtPy) for designing behavioral paradigms and providing a graphical user interface to control the experiments. It also includes software that runs in an [Arduino Due](https://www.arduino.cc/en/Main/ArduinoBoardDue) to provide an interface for detecting external events and triggering stimuli.

TASKontrol was developed by Santiago Jaramillo and it is maintained by the [Jaramillo lab](http://jaralab.uoregon.edu) at the University of Oregon. The framework was largely inspired by systems such as [BControl](http://brodywiki.princeton.edu/bcontrol) and the [Linux+RTAI statemachine](https://github.com/cculianu/rt-fsm) originally developed at Cold Spring Harbor Laboratory.

You can find the full documentation at:
  http://taskontrol.readthedocs.org


## INSTALLATION

**NOTE**: For installation on older systems in the Jaramillo lab (using Ubuntu 20.04), see instead [INSTALL.jaralab.md](./INSTALL.jaralab.md) to install the required packages from the Ubuntu repository rather than using pip/conda.

The installation requires that you have working versions of Python and Git.

1. Using Git, clone the stable version of TASKontrol:
  * `git clone https://github.com/sjara/taskontrol.git`
2. Go to the `taskontrol` folder that was just created:
  * `cd taskontrol`
3. Create a virtual environment, either using conda, venv or virtualenvwrapper.
4. Activate the virtual environment.
  * The prompt should now indicate you are inside the environment.
5. Create a taskontrol rig settings file (based on the template):
  * `cp settings/rigsettings_template.py settings/rigsettings.py`
  * Edit the rigsettings.py file if necessary (for example, to set a specific `STATE_MACHINE_TYPE`)
6. Inside that virtual environment, install the package (in development mode):
  * `pip install -e ./`
7. Test the installation:
  * `python examples/example003_dispatcher.py`
  * You should see a window with a big green button and an emulator window.
