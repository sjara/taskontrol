 ______________

   TASKontrol
 ______________


TASKontrol is a framework for developing behavioral experiments.

It consists of modules written in Python and PySide (Qt for Python)
that help design behavioral paradigms and provide a graphical user
interface to control the experiments.

TASKontrol does not control hardware directly. Instead, it provides a
client to communicate with a finite state machine running on hardware
connected to external signals. The default implementation of the
state machine server runs on the Arduino platform.

The design of TASKontrol was largely inspired by BControl (created and
maintained by the Brody Lab) and the state machine for Linux+RTAI,
originally developed at Cold Spring Harbor Laboratory.

TASKontrol provides the following advantages:
- No need for a Windows license, it runs easily on Linux.
- No need for a Matlab license, it is written in Python.
- No need for multiple computers, when used with the Arduino server.
- An appealing graphical interface, it uses Qt.

You can find the full documentation at:
  http://taskontrol.readthedocs.org

To download the source code, use the following git command:
  git clone git://github.com/sjara/taskontrol.git

To get started read INSTALL.txt in this folder.
--
Santiago Jaramillo <sjara@uoregon.edu>
