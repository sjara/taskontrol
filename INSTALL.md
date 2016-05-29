___________________________________

 TASKontrol installation and setup
___________________________________


The steps necessary to get started on any operating system are summarized as follows:
- Install python, PySide (which depends on Qt4), numpy and h5py.
- For data plots you will also need matplotlib and pyqtgraph.
- For sounds you will need pyo and serial.
- Download the TASKontrol source code (using git).
- Create the file .../settings/rigsettings.py based on
  rigsettings_template.py and change values according to
  your setup.
- Add the folder containing 'taskontrol' to the Python path.
- Test your system with one of the example paradigms.


===== Installation steps for Ubuntu 12.04 or 14.04 =====

* Before starting, you may need to update the list of packages:
  sudo apt-get update

* Install dependencies:
  sudo apt-get install git ipython python-pyside python-numpy python-matplotlib python-h5py python-pyo python-serial

* Some widgets/plots depend on pyqtgraph (faster than matplotlib).
  Download .deb from  http://luke.campagnola.me/debian/dev/
  Install: sudo dpkg -i python-pyqtgraph_0.9.8-1_all.deb 

* Create and go to the directory where you want the code:
  mkdir ~/src
  cd ~/src/

* Clone source code from repository:
  git clone git://github.com/sjara/taskontrol.git

* Define the settings for this rig:
  cd ~/src/taskontrol/settings/
  cp rigsettings_template.py rigsettings.py
  [edit rigsettings.py to match your settings, e.g. STATE_MACHINE_TYPE]

* Add directory to python path:
  export PYTHONPATH=$PYTHONPATH:~/src
  (this only works for the current terminal, edit ~/.bashrc
   if you want the path change to be permanent)

* If using an arduino as server, you need to have access to the serial port:
  - Add yourself to the dialout group:
    sudo usermod -aG dialout <username>
  - You need to re-login for this to take effect.

* Test the system:
  - Set the appropriate value for STATE_MACHINE_TYPE in
    ~/src/taskontrol/settings/rigsettings.py
  - In a terminal, go to the examples directory:
    cd ~/src/taskontrol/examples/
  - Run a simple example:
    python example003.py
    [you should see a small window with a 'run' button]

* More details and documentation can be found in the 'doc' folder.


===== TROUBLESHOOTING: =====

For each error (E) we describe a probable cause (C) and solution (S):

E: System only shows "Waiting for Arduino to be ready..." and never connects:
C: You have no access to the serial port, or the arduino is not available (unplugged).
S: See above for how to add yourself to the 'dialout' group.

E: 'ImportError: No module named PySide
C: The necessary modules (in this case PySide) have not been installed correctly.
S: Install all the dependencies as explained above.

E: 'ImportError: No module named taskontrol.settings'
C:  Your PYTHON path is not setup correctly.
S:  export PYTHONPATH=$PYTHONPATH:~/src
