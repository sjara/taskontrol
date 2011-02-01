 ______________

   TASKontrol
 ______________


TASKontrol is a system for controlling behavioral experiments.

It uses the state machine and sound server running on Linux+RTAI,
originally developed for Cold Spring Harbor Laboratory, available
at http://code.google.com/p/rt-fsm/

TASKontrol consists of a client and a set of modules written in Python
and PyQt4 designed to ease the process of writing behavioral
protocols.

It can serve as an alternative to BControl, and enables controlling
behavioral experiments without the need of Matlab.  Most of TASKontrol
is based on designs and ideas implemented in BControl. More
information about BControl, including nice introductions to the state
machine and the trial structure, can be found at:
http://brodylab.princeton.edu/bcontrol

TASKontrol can run on the same computer as the state machine server,
avoiding the need of an additional "governing" machine (usually
running Windows). In summary, compared to the standard system as of
2009, TASKontrol has the following advantages:
- No need for a Windows license.
- No need for a Matlab license.
- No need for a second computer.
And all this with the power of Python and the beauty of Qt4.

To download the source code, use the following git command:
  git clone git://github.com/sjara/taskontrol.git

To get started read INSTALL.txt in this folder.
--
Santiago Jaramillo <jara@cshl.edu>


