Additional timers (extratimers)
===============================

The state machine starts a timer (``statetimer``) when the system enters each state. This timer is used to trigger an event (``Tup``) after a specified period for each state. This is how timed transitions are usually implemented.

Sometimes, it is inconvenient to implement transition logic using only state timers. For example, imagine you need to implement a train of 5 pulses of light. You would need to create an ON state for each pulse, and an OFF state for each pulse:

.. code-block:: python

            # -- Set state matrix --
            self.sm.add_state(name='pulse1_on', statetimer=0.1,
                              transitions={'Tup':'pulse1_off'}, outputsOn=['centerLED'])
            self.sm.add_state(name='pulse1_off', statetimer=0.2,
                              transitions={'Tup':'pulse2_on'}, outputsOff=['centerLED'])
            self.sm.add_state(name='pulse2_on', statetimer=0.1,
                              transitions={'Tup':'pulse2_off'}, outputsOn=['centerLED'])
            self.sm.add_state(name='pulse2_off', statetimer=0.2,
                              transitions={'Tup':'pulse3_on'}, outputsOff=['centerLED'])
            ...
            self.sm.add_state(name='pulse5_on', statetimer=0.1,
                              transitions={'Tup':'pulse5_off'}, outputsOn=['centerLED'])
            self.sm.add_state(name='pulse5_off', statetimer=0.2,
                              transitions={'Tup':'ready_next_trial'}, outputsOff=['centerLED'])


It would be easier if there was a timer that stays active even if the system has transitioned to another state. This is exactly what *extratimers* do.

Here is an example on how you implement the pulse train using extratimers:

.. code-block:: python
    :linenos:

    from taskontrol.plugins import templates
    from taskontrol.core import statematrix
    from taskontrol.settings import rigsettings

    class Paradigm(templates.ParadigmMinimal):
        def __init__(self,parent=None):
            super(Paradigm, self).__init__(parent)
            self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                              outputs=rigsettings.OUTPUTS,
                                              readystate='ready_next_trial',
                                              extratimers=['trainTimer'])
            # The parent class defines self.dispatcherModel used below.

        def prepare_next_trial(self, nextTrial):
            # -- Set extra timers --
            self.sm.set_extratimer('trainTimer', duration=1.5)

            # -- Set state matrix --
            self.sm.add_state(name='start', statetimer=0,
                              transitions={'Tup':'pulse_on'}, trigger=['trainTimer'])
            self.sm.add_state(name='pulse_on', statetimer=0.1,
                              transitions={'Tup':'pulse_off','trainTimer':'end_train'},
                              outputsOn=['centerLED'])
            self.sm.add_state(name='pulse_off', statetimer=0.2,
                              transitions={'Tup':'pulse_on','trainTimer':'end_train'},
                              outputsOff=['centerLED'])
            self.sm.add_state(name='end_train', statetimer=1,
                              transitions={'Tup':'ready_next_trial'},
                              outputsOff=['centerLED'])
            print self.sm
            self.dispatcherModel.set_state_matrix(self.sm)
            # -- Tell the state machine that we are ready to start --
            self.dispatcherModel.ready_to_start_trial()

    if __name__ == "__main__":
        (app,paradigm) = templates.paramgui.create_app(Paradigm)

	
.. note:: In this example, we import a couple of additional modules (``statematrix`` and ``rigsettings``). In previous examples, these were imported by the ``templates`` module, but here we will use them directly.

* **Line 8** creates a StateMatrix object with specific inputs, outputs and one extratimer called ``trainTimer``. Take a look at `rigsettings_template.py`_, to see how inputs and outputs are defined.
* **Line 16** sets the duration of our extratimer.
* **Line 19** defines the first state, which triggers the extratimer (line 20)
* The system will switch back and forth between states ``pulse_on`` and ``pulse_off`` until the ``trainTimer`` ends and makes the system transition to the ``end_train`` state.
    
.. _rigsettings_template.py: https://github.com/sjara/taskontrol/blob/master/settings/rigsettings_template.py



  

  


  
