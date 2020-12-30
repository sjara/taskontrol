State machine implementation
============================

TASKontrol does not control hardware directly. Instead, it provides a client to communicate with a finite state machine running on hardware connected to external signals. The default implementation of the state machine server runs on the Arduino platform, but the framework also provides an emulator to test paradigms. This page describes how the event-driven state machine is implemented.

Arduino programs usually contain two main functions:

* ``setup()`` which runs once after the board is reset.
* ``loop()`` which runs over and over from then on.

In our system, ``setup()`` shuts off all outputs and establishes the connection between the client (the computer running the graphical interface) and the server (the Arduino board). The rest happens in ``loop()``. You can see the code in `statemachine/statemachine.ino`_.

* The main function inside ``loop()`` is ``execute_cycle()``, which checks if any inputs have changed or any timers have finished. If any of these events have happened, they get added to an events queue.
* At the end of ``execute_cycle()``, we call ``update_state_machine()`` which will go through the queue transitioning through states.



.. _statemachine/statemachine.ino: https://github.com/sjara/taskontrol/blob/master/statemachine/statemachine.ino
